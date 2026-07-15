from fastapi import APIRouter
from app.api.v1.endpoints import (
    analytics, ingestion, ocr, predictions, optimization, simulator, assistant
)

api_router = APIRouter()

api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Data Ingestion"])
api_router.include_router(ocr.router, prefix="/ocr", tags=["OCR scanning"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["ML Predictions"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["OR-Tools Scheduler"])
api_router.include_router(simulator.router, prefix="/simulator", tags=["Scenario Simulator"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Agentic AI Assistant"])
