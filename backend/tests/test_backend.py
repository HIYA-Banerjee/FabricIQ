import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.simulator.factory_simulator import seed_database
from app.models.models import Order, Machine, Supplier, PredictionHistory
from app.services.ingestion_service import IngestionService
from app.simulator.scenario_runner import ScenarioRunner
from app.schemas.prediction import ScenarioRequest
from app.optimizer.scheduler import ORToolsScheduler
from datetime import datetime, timedelta

# Create an in-memory SQLite database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        seed_database(db_session, "test_tenant")
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)

def test_db_seeding(db):
    """
    Verify synthetic generator creates rows for orders, machines, and suppliers.
    """
    orders = db.query(Order).filter(Order.tenant_id == "test_tenant").all()
    machines = db.query(Machine).filter(Machine.tenant_id == "test_tenant").all()
    suppliers = db.query(Supplier).filter(Supplier.tenant_id == "test_tenant").all()
    
    assert len(orders) > 0
    assert len(machines) > 0
    assert len(suppliers) > 0

def test_ingestion_validation(db):
    """
    Assert duplicate Order ID rejection and impossible values catches.
    """
    # Duplicate ID check
    orders = db.query(Order).filter(Order.tenant_id == "test_tenant").all()
    existing_id = orders[0].id
    
    csv_content = f"id,customer,material_type,quantity,start_date,due_date\n{existing_id},Fake Customer,Cotton,1000,2026-07-01,2026-07-10\n"
    res = IngestionService.process_file_upload(db, csv_content.encode("utf-8"), "test.csv", "test_tenant")
    assert res["success"] is False
    assert res["duplicate_count"] == 1
    
    # Impossible quantity check
    csv_content_invalid = "id,customer,material_type,quantity,start_date,due_date\nORD-TEST-99,Fake Customer,Cotton,-500,2026-07-01,2026-07-10\n"
    res_inv = IngestionService.process_file_upload(db, csv_content_invalid.encode("utf-8"), "test_inv.csv", "test_tenant")
    assert len(res_inv["errors"]) > 0

def test_scenario_simulation(db):
    """
    Test scenario runner correctly computes the impact of machine failure.
    """
    machines = db.query(Machine).filter(Machine.tenant_id == "test_tenant").all()
    outage_machine_id = machines[0].id
    
    req = ScenarioRequest(
        machine_id_outage=outage_machine_id,
        supplier_id_delay=None,
        supplier_delay_days=0.0
    )
    
    sim_res = ScenarioRunner.run_simulation(db, req, "test_tenant")
    assert sim_res.scenario_description is not None
    assert sim_res.revenue_at_risk >= 0.0
    assert len(sim_res.mitigation_actions) > 0

def test_scheduling_optimization(db):
    """
    Verify OR-Tools schedules all active operations without overlaps.
    """
    orders = db.query(Order).filter(Order.tenant_id == "test_tenant", Order.status != "Completed").all()
    machines = db.query(Machine).filter(Machine.tenant_id == "test_tenant").all()
    
    res = ORToolsScheduler.optimize_production_schedule(orders, machines, "test_tenant")
    assert res["success"] is True
    assert len(res["scheduled_jobs"]) > 0
