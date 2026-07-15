from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.prediction import ScenarioRequest, ScenarioResponse
from app.simulator.scenario_runner import ScenarioRunner
from app.core.config import settings
from typing import Optional

router = APIRouter()

@router.post("/simulate", response_model=ScenarioResponse)
def simulate_scenario(
    request: ScenarioRequest,
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Simulates a production failure / supply delay and returns delta KPIs + corrective recommendations.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    res = ScenarioRunner.run_simulation(db, request, t_id)
    return res
