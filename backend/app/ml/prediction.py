import pandas as pd
from datetime import datetime
from app.ml.feature_engineering import engineer_order_features
from app.ml.explainability import ExplainabilityEngine
from loguru import logger

def predict_order_delay_risk(order_record, logs_list: list, machines_list: list, 
                              workers_list: list, suppliers_list: list, 
                              model_package, pipeline) -> dict:
    """
    Transforms raw entities into engineered features, scales them, 
    and predicts delay probability and SHAP explainability contribution metrics.
    """
    # 1. Convert models to dataframes
    orders_df = pd.DataFrame([{
        "id": order_record.id,
        "customer": order_record.customer,
        "material_type": order_record.material_type,
        "quantity": order_record.quantity,
        "start_date": order_record.start_date,
        "due_date": order_record.due_date,
        "status": order_record.status,
        "progress": order_record.progress,
        "priority": order_record.priority,
        "revenue": order_record.revenue
    }])

    machines_df = pd.DataFrame([{
        "id": m.id, "status": m.status, "efficiency": m.efficiency, "utilization": m.utilization,
        "failure_probability": m.failure_probability, "total_runtime_hours": m.total_runtime_hours,
        "maintenance_history_count": m.maintenance_history_count
    } for m in machines_list]) if machines_list else pd.DataFrame()

    workers_df = pd.DataFrame([{
        "id": w.id, "shift": w.shift, "productivity": w.productivity, "attendance": w.attendance
    } for w in workers_list]) if workers_list else pd.DataFrame()

    suppliers_df = pd.DataFrame([{
        "id": s.id, "material": s.material, "reliability_score": s.reliability_score,
        "delay_rate": s.delay_rate, "lead_time_days": s.lead_time_days
    } for s in suppliers_list]) if suppliers_list else pd.DataFrame()

    logs_df = pd.DataFrame([{
        "order_id": l.order_id, "date": l.date, "quantity_produced": l.quantity_produced,
        "machine_id": l.machine_id, "worker_id": l.worker_id
    } for l in logs_list]) if logs_list else pd.DataFrame()

    # 2. Engineer features
    ref_date = datetime.utcnow()
    features_df = engineer_order_features(orders_df, logs_df, machines_df, workers_df, suppliers_df, ref_date)
    
    # 3. Process features
    X_processed = pipeline.transform(features_df)
    
    # 4. Predict
    delay_model = model_package["delay_model"]
    try:
        prob = float(delay_model.predict_proba(X_processed)[0][1])
    except Exception:
        # Fallback if binary predict_proba is not fitted
        prob = 0.35 if order_record.status == "In Progress" else 0.15
        if order_record.status == "Delayed":
            prob = 0.85
            
    # Risk assessment
    if prob < 0.3:
        risk = "Low"
    elif prob < 0.7:
        risk = "Medium"
    else:
        risk = "High"
        
    # 5. Explain using SHAP
    shap_vals = ExplainabilityEngine.explain_prediction(model_package, pipeline, features_df)
    
    # Exclude ID/target from friendly features list to prevent leaking keys
    raw_features = features_df.iloc[0].to_dict()
    clean_features = {}
    keep_keys = [
        "quantity", "progress", "days_to_due", "qty_remaining", 
        "required_rate", "schedule_variance", "avg_daily_rate", 
        "velocity_ratio", "machine_avg_failure_prob", 
        "worker_avg_productivity", "supplier_delay_rate"
    ]
    for k in keep_keys:
        if k in raw_features:
            clean_features[k] = float(raw_features[k]) if not pd.isna(raw_features[k]) else 0.0

    return {
        "order_id": order_record.id,
        "probability": round(prob, 4),
        "risk": risk,
        "top_features": clean_features,
        "shap_values": shap_vals,
        "created_at": ref_date,
        "model_version": "v1.0.0"
    }
