from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.prediction_service import PredictionService
from app.repositories.prediction_repo import PredictionRepository
from app.core.config import settings
from typing import Optional, List
import json

router = APIRouter()

@router.post("/batch")
def trigger_batch_predictions(
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Triggers prediction and SHAP calculation runs for all active orders, 
    and updates machine failure probabilities.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    results = PredictionService.run_batch_predictions(db, t_id)
    return {"success": True, "count": len(results), "predictions": results}

@router.get("/order/{order_id}")
def get_order_delay_prediction(
    order_id: str,
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Retrieves the prediction risk, recommendations, and SHAP drivers for a specific order.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    pred = PredictionService.get_order_prediction(db, order_id, t_id)
    if not pred:
        raise HTTPException(status_code=404, detail="Order not found or has no active prediction logs.")
    return pred

@router.get("/history")
def get_prediction_history(
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Returns historical predictions log list for analysis.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    hist = PredictionRepository.get_all(db, t_id)
    return [
        {
            "id": h.id,
            "order_id": h.order_id,
            "probability": h.probability,
            "risk": h.risk,
            "created_at": h.created_at,
            "top_features": json.loads(h.top_features) if h.top_features else {},
            "shap_values": json.loads(h.shap_values) if h.shap_values else {},
            "recommendations": json.loads(h.recommendations) if h.recommendations else []
        }
        for h in hist
    ]
