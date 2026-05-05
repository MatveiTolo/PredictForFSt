from fastapi import FastAPI

app = FastAPI(
    title="PredictForFSt API",
    description="Сервис предсказания курсов валют и ресурсов",
    version="0.1.0",
)


@app.get("/health")
async def health_check():
    """Health-check эндпоинт для проверки работоспособности сервера."""
    return {"status": "ok", "service": "PredictForFSt API"}