from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
from models import (
    ForecastRequest, PredictionRecord, UserRegister,
    UserLogin, TokenResponse, RefreshRequest, UserRole,
)
from auth import (
    get_current_user, require_role, get_auth_service,
    get_user_repo, user_repo,
)
from repository import PredictionRepository
from services import AuthService, PredictionService

# Импорт ML-функции
from ml.forecast import forecast_ticker

# Синглтоны
prediction_repo = PredictionRepository()
prediction_service = PredictionService(prediction_repo)

app = FastAPI(
    title="PredictForFSt API",
    description="Сервис предсказания курсов валют и ресурсов",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Эндпоинты ----

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "PredictForFSt API"}


@app.get("/api/symbols")
def get_symbols():
    symbols = [
        {"value": "USDRUB=X", "label": "USD/RUB (Доллар/Рубль)"},
        {"value": "GC=F", "label": "Gold Futures (GC=F)"},
        {"value": "BZ=F", "label": "Brent Crude Oil (BZ=F)"},
    ]
    return {"symbols": symbols}


@app.post("/api/forecast")
def post_forecast(req: ForecastRequest):
    try:
        result = forecast_ticker(ticker=req.ticker, horizon_days=req.horizon)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---- Аутентификация с refresh токенами ----

@app.post("/auth/register", status_code=201)
def register(user: UserRegister, auth_svc: AuthService = Depends(get_auth_service)):
    if user_repo.get_by_username(user.username):
        raise HTTPException(status_code=409, detail="Пользователь уже существует")

    user_repo.create(
        username=user.username,
        email=user.email,
        hashed_password=auth_svc.hash_password(user.password),
        role=UserRole.USER,
    )
    return {"message": "Пользователь создан", "username": user.username}


@app.post("/auth/login", response_model=TokenResponse)
def login(user: UserLogin, auth_svc: AuthService = Depends(get_auth_service)):
    db_user = user_repo.get_by_username(user.username)
    if not db_user or not auth_svc.verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    role = db_user["role"].value if isinstance(db_user["role"], UserRole) else db_user["role"]
    access_token = auth_svc.create_access_token(user.username, role)
    refresh_token = auth_svc.create_refresh_token(user.username)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, auth_svc: AuthService = Depends(get_auth_service)):
    """Обновить access token по refresh token."""
    try:
        new_access = auth_svc.refresh_access_token(req.refresh_token)
        # При ротации возвращаем тот же refresh (он уже заменён в refresh_access_token)
        return TokenResponse(access_token=new_access, refresh_token=req.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/auth/logout")
def logout(
    refresh_token: str,
    current_user: dict = Depends(get_current_user),
    auth_svc: AuthService = Depends(get_auth_service),
):
    """Выход — отозвать refresh token."""
    auth_svc.revoke_refresh_token(current_user["username"], refresh_token)
    return {"message": "Выход выполнен"}


@app.get("/auth/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"].value if isinstance(current_user["role"], UserRole) else current_user["role"],
    }


# ---- Администрирование ----

@app.get("/admin/users")
def get_all_users(current_user: dict = Depends(require_role(UserRole.ADMIN))):
    return [
        {"username": u["username"], "email": u["email"],
         "role": u["role"].value if isinstance(u["role"], UserRole) else u["role"]}
        for u in user_repo.get_all()
    ]


@app.put("/admin/users/{username}/role")
def set_user_role(
    username: str,
    role: UserRole,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
):
    if not user_repo.update_role(username, role):
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"message": f"Роль пользователя {username} изменена на {role.value}"}


# ---- CRUD прогнозов ----

@app.post("/predictions", status_code=201)
def create_prediction(
    req: ForecastRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        result = forecast_ticker(ticker=req.ticker, horizon_days=req.horizon)
        last_price = result["forecast"]["prices"][-1]
        last_date = result["forecast"]["dates"][-1]

        record = prediction_service.create(
            username=current_user["username"],
            ticker=req.ticker,
            date=last_date,
            price=last_price,
        )
        return record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predictions", response_model=list[PredictionRecord])
def get_predictions(current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == UserRole.ADMIN
    return prediction_service.get_for_user(current_user["username"], is_admin)


@app.get("/predictions/{prediction_id}", response_model=PredictionRecord)
def get_prediction(prediction_id: int, current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == UserRole.ADMIN
    try:
        return prediction_service.get_by_id(prediction_id, current_user["username"], is_admin)
    except ValueError:
        raise HTTPException(status_code=404, detail="Прогноз не найден")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Доступ запрещён")


@app.delete("/predictions/{prediction_id}")
def delete_prediction(prediction_id: int, current_user: dict = Depends(get_current_user)):
    is_admin = current_user.get("role") == UserRole.ADMIN
    try:
        prediction_service.delete(prediction_id, current_user["username"], is_admin)
        return {"message": f"Прогноз {prediction_id} удалён"}
    except ValueError:
        raise HTTPException(status_code=404, detail="Прогноз не найден")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Доступ запрещён")