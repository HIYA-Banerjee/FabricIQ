import json
from sqlalchemy.orm import Session
from app.models.models import PredictionHistory
from typing import List, Optional

class PredictionRepository:
    @staticmethod
    def get_latest_for_order(db: Session, order_id: str, tenant_id: str) -> Optional[PredictionHistory]:
        return db.query(PredictionHistory)\
                 .filter(PredictionHistory.order_id == order_id, PredictionHistory.tenant_id == tenant_id)\
                 .order_by(PredictionHistory.created_at.desc())\
                 .first()

    @staticmethod
    def get_all(db: Session, tenant_id: str) -> List[PredictionHistory]:
        return db.query(PredictionHistory).filter(PredictionHistory.tenant_id == tenant_id).all()

    @staticmethod
    def save_prediction(db: Session, tenant_id: str, order_id: str, probability: float, 
                        risk: str, top_features: dict, shap_values: dict, recommendations: list, 
                        model_version: str = "v1.0.0") -> PredictionHistory:
        
        hist = PredictionHistory(
            tenant_id=tenant_id,
            order_id=order_id,
            probability=probability,
            risk=risk,
            top_features=json.dumps(top_features),
            shap_values=json.dumps(shap_values),
            recommendations=json.dumps(recommendations),
            model_version=model_version
        )
        db.add(hist)
        db.commit()
        db.refresh(hist)
        return hist
