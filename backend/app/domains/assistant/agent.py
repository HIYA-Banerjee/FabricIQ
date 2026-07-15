import re
import json
from sqlalchemy.orm import Session
from app.models.models import Order, Machine, Worker, Supplier, PredictionHistory
from app.services.prediction_service import PredictionService
from app.simulator.scenario_runner import ScenarioRunner
from app.schemas.prediction import ScenarioRequest
from app.services.optimization_service import OptimizationService
from loguru import logger

class AgenticAIAssistant:
    @staticmethod
    def answer_query(db: Session, query: str, tenant_id: str) -> dict:
        """
        Agentic AI Layer:
        Parses query, decides which tool(s) to call, runs the tool(s),
        and builds a natural language response with tool logs and reasoning steps.
        """
        logger.info(f"Agentic AI received query: '{query}' for tenant {tenant_id}")
        
        normalized = query.lower()
        tool_calls = []
        thought_steps = []
        
        # Tool 1: Run Scenario Analysis Tool
        if "what happens if" in normalized or "scenario" in normalized or "what if" in normalized:
            thought_steps.append("Intent detected: What-If Production Scenario Simulation.")
            
            # Extract possible machine outage
            mac_match = re.search(r'(mac-\w+-\d+)', normalized)
            # Extract possible supplier delay
            sup_match = re.search(r'(sup-\w+-\d+)', normalized)
            # Extract delay days
            days_match = re.search(r'(\d+)\s+day', normalized)
            # Extract rush quantity
            qty_match = re.search(r'(\d+)\s+unit', normalized)
            
            machine_outage = mac_match.group(1).upper() if mac_match else None
            supplier_id = sup_match.group(1).upper() if sup_match else None
            delay_days = float(days_match.group(1)) if days_match else 0.0
            
            rush_qty = float(qty_match.group(1)) if qty_match else 0.0
            rush_mat = "Cotton" if "cotton" in normalized else "Polyester" if "polyester" in normalized else None
            
            req = ScenarioRequest(
                machine_id_outage=machine_outage,
                supplier_id_delay=supplier_id,
                supplier_delay_days=delay_days,
                rush_order_qty=rush_qty,
                rush_order_material=rush_mat
            )
            
            thought_steps.append(f"Invoking Tool 'RunScenarioAnalysisTool' with args: {req.model_dump()}")
            tool_res = ScenarioRunner.run_simulation(db, req, tenant_id)
            
            tool_calls.append({
                "tool_name": "RunScenarioAnalysisTool",
                "tool_args": req.model_dump(),
                "tool_output": tool_res.model_dump()
            })
            
            ans = (
                f"I simulated the scenario: '{tool_res.scenario_description}'. "
                f"If this occurs, the number of delayed orders is predicted to change from "
                f"{tool_res.original_delayed_orders} to {tool_res.simulated_delayed_orders}, "
                f"with a revenue-at-risk of ${tool_res.revenue_at_risk:,.2f}. "
                f"Proposed mitigations: {', '.join(tool_res.mitigation_actions)}"
            )
            
        # Tool 2: Schedule Optimizer Tool
        elif "optimize" in normalized or "schedule" in normalized or "gantt" in normalized:
            thought_steps.append("Intent detected: Optimize Schedule.")
            thought_steps.append("Invoking Tool 'OptimizeScheduleTool'.")
            
            opt_res = OptimizationService.get_optimized_schedule(db, tenant_id)
            tool_calls.append({
                "tool_name": "OptimizeScheduleTool",
                "tool_args": {},
                "tool_output": {
                    "success": opt_res.get("success", False),
                    "makespan_hours": opt_res.get("makespan_hours", 0),
                    "delayed_orders": opt_res.get("delayed_orders_count", 0)
                }
            })
            
            if opt_res.get("success"):
                ans = (
                    f"I executed the schedule optimization engine. "
                    f"The optimal machine routing completes all operations in {opt_res['makespan_hours']} hours "
                    f"and minimizes delivery delays down to {opt_res['delayed_orders_count']} orders. "
                    f"You can review the updated Gantt layout on the Scheduler page."
                )
            else:
                ans = f"The optimization engine finished with warnings: {opt_res.get('message', 'Unknown issue')}"

        # Tool 3: Predict Order Delay Tool
        elif "why is" in normalized or "delay risk" in normalized or "ord-" in normalized:
            thought_steps.append("Intent detected: Check Order Delay Cause.")
            ord_match = re.search(r'(ord-\w+-\d+)', normalized)
            
            if ord_match:
                order_id = ord_match.group(1).upper()
                thought_steps.append(f"Invoking Tool 'PredictOrderDelayTool' for order ID {order_id}")
                pred = PredictionService.get_order_prediction(db, order_id, tenant_id)
                
                tool_calls.append({
                    "tool_name": "PredictOrderDelayTool",
                    "tool_args": {"order_id": order_id},
                    "tool_output": pred
                })
                
                if pred:
                    shaps = ", ".join([f"{k} ({'+' if v>0 else ''}{v*100:.1f}%)" for k, v in pred["shap_values"].items() if abs(v) > 0.01])
                    ans = (
                        f"Order {order_id} has a {pred['probability']*100:.1f}% risk of delay (Classification: {pred['risk']}). "
                        f"Explainable AI (SHAP) attributions indicate the main drivers are: {shaps}. "
                        f"Actions: {', '.join(pred['recommendations'])}"
                    )
                else:
                    ans = f"I could not find order record {order_id} in this factory."
            else:
                ans = "Please specify the Order ID (e.g. ORD-factory_alpha-1001) so I can fetch its explainability metrics."

        # Tool 4: General Database Summary Tool
        else:
            thought_steps.append("Intent detected: Query Factory Status.")
            thought_steps.append("Invoking Tool 'DatabaseQueryTool'.")
            
            orders = db.query(Order).filter(Order.tenant_id == tenant_id).all()
            machines = db.query(Machine).filter(Machine.tenant_id == tenant_id).all()
            
            # Count values
            total_orders = len(orders)
            in_prog = len([o for o in orders if o.status == "In Progress"])
            delayed = len([o for o in orders if o.status == "Delayed"])
            broken_macs = len([m for m in machines if m.status in ("Error", "Maintenance")])
            
            db_out = {
                "total_orders": total_orders,
                "in_progress_orders": in_prog,
                "delayed_orders": delayed,
                "offline_machines": broken_macs
            }
            
            tool_calls.append({
                "tool_name": "DatabaseQueryTool",
                "tool_args": {"metrics": ["orders", "machines"]},
                "tool_output": db_out
            })
            
            ans = (
                f"Currently, there are {total_orders} total orders ({in_prog} in progress, {delayed} delayed). "
                f"On the shop floor, {broken_macs} machines are currently offline for maintenance or error repair. "
                f"How else can I assist with production scheduler runs or what-if scenario simulations?"
            )
            
        return {
            "answer": ans,
            "thought_process": " -> ".join(thought_steps),
            "tool_calls": tool_calls
        }
