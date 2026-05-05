from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from datetime import datetime

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