from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, field_validator
from datetime import datetime
from auth import (
    fake_users_db,
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_role,
)
from models import UserRole

# Импорт ML-функции
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


# ---- Приложение ----

app = FastAPI(
    title="PredictForFSt API",
    description="Сервис предсказания курсов валют и ресурсов",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Временное хранилище прогнозов
predictions_db: list[dict] = []
next_id: int = 1


# ---- Автоматическое создание admin при запуске ----

if "admin" not in fake_users_db:
    fake_users_db["admin"] = {
        "username": "admin",
        "email": "admin@admin.com",
        "hashed_password": get_password_hash("admin123"),
        "role": UserRole.ADMIN,
    }
    print("*** Admin пользователь создан (admin / admin123) ***")


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
    """Получить прогноз от ML-модели (без авторизации)."""
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
        "role": UserRole.USER,
    }
    return {"message": "Пользователь создан", "username": user.username}


@app.post("/auth/login")
def login(user: UserLogin):
    """Вход в систему — получение JWT токена."""
    db_user = fake_users_db.get(user.username)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_access_token(data={
        "sub": user.username,
        "role": db_user.get("role", UserRole.USER).value,
    })
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Информация о текущем пользователе."""
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user.get("role", UserRole.USER).value,
    }


# ---- Администрирование (только для admin) ----

@app.get("/admin/users")
def get_all_users(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    """Получить список всех пользователей (только admin)."""
    return [
        {
            "username": u["username"],
            "email": u["email"],
            "role": u.get("role", UserRole.USER).value,
        }
        for u in fake_users_db.values()
    ]


@app.put("/admin/users/{username}/role")
def set_user_role(
    username: str,
    role: UserRole,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
):
    """Изменить роль пользователя (только admin)."""
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    fake_users_db[username]["role"] = role
    return {"message": f"Роль пользователя {username} изменена на {role.value}"}


# ---- CRUD для сохранения прогнозов (защищённые) ----

@app.post("/predictions", status_code=201)
def create_prediction(
    req: ForecastRequest,
    current_user: dict = Depends(get_current_user),
):
    """Сохранить прогноз в избранное (только для авторизованных)."""
    global next_id
    try:
        result = forecast_ticker(ticker=req.ticker, horizon_days=req.horizon)
        last_price = result["forecast"]["prices"][-1]
        last_date = result["forecast"]["dates"][-1]

        record = {
            "id": next_id,
            "username": current_user["username"],
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
def get_predictions(current_user: dict = Depends(get_current_user)):
    """Получить прогнозы текущего пользователя (admin видит все)."""
    if current_user.get("role") == UserRole.ADMIN:
        return predictions_db
    return [p for p in predictions_db if p["username"] == current_user["username"]]


@app.get("/predictions/{prediction_id}", response_model=PredictionRecord)
def get_prediction(
    prediction_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Получить прогноз по ID (свой или admin)."""
    for record in predictions_db:
        if record["id"] == prediction_id:
            if record["username"] != current_user["username"] and current_user.get("role") != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Доступ запрещён")
            return record
    raise HTTPException(status_code=404, detail="Прогноз не найден")


@app.delete("/predictions/{prediction_id}")
def delete_prediction(
    prediction_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Удалить прогноз по ID (свой или admin)."""
    for i, record in enumerate(predictions_db):
        if record["id"] == prediction_id:
            if record["username"] != current_user["username"] and current_user.get("role") != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Доступ запрещён")
            del predictions_db[i]
            return {"message": f"Прогноз {prediction_id} удалён"}
    raise HTTPException(status_code=404, detail="Прогноз не найден")