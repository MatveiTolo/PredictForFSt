from pydantic import BaseModel, field_validator
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    GUEST = "guest"
    USER = "user"
    ADMIN = "admin"


class Prediction(BaseModel):
    id: int
    ticker: str
    date: str
    predicted_price: float
    created_at: datetime


class PredictionCreate(BaseModel):
    ticker: str
    date: str
    predicted_price: float

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str):
        v = (v or "").strip()
        if not v:
            raise ValueError("ticker must not be empty")
        return v

    @field_validator("predicted_price")
    @classmethod
    def validate_price(cls, v: float):
        if v <= 0:
            raise ValueError("predicted_price must be greater than 0")
        return v


class PredictionUpdate(BaseModel):
    ticker: str | None = None
    date: str | None = None
    predicted_price: float | None = None