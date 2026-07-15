from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any

class PredictionResponse(BaseModel):
    order_id: str
    probability: float
    risk: str
    top_features: Dict[str, float]
    shap_values: Dict[str, float]
    recommendations: List[str]
    created_at: datetime
    model_version: str

    model_config = ConfigDict(from_attributes=True)

class ScenarioRequest(BaseModel):
    machine_id_outage: Optional[str] = None
    supplier_id_delay: Optional[str] = None
    supplier_delay_days: Optional[float] = 0.0
    rush_order_qty: Optional[float] = 0.0
    rush_order_material: Optional[str] = None

class ScenarioResponse(BaseModel):
    scenario_description: str
    original_delayed_orders: int
    simulated_delayed_orders: int
    original_makespan_hours: float
    simulated_makespan_hours: float
    revenue_at_risk: float
    mitigation_actions: List[str]
    impacted_order_ids: List[str]
