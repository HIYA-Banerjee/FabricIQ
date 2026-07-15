try:
    from ortools.sat.python import cp_model  # pyrefly: ignore [missing-import]
    OR_TOOLS_AVAILABLE = True
except Exception as e:
    import sys
    print(f"WARNING: OR-Tools could not be imported due to DLL/platform error: {e}", file=sys.stderr)
    OR_TOOLS_AVAILABLE = False
    cp_model = None

from datetime import datetime, timedelta
import pandas as pd
from loguru import logger  # pyrefly: ignore [missing-import]

class ORToolsScheduler:
    @staticmethod
    def optimize_production_schedule(orders: list, machines: list, tenant_id: str) -> dict:
        """
        Formulates and solves a Flexible Job Shop Scheduling problem.
        Assigns order steps (Spinning -> Weaving -> Dyeing -> QC) to machines
        to minimize total completion delays and load balance workloads.
        """
        tasks_per_order = ["Spinning", "Weaving", "Dyeing", "QC"]
        machines_by_type = {}
        for m in machines:
            if m.type not in machines_by_type:
                machines_by_type[m.type] = []
            machines_by_type[m.type].append(m)

        if not OR_TOOLS_AVAILABLE:
            success = False
            curr_hour = 0
            scheduled_jobs = []
            machine_loads = {m.id: 0 for m in machines}
            for idx, order in enumerate(orders):
                order_id = order.id
                for task_name in tasks_per_order:
                    candidate_machines = machines_by_type.get(task_name, [])
                    if candidate_machines:
                        m = candidate_machines[idx % len(candidate_machines)]
                        duration = max(2, int(order.quantity / 50.0))
                        scheduled_jobs.append({
                            "order_id": order_id,
                            "task_name": task_name,
                            "machine_id": m.id,
                            "start_hour": curr_hour,
                            "end_hour": curr_hour + duration,
                            "duration_hours": duration
                        })
                        machine_loads[m.id] += duration
                        curr_hour += duration
            return {
                "success": success,
                "scheduled_jobs": scheduled_jobs,
                "machine_loads": machine_loads,
                "delayed_orders_count": 0,
                "total_delay_hours": 0,
                "makespan_hours": curr_hour
            }

        model = cp_model.CpModel()

        # Max scheduling horizon: e.g. 500 hours
        horizon = 1000
        
        # Variables: start, end, presence, intervals
        all_tasks = {} # (order_id, task_name) -> {machine_id: (start_var, end_var, interval_var, presence_var)}
        machine_intervals = {m.id: [] for m in machines}
        
        # Objective variables
        order_completion_vars = {}
        order_delay_vars = {}
        
        for order in orders:
            order_id = order.id
            due_hours = max(24, int((order.due_date - order.start_date).total_seconds() / 3600.0))
            
            previous_end = None
            
            for task_idx, task_name in enumerate(tasks_per_order):
                # Available machines for this task type
                candidate_machines = machines_by_type.get(task_name, [])
                if not candidate_machines:
                    logger.warning(f"No machines found for task type: {task_name}")
                    continue
                
                # Create boolean variables representing machine selection
                machine_selections = {}
                task_starts = []
                task_ends = []
                
                for m in candidate_machines:
                    presence_var = model.NewBoolVar(f"pres_{order_id}_{task_name}_{m.id}")
                    
                    # Duration depends on machine efficiency and order quantity
                    # Standard rate: 50 units per hour
                    standard_duration = max(2, int(order.quantity / 50.0))
                    duration = int(standard_duration / max(0.1, m.efficiency))
                    
                    start_var = model.NewIntVar(0, horizon, f"start_{order_id}_{task_name}_{m.id}")
                    end_var = model.NewIntVar(0, horizon, f"end_{order_id}_{task_name}_{m.id}")
                    
                    interval_var = model.NewOptionalIntervalVar(
                        start_var, duration, end_var, presence_var, 
                        f"interval_{order_id}_{task_name}_{m.id}"
                    )
                    
                    machine_selections[m.id] = (start_var, end_var, interval_var, presence_var)
                    machine_intervals[m.id].append(interval_var)
                    
                    task_starts.append(start_var)
                    task_ends.append(end_var)
                
                # Constraint: Exactly one machine is selected for each task
                model.AddExactlyOne(pres for (_, _, _, pres) in machine_selections.values())
                
                # Unified start/end variables for the task across all options
                unified_start = model.NewIntVar(0, horizon, f"start_{order_id}_{task_name}")
                unified_end = model.NewIntVar(0, horizon, f"end_{order_id}_{task_name}")
                
                # Link selected machine start/end to unified start/end
                for m_id, (s_var, e_var, _, pres_var) in machine_selections.items():
                    model.Add(unified_start == s_var).OnlyEnforceIf(pres_var)
                    model.Add(unified_end == e_var).OnlyEnforceIf(pres_var)
                    
                # Constraint: Step-by-step sequence order (Spinning -> Weaving -> Dyeing -> QC)
                if previous_end is not None:
                    model.Add(unified_start >= previous_end)
                    
                previous_end = unified_end
                all_tasks[(order_id, task_name)] = machine_selections
                
            # Track final completion time and delay for each order
            if previous_end is not None:
                order_completion_vars[order_id] = previous_end
                
                # Delay = max(0, completion_time - due_hours)
                delay_var = model.NewIntVar(0, horizon, f"delay_{order_id}")
                model.Add(delay_var >= previous_end - due_hours)
                model.Add(delay_var >= 0)
                order_delay_vars[order_id] = delay_var
                
        # Constraint: Machines can only work on one task at a time (NoOverlap)
        for m_id, intervals in machine_intervals.items():
            if intervals:
                model.AddNoOverlap(intervals)
                
        # Objective: Minimize total delay + makespan
        makespan = model.NewIntVar(0, horizon, "makespan")
        if order_completion_vars:
            model.AddMaxEquality(makespan, order_completion_vars.values())
            
        total_delay = sum(order_delay_vars.values())
        
        # Minimizing delay is priority, minimizing makespan is secondary
        model.Minimize(total_delay * 10 + makespan)
        
        # 3. Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 5.0
        status = solver.Solve(model)
        
        scheduled_jobs = []
        machine_loads = {m.id: 0 for m in machines}
        delayed_orders_count = 0
        total_delay_hours = 0
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for (order_id, task_name), machine_selections in all_tasks.items():
                for m_id, (s_var, e_var, _, pres_var) in machine_selections.items():
                    if solver.Value(pres_var):
                        start_val = solver.Value(s_var)
                        end_val = solver.Value(e_var)
                        duration_val = end_val - start_val
                        
                        scheduled_jobs.append({
                            "order_id": order_id,
                            "task_name": task_name,
                            "machine_id": m_id,
                            "start_hour": start_val,
                            "end_hour": end_val,
                            "duration_hours": duration_val
                        })
                        machine_loads[m_id] += duration_val
                        
            for order_id, d_var in order_delay_vars.items():
                d_val = solver.Value(d_var)
                if d_val > 0:
                    delayed_orders_count += 1
                    total_delay_hours += d_val
                    
            success = True
        else:
            # Fallback simple greedy scheduling to make sure the app never hangs
            success = False
            curr_hour = 0
            for idx, order in enumerate(orders):
                order_id = order.id
                for task_name in tasks_per_order:
                    candidate_machines = machines_by_type.get(task_name, [])
                    if candidate_machines:
                        m = candidate_machines[idx % len(candidate_machines)]
                        duration = max(2, int(order.quantity / 50.0))
                        scheduled_jobs.append({
                            "order_id": order_id,
                            "task_name": task_name,
                            "machine_id": m.id,
                            "start_hour": curr_hour,
                            "end_hour": curr_hour + duration,
                            "duration_hours": duration
                        })
                        machine_loads[m.id] += duration
                        curr_hour += duration
            
        return {
            "success": success,
            "scheduled_jobs": scheduled_jobs,
            "machine_loads": machine_loads,
            "delayed_orders_count": delayed_orders_count,
            "total_delay_hours": total_delay_hours,
            "makespan_hours": solver.Value(makespan) if success else curr_hour
        }
