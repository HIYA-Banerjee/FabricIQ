import pandas as pd
from sqlalchemy.orm import Session  # pyrefly: ignore [missing-import]
from app.models.models import Order, Machine, Worker, Supplier, ProductionLog
from app.ml.feature_engineering import engineer_order_features
from datetime import datetime

def load_ml_dataset(db: Session, tenant_id: str = None) -> pd.DataFrame:
    """
    Extracts tables from the DB, runs feature engineering, and appends a target binary classification label:
    - target: 1 if order status is 'Delayed', or if past its due date and not completed; 0 otherwise.
    """
    # 1. Fetch data
    order_query = db.query(Order)
    machine_query = db.query(Machine)
    worker_query = db.query(Worker)
    supplier_query = db.query(Supplier)
    log_query = db.query(ProductionLog)

    if tenant_id:
        order_query = order_query.filter(Order.tenant_id == tenant_id)
        machine_query = machine_query.filter(Machine.tenant_id == tenant_id)
        worker_query = worker_query.filter(Worker.tenant_id == tenant_id)
        supplier_query = supplier_query.filter(Supplier.tenant_id == tenant_id)
        log_query = log_query.filter(ProductionLog.tenant_id == tenant_id)

    orders = order_query.all()
    machines = machine_query.all()
    workers = worker_query.all()
    suppliers = supplier_query.all()
    logs = log_query.all()

    if not orders:
        return pd.DataFrame()

    # 2. Convert to DataFrames
    orders_df = pd.DataFrame([{
        "id": o.id, "customer": o.customer, "material_type": o.material_type,
        "quantity": o.quantity, "start_date": o.start_date, "due_date": o.due_date,
        "status": o.status, "progress": o.progress, "priority": o.priority, "revenue": o.revenue
    } for o in orders])

    machines_df = pd.DataFrame([{
        "id": m.id, "status": m.status, "efficiency": m.efficiency, "utilization": m.utilization,
        "failure_probability": m.failure_probability, "total_runtime_hours": m.total_runtime_hours,
        "maintenance_history_count": m.maintenance_history_count
    } for m in machines]) if machines else pd.DataFrame()

    workers_df = pd.DataFrame([{
        "id": w.id, "shift": w.shift, "productivity": w.productivity, "attendance": w.attendance
    } for w in workers]) if workers else pd.DataFrame()

    suppliers_df = pd.DataFrame([{
        "id": s.id, "material": s.material, "reliability_score": s.reliability_score,
        "delay_rate": s.delay_rate, "lead_time_days": s.lead_time_days
    } for s in suppliers]) if suppliers else pd.DataFrame()

    logs_df = pd.DataFrame([{
        "order_id": l.order_id, "date": l.date, "quantity_produced": l.quantity_produced,
        "machine_id": l.machine_id, "worker_id": l.worker_id
    } for l in logs]) if logs else pd.DataFrame()

    # 3. Engineer features
    ref_date = datetime.utcnow()
    features_df = engineer_order_features(orders_df, logs_df, machines_df, workers_df, suppliers_df, ref_date)

    # 4. Define training label
    # Delayed = 1 if status is 'Delayed', or if overdue and progress < 1.0
    def label_target(row):
        if row["status"] == "Delayed":
            return 1
        due_dt = pd.to_datetime(row["due_date"])
        if due_dt < ref_date and row["progress"] < 1.0:
            return 1
        return 0

    features_df["target"] = features_df.apply(label_target, axis=1)

    return features_df
