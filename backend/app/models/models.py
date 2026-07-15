from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, primary_key=True, index=True)
    customer = Column(String, nullable=False)
    material_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    start_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String, default="Pending")  # Pending, In Progress, Completed, Delayed
    progress = Column(Float, default=0.0)      # 0.0 to 1.0
    priority = Column(String, default="Medium")  # Low, Medium, High
    revenue = Column(Float, default=0.0)

    # Relationships
    production_logs = relationship("ProductionLog", back_populates="order", cascade="all, delete-orphan")

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)        # Spinning, Weaving, Dyeing, QC
    status = Column(String, default="Idle")       # Idle, Running, Maintenance, Error
    efficiency = Column(Float, default=0.85)      # 0.0 to 1.0
    utilization = Column(Float, default=0.0)      # 0.0 to 1.0
    failure_probability = Column(Float, default=0.0) # 0.0 to 1.0
    total_runtime_hours = Column(Float, default=0.0)
    maintenance_history_count = Column(Integer, default=0)

    production_logs = relationship("ProductionLog", back_populates="machine")

class Worker(Base):
    __tablename__ = "workers"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    shift = Column(String, nullable=False)        # Day, Evening, Night
    productivity = Column(Float, default=0.85)     # 0.0 to 1.0
    attendance = Column(Boolean, default=True)

    production_logs = relationship("ProductionLog", back_populates="worker")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    material = Column(String, nullable=False)
    reliability_score = Column(Float, default=100.0) # 0.0 to 100.0
    delay_rate = Column(Float, default=0.0)          # 0.0 to 1.0
    lead_time_days = Column(Float, default=5.0)

class ProductionLog(Base):
    __tablename__ = "production_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(String, index=True, nullable=False)
    order_id = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    quantity_produced = Column(Float, nullable=False)
    machine_id = Column(String)
    worker_id = Column(String)

    # Note: ForeignKey attributes can be set but for multi-tenancy flexibility we handle joining manually or keep it simple
    order_id_fk = Column(String, ForeignKey("orders.id"))
    machine_id_fk = Column(String, ForeignKey("machines.id"))
    worker_id_fk = Column(String, ForeignKey("workers.id"))

    order = relationship("Order", back_populates="production_logs")
    machine = relationship("Machine", back_populates="production_logs")
    worker = relationship("Worker", back_populates="production_logs")

class PredictionHistory(Base):
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(String, index=True, nullable=False)
    order_id = Column(String, nullable=False)
    probability = Column(Float, nullable=False)
    risk = Column(String, nullable=False)         # Low, Medium, High
    top_features = Column(Text)                   # JSON string of features
    shap_values = Column(Text)                    # JSON string of SHAP values
    recommendations = Column(Text)                # JSON string of recommendations list
    created_at = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String, default="v1.0.0")
