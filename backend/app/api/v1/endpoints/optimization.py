from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.optimization_service import OptimizationService
from app.core.config import settings
from typing import Optional

router = APIRouter()

@router.get("/schedule")
def run_scheduler_optimization(
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Reruns scheduling optimization and returns the machine timeline allocation.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    res = OptimizationService.get_optimized_schedule(db, t_id)
    return res
