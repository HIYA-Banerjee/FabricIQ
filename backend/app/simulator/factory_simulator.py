import random
from datetime import datetime, timedelta
from app.models.models import Order, Machine, Worker, Supplier, ProductionLog
from sqlalchemy.orm import Session

# Synthetic settings
MATERIALS = ["Cotton", "Polyester", "Silk", "Wool", "Linen"]
CUSTOMERS = ["DenimCo", "FashionHouse", "TexStyle", "GlobalWeave", "ThreadCorp", "EcoFiber"]
SHIFTS = ["Day", "Evening", "Night"]
MACHINE_TYPES = ["Spinning", "Weaving", "Dyeing", "QC"]

def generate_factory_dataset(tenant_id: str, num_orders: int = 40):
    random.seed(42 if tenant_id == "factory_alpha" else 100)
    
    # 1. Suppliers
    suppliers = []
    supplier_names = [f"Supplier-{tenant_id}-{i}" for i in range(1, 8)]
    for i, name in enumerate(supplier_names):
        mat = random.choice(MATERIALS)
        rel_score = round(random.uniform(70.0, 99.0), 1)
        delay_rate = round((100.0 - rel_score) / 100.0, 3)
        lead_time = round(random.uniform(3.0, 10.0), 1)
        suppliers.append({
            "id": f"SUP-{tenant_id}-{100+i}",
            "name": name,
            "material": mat,
            "reliability_score": rel_score,
            "delay_rate": delay_rate,
            "lead_time_days": lead_time
        })

    # 2. Machines
    machines = []
    # Spinners, Weavers, Dyers, QC machines
    machine_counts = {"Spinning": 3, "Weaving": 4, "Dyeing": 2, "QC": 2}
    mac_idx = 101
    for mtype, count in machine_counts.items():
        for _ in range(count):
            eff = round(random.uniform(0.75, 0.95), 2)
            util = round(random.uniform(0.5, 0.9), 2)
            runtime = round(random.uniform(100.0, 2500.0), 1)
            m_history = random.randint(1, 15)
            # failure prob increases with runtime and utilization
            fail_p = round(min(0.95, (runtime / 3000.0) * util + (0.1 * m_history)), 2)
            status = random.choice(["Running", "Running", "Running", "Idle", "Maintenance"])
            if fail_p > 0.75 and status == "Running":
                status = "Error"
                
            machines.append({
                "id": f"MAC-{tenant_id}-{mac_idx}",
                "name": f"{mtype} Loom #{mac_idx}",
                "type": mtype,
                "status": status,
                "efficiency": eff,
                "utilization": util,
                "failure_probability": fail_p,
                "total_runtime_hours": runtime,
                "maintenance_history_count": m_history
            })
            mac_idx += 1

    # 3. Workers
    workers = []
    worker_names = [
        "Alex Mercer", "Bob Smith", "Carlos Garcia", "Diana Prince", "Emily Watson", 
        "Frank Castle", "Grace Hopper", "Henry Cavill", "Ivan Drago", "Julia Roberts"
    ]
    if tenant_id == "factory_beta":
        worker_names = ["Kate Moss", "Leo Vinci", "Mia Wong", "Nathan Drake", "Olivia Wilde"]
        
    for i, wname in enumerate(worker_names):
        shift = random.choice(SHIFTS)
        prod = round(random.uniform(0.7, 0.98), 2)
        attendance = random.choices([True, False], weights=[0.9, 0.1])[0]
        workers.append({
            "id": f"WRK-{tenant_id}-{200+i}",
            "name": wname,
            "shift": shift,
            "productivity": prod,
            "attendance": attendance
        })

    # 4. Orders & Daily production log
    orders = []
    production_logs = []
    base_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(1, num_orders + 1):
        order_id = f"ORD-{tenant_id}-{1000+i}"
        mat = random.choice(MATERIALS)
        qty = round(random.uniform(500.0, 5000.0), 1)
        start_d = base_date + timedelta(days=random.randint(-15, 10))
        duration = random.randint(10, 25)
        due_d = start_d + timedelta(days=duration)
        
        # Calculate status & progress based on start_date relative to utcnow
        days_since_start = (datetime.utcnow() - start_d).days
        progress = 0.0
        status = "Pending"
        
        if days_since_start > 0:
            if days_since_start >= duration:
                progress = 1.0
                status = "Completed"
            else:
                progress = round(min(0.95, days_since_start / duration), 2)
                status = "In Progress"
                # If behind schedule, label it delayed or let model predict it
                if progress < (days_since_start / duration) - 0.15:
                    status = "Delayed"
        
        priority = random.choices(["Low", "Medium", "High"], weights=[0.2, 0.5, 0.3])[0]
        # Revenue: approx $15 per unit
        revenue = round(qty * random.uniform(12.0, 18.0), 2)

        orders.append({
            "id": order_id,
            "customer": random.choice(CUSTOMERS),
            "material_type": mat,
            "quantity": qty,
            "start_date": start_d,
            "due_date": due_d,
            "status": status,
            "progress": progress,
            "priority": priority,
            "revenue": revenue
        })

        # Production Logs for in progress or completed orders
        if progress > 0:
            qty_to_log = qty * progress
            num_logs = max(1, days_since_start)
            avg_log_qty = qty_to_log / num_logs
            
            for d in range(num_logs):
                log_date = start_d + timedelta(days=d)
                if log_date > datetime.utcnow():
                    break
                selected_mac = random.choice(machines)["id"]
                selected_wrk = random.choice(workers)["id"]
                
                production_logs.append({
                    "tenant_id": tenant_id,
                    "order_id": order_id,
                    "date": log_date,
                    "quantity_produced": round(avg_log_qty * random.uniform(0.8, 1.2), 1),
                    "machine_id": selected_mac,
                    "worker_id": selected_wrk
                })

    return {
        "suppliers": suppliers,
        "machines": machines,
        "workers": workers,
        "orders": orders,
        "production_logs": production_logs
    }

def seed_database(db: Session, tenant_id: str):
    data = generate_factory_dataset(tenant_id)
    
    # Clear existing data for this tenant
    db.query(ProductionLog).filter(ProductionLog.tenant_id == tenant_id).delete()
    db.query(Order).filter(Order.tenant_id == tenant_id).delete()
    db.query(Machine).filter(Machine.tenant_id == tenant_id).delete()
    db.query(Worker).filter(Worker.tenant_id == tenant_id).delete()
    db.query(Supplier).filter(Supplier.tenant_id == tenant_id).delete()
    db.commit()

    # Seed Suppliers
    for s in data["suppliers"]:
        db.add(Supplier(tenant_id=tenant_id, **s))
    
    # Seed Machines
    for m in data["machines"]:
        db.add(Machine(tenant_id=tenant_id, **m))
        
    # Seed Workers
    for w in data["workers"]:
        db.add(Worker(tenant_id=tenant_id, **w))
        
    # Seed Orders
    for o in data["orders"]:
        db.add(Order(tenant_id=tenant_id, **o))
        
    db.commit() # Commit to get relationships wired up
    
    # Seed Production Logs
    for pl in data["production_logs"]:
        db.add(ProductionLog(**pl))
        
    db.commit()
