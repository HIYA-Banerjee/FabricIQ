from pydantic import BaseModel, ConfigDict
from typing import Optional

class MachineBase(BaseModel):
    id: str
    name: str
    type: str
    status: str = "Idle"
    efficiency: float = 0.85
    utilization: float = 0.0
    failure_probability: float = 0.0
    total_runtime_hours: float = 0.0
    maintenance_history_count: int = 0

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    efficiency: Optional[float] = None
    utilization: Optional[float] = None
    failure_probability: Optional[float] = None
    total_runtime_hours: Optional[float] = None
    maintenance_history_count: Optional[int] = None

class MachineResponse(MachineBase):
    tenant_id: str

    model_config = ConfigDict(from_attributes=True)
