from sqlalchemy.orm import Session
from app.optimizer.scheduler import ORToolsScheduler
from app.repositories.order_repo import OrderRepository
from app.repositories.machine_repo import MachineRepository
from app.models.models import Order
from loguru import logger

class OptimizationService:
    @staticmethod
    def get_optimized_schedule(db: Session, tenant_id: str) -> dict:
        """
        Loads active database objects and runs the OR-Tools scheduling solver.
        """
        logger.info(f"Generating optimized production schedule for tenant {tenant_id}...")
        
        orders = db.query(Order).filter(Order.tenant_id == tenant_id, Order.status != "Completed").all()
        machines = MachineRepository.get_all(db, tenant_id)
        
        if not orders:
            return {"success": False, "message": "No active orders found for scheduling."}
        if not machines:
            return {"success": False, "message": "No machines found in directory."}
            
        result = ORToolsScheduler.optimize_production_schedule(orders, machines, tenant_id)
        return result
