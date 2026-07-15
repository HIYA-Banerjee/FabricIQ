from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Order, Machine, Worker, Supplier, PredictionHistory
from app.core.config import settings
from typing import Optional

router = APIRouter()

@router.get("/")
def get_dashboard_analytics(
    tenant_id: Optional[str] = Header(None, alias=settings.TENANT_HEADER),
    db: Session = Depends(get_db)
):
    """
    Returns executive-level summary KPIs and trends for the specific factory tenant.
    """
    t_id = tenant_id or settings.DEFAULT_TENANT_ID
    
    orders = db.query(Order).filter(Order.tenant_id == t_id).all()
    machines = db.query(Machine).filter(Machine.tenant_id == t_id).all()
    workers = db.query(Worker).filter(Worker.tenant_id == t_id).all()
    suppliers = db.query(Supplier).filter(Supplier.tenant_id == t_id).all()
    
    total_orders = len(orders)
    orders_in_progress = len([o for o in orders if o.status == "In Progress"])
    orders_completed = len([o for o in orders if o.status == "Completed"])
    
    # Calculate high-risk orders based on cached predictions
    predictions = db.query(PredictionHistory).filter(PredictionHistory.tenant_id == t_id).all()
    # Get latest prediction per order
    latest_preds = {}
    for p in predictions:
        if p.order_id not in latest_preds or p.created_at > latest_preds[p.order_id].created_at:
            latest_preds[p.order_id] = p
            
    high_risk_count = len([p for p in latest_preds.values() if p.risk == "High"])
    
    # Machine indicators
    running_machines = len([m for m in machines if m.status == "Running"])
    idle_machines = len([m for m in machines if m.status == "Idle"])
    maint_machines = len([m for m in machines if m.status in ("Maintenance", "Error")])
    
    avg_mach_util = sum([m.utilization for m in machines]) / max(1, len(machines))
    avg_wrk_prod = sum([w.productivity for w in workers]) / max(1, len(workers))
    
    # Material stocks and supplier ratings
    material_distribution = {}
    for o in orders:
        material_distribution[o.material_type] = material_distribution.get(o.material_type, 0) + o.quantity
        
    supplier_perf = [{"name": s.name, "rating": s.reliability_score, "material": s.material} for s in suppliers]

    return {
        "tenant_id": t_id,
        "kpis": {
            "total_orders": total_orders,
            "orders_in_progress": orders_in_progress,
            "orders_completed": orders_completed,
            "high_risk_orders": high_risk_count,
            "on_time_rate": round((orders_completed / max(1, orders_completed + high_risk_count)) * 100.0, 1),
            "avg_machine_utilization": round(avg_mach_util * 100.0, 1),
            "avg_worker_productivity": round(avg_wrk_prod * 100.0, 1),
        },
        "machines": {
            "running": running_machines,
            "idle": idle_machines,
            "maintenance": maint_machines,
            "total": len(machines),
            "list": [{"id": m.id, "name": m.name, "type": m.type, "status": m.status, "failure_prob": m.failure_probability} for m in machines]
        },
        "materials": material_distribution,
        "suppliers": supplier_perf
    }
