from app.optimizer.scheduler import ORToolsScheduler
from app.models.models import Order, Machine, Supplier
from app.schemas.prediction import ScenarioRequest, ScenarioResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import copy

class ScenarioRunner:
    @staticmethod
    def run_simulation(db: Session, request: ScenarioRequest, tenant_id: str) -> ScenarioResponse:
        """
        Executes a hypothetical production floor scenario, compares results against
        the baseline schedule, and estimates revenue-at-risk and suggested mitigations.
        """
        # 1. Fetch baseline active orders and machines
        orders = db.query(Order).filter(Order.tenant_id == tenant_id, Order.status != "Completed").all()
        machines = db.query(Machine).filter(Machine.tenant_id == tenant_id).all()
        suppliers = db.query(Supplier).filter(Supplier.tenant_id == tenant_id).all()
        
        # 2. Run baseline optimization
        baseline_res = ORToolsScheduler.optimize_production_schedule(orders, machines, tenant_id)
        
        # 3. Clone and apply scenario changes
        sim_orders = [copy.copy(o) for o in orders]
        sim_machines = [copy.copy(m) for m in machines]
        
        scenario_descriptions = []
        
        # Scenario: Machine outage
        if request.machine_id_outage:
            outage_m = next((m for m in sim_machines if m.id == request.machine_id_outage), None)
            if outage_m:
                # Remove or lower efficiency to near zero
                outage_m.efficiency = 0.001
                outage_m.status = "Error"
                scenario_descriptions.append(f"Machine Outage on '{outage_m.name}'")
                
        # Scenario: Supplier Delay
        if request.supplier_id_delay and request.supplier_delay_days > 0:
            supplier = db.query(Supplier).filter(Supplier.id == request.supplier_id_delay).first()
            if supplier:
                scenario_descriptions.append(f"Supplier '{supplier.name}' delayed by {request.supplier_delay_days} days")
                # Delay the start date of orders that require the supplier's material type
                for order in sim_orders:
                    if order.material_type == supplier.material:
                        order.start_date = order.start_date + timedelta(days=request.supplier_delay_days)

        # Scenario: Rush Order Injected
        if request.rush_order_qty > 0 and request.rush_order_material:
            rush_id = f"ORD-{tenant_id}-RUSH"
            rush_order = Order(
                id=rush_id,
                tenant_id=tenant_id,
                customer="RUSH_INJECTION_MOCK",
                material_type=request.rush_order_material,
                quantity=request.rush_order_qty,
                start_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=5),
                status="Pending",
                progress=0.0,
                priority="High",
                revenue=round(request.rush_order_qty * 15.0, 2)
            )
            sim_orders.append(rush_order)
            scenario_descriptions.append(f"Rush Order Injected ({request.rush_order_qty} units of {request.rush_order_material})")
            
        if not scenario_descriptions:
            scenario_descriptions.append("No changes applied (Baseline execution)")

        # 4. Run simulated optimization
        sim_res = ORToolsScheduler.optimize_production_schedule(sim_orders, sim_machines, tenant_id)
        
        # 5. Calculate delta analysis
        # Revenue-at-risk = sum of revenue for orders that are delayed in simulated run
        revenue_at_risk = 0.0
        impacted_order_ids = []
        
        # Check which simulated jobs ended past their due hours
        sim_jobs = sim_res["scheduled_jobs"]
        for order in sim_orders:
            order_jobs = [job for job in sim_jobs if job["order_id"] == order.id]
            if order_jobs:
                final_completion_hour = max(job["end_hour"] for job in order_jobs)
                due_hours = int((order.due_date - order.start_date).total_seconds() / 3600.0)
                if final_completion_hour > due_hours:
                    impacted_order_ids.append(order.id)
                    revenue_at_risk += order.revenue
                    
        # 6. Formulate corrective actions based on the scenario
        mitigations = []
        if request.machine_id_outage:
            mitigations.append(f"Redirect task queues from '{request.machine_id_outage}' to alternative machines.")
            mitigations.append("Schedule emergency repair shift to reduce downtime.")
        if request.supplier_id_delay:
            mitigations.append("Source alternative material stock from buffer inventory.")
            mitigations.append("Reallocate workers to other active departments to balance labor overhead.")
        if request.rush_order_qty > 0:
            mitigations.append("Increase overtime hours for the Evening/Night shifts.")
            mitigations.append("De-prioritize low-value orders to free up loom capacity.")

        if not mitigations:
            mitigations.append("No immediate mitigations required. Continue monitoring.")
            
        return ScenarioResponse(
            scenario_description=" + ".join(scenario_descriptions),
            original_delayed_orders=baseline_res["delayed_orders_count"],
            simulated_delayed_orders=sim_res["delayed_orders_count"],
            original_makespan_hours=float(baseline_res["makespan_hours"]),
            simulated_makespan_hours=float(sim_res["makespan_hours"]),
            revenue_at_risk=round(revenue_at_risk, 2),
            mitigation_actions=mitigations,
            impacted_order_ids=impacted_order_ids
        )
