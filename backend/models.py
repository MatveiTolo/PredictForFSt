from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class UserInDB(BaseModel):
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.USER


class TokenData(BaseModel):
    sub: str
    role: str


class PredictionRecord(BaseModel):
    id: int
    ticker: str
    date: str
    predicted_price: float
    created_at: str
    username: str


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
            raise ValueError("Минимум 3 символа")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str):
        if len(v) < 4:
            raise ValueError("Минимум 4 символа")
        return v


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str