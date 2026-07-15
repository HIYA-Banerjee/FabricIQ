from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List

class OrderBase(BaseModel):
    id: str
    customer: str
    material_type: str
    quantity: float
    start_date: datetime
    due_date: datetime
    status: str = "Pending"
    progress: float = 0.0
    priority: str = "Medium"
    revenue: float = 0.0

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    customer: Optional[str] = None
    material_type: Optional[str] = None
    quantity: Optional[float] = None
    start_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    progress: Optional[float] = None
    priority: Optional[str] = None
    revenue: Optional[float] = None

class OrderResponse(OrderBase):
    tenant_id: str
    
    model_config = ConfigDict(from_attributes=True)
