from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator
from datetime import datetime
from auth import (
    fake_users_db,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
)
from pydantic import BaseModel, field_validator, EmailStr

# Импорт твоей ML-функции
from ml.forecast import forecast_ticker


# ---- Pydantic-модели ----

class ForecastRequest(BaseModel):
    ticker: str
    horizon: int

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("ticker must not be empty")
        return v

    @field_validator("horizon")
    @classmethod
    def validate_horizon(cls, v: int):
        if not (3 <= v <= 30):
            raise ValueError("horizon must be between 3 and 30")
        return v


class PredictionRecord(BaseModel):
    id: int
    ticker: str
    date: str
    predicted_price: float
    created_at: str


# ---- Приложение ----

class UserRegister(BaseModel):
    email: str
    username: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str):
        v = (v or "").strip()
        if not v or "@" not in v:
            raise ValueError("Некорректный email")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str):
        v = (v or "").strip()
        if len(v) < 3:
            raise ValueError("Имя пользователя должно быть не менее 3 символов")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 4:
            raise ValueError("Пароль должен быть не менее 4 символов")
        return v


class UserLogin(BaseModel):
    username: str
    password: str

app = FastAPI(
    title="PredictForFSt API",
    description="Сервис предсказания курсов валют и ресурсов",
    version="0.1.0",
)

# Временное хранилище прогнозов
predictions_db: list[dict] = []
next_id: int = 1


# ---- Эндпоинты ----

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "PredictForFSt API"}


@app.get("/api/symbols")
def get_symbols():
    """Список доступных тикеров."""
    symbols = [
        {"value": "USDRUB=X", "label": "USD/RUB (Доллар/Рубль)"},
        {"value": "GC=F", "label": "Gold Futures (GC=F)"},
        {"value": "BZ=F", "label": "Brent Crude Oil (BZ=F)"},
    ]
    return {"symbols": symbols}


@app.post("/api/forecast")
def post_forecast(req: ForecastRequest):
    """Получить прогноз от ML-модели."""
    try:
        result = forecast_ticker(ticker=req.ticker, horizon_days=req.horizon)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

# ---- Авторизация ----

@app.post("/auth/register", status_code=201)
def register(user: UserRegister):
    """Регистрация нового пользователя."""
    if user.username in fake_users_db:
        raise HTTPException(status_code=409, detail="Пользователь уже существует")
    
    fake_users_db[user.username] = {
        "username": user.username,
        "email": user.email,
        "hashed_password": get_password_hash(user.password),
    }
    return {"message": "Пользователь создан", "username": user.username}


@app.post("/auth/login")
def login(user: UserLogin):
    """Вход в систему — получение JWT токена."""
    db_user = fake_users_db.get(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Информация о текущем пользователе."""
    return {"username": current_user["username"], "email": current_user["email"]}


# ---- CRUD для сохранения прогнозов ----

@app.post("/predictions", status_code=201)
def create_prediction(req: ForecastRequest):
    """Сохранить прогноз в избранное."""
    global next_id
    try:
        result = forecast_ticker(ticker=req.ticker, horizon_days=req.horizon)
        # Сохраняем только последнюю предсказанную цену
        last_price = result["forecast"]["prices"][-1]
        last_date = result["forecast"]["dates"][-1]

        record = {
            "id": next_id,
            "ticker": req.ticker,
            "date": last_date,
            "predicted_price": last_price,
            "created_at": datetime.utcnow().isoformat(),
        }
        predictions_db.append(record)
        next_id += 1
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predictions", response_model=list[PredictionRecord])
def get_predictions():
    """Получить все сохранённые прогнозы."""
    return predictions_db


@app.get("/predictions/{prediction_id}", response_model=PredictionRecord)
def get_prediction(prediction_id: int):
    """Получить прогноз по ID."""
    for record in predictions_db:
        if record["id"] == prediction_id:
            return record
    raise HTTPException(status_code=404, detail="Прогноз не найден")


@app.delete("/predictions/{prediction_id}")
def delete_prediction(prediction_id: int):
    """Удалить прогноз по ID."""
    for i, record in enumerate(predictions_db):
        if record["id"] == prediction_id:
            del predictions_db[i]
            return {"message": f"Прогноз {prediction_id} удалён"}
    raise HTTPException(status_code=404, detail="Прогноз не найден")