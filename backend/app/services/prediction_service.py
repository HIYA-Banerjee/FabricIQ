import json
from sqlalchemy.orm import Session
from app.ml.model_loader import ModelLoader
from app.ml.prediction import predict_order_delay_risk
from app.repositories.order_repo import OrderRepository
from app.repositories.machine_repo import MachineRepository
from app.repositories.prediction_repo import PredictionRepository
from app.models.models import ProductionLog, Worker, Supplier
from loguru import logger
import numpy as np

class PredictionService:
    @staticmethod
    def run_batch_predictions(db: Session, tenant_id: str):
        """
        Runs delay predictions for all active (non-completed) orders and updates
        machine failure probabilities (Predictive Maintenance) for the tenant.
        Caches predictions in the database history.
        """
        logger.info(f"Running batch predictions for tenant {tenant_id}...")
        
        # Load Model
        model_package, pipeline, version = ModelLoader.load_model_artifact()
        
        # 1. Update Machine Failure Probabilities (Predictive Maintenance)
        machines = MachineRepository.get_all(db, tenant_id)
        if machines and version != "mock_fallback":
            maint_model = model_package.get("maintenance_model")
            if maint_model:
                for m in machines:
                    # Feature vector for machine: [total_runtime_hours, utilization, maintenance_history_count]
                    feat = np.array([[m.total_runtime_hours, m.utilization, m.maintenance_history_count]])
                    try:
                        prob = float(maint_model.predict_proba(feat)[0][1])
                        m.failure_probability = round(prob, 4)
                        # If failure risk is high, flag maintenance
                        if prob > 0.8:
                            m.status = "Maintenance"
                    except Exception as e:
                        logger.error(f"Failed to predict machine failure: {str(e)}")
                db.commit()

        # 2. Run Delay Predictions
        orders = db.query(OrderRepository.get_all(db, tenant_id)).filter(Order.status != "Completed").all() if hasattr(OrderRepository.get_all, "filter") else OrderRepository.get_all(db, tenant_id)
        active_orders = [o for o in orders if o.status != "Completed"]
        
        logs = db.query(ProductionLog).filter(ProductionLog.tenant_id == tenant_id).all()
        workers = db.query(Worker).filter(Worker.tenant_id == tenant_id).all()
        suppliers = db.query(Supplier).filter(Supplier.tenant_id == tenant_id).all()
        
        results = []
        for order in active_orders:
            # Filter logs for this order
            order_logs = [l for l in logs if l.order_id == order.id]
            
            try:
                pred = predict_order_delay_risk(
                    order, order_logs, machines, workers, suppliers, model_package, pipeline
                )
                
                # Rule-based recommendations linked to SHAP values
                recs = []
                shaps = pred["shap_values"]
                
                if shaps.get("Behind Schedule", 0.0) > 0.05:
                    recs.append("Behind schedule. Assign high-productivity workers to next shift.")
                if shaps.get("Supplier Delivery Risk", 0.0) > 0.05:
                    recs.append(f"Supplier Delay risk detected. Recommend buffer material procurement for {order.material_type}.")
                if shaps.get("High Machine Downtime Risk", 0.0) > 0.05:
                    recs.append("Machine failure risk detected. Schedule preventive inspection immediately.")
                if shaps.get("Low Production Velocity", 0.0) > 0.05:
                    recs.append("Production velocity too low. Reassign weaving tasks to a faster Loom.")
                    
                if not recs:
                    recs.append("Production is normal. Keep standard schedule.")
                    
                pred["recommendations"] = recs
                
                # Cache prediction in Database
                PredictionRepository.save_prediction(
                    db, tenant_id, order.id, pred["probability"], pred["risk"],
                    pred["top_features"], pred["shap_values"], pred["recommendations"], version
                )
                results.append(pred)
            except Exception as e:
                logger.error(f"Error predicting delay for order {order.id}: {str(e)}")
                
        return results

    @staticmethod
    def get_order_prediction(db: Session, order_id: str, tenant_id: str) -> dict:
        """
        Gets cached prediction from the DB, or runs it live if not yet cached.
        """
        cached = PredictionRepository.get_latest_for_order(db, order_id, tenant_id)
        if cached:
            return {
                "order_id": cached.order_id,
                "probability": cached.probability,
                "risk": cached.risk,
                "top_features": json.loads(cached.top_features),
                "shap_values": json.loads(cached.shap_values),
                "recommendations": json.loads(cached.recommendations),
                "created_at": cached.created_at,
                "model_version": cached.model_version
            }
            
        # Run live
        logger.info(f"Prediction not cached for order {order_id}. Running live inference...")
        model_package, pipeline, version = ModelLoader.load_model_artifact()
        
        from app.models.models import Order, Machine, Worker, Supplier, ProductionLog
        order = db.query(Order).filter(Order.id == order_id, Order.tenant_id == tenant_id).first()
        if not order:
            return {}
            
        logs = db.query(ProductionLog).filter(ProductionLog.tenant_id == tenant_id, ProductionLog.order_id == order_id).all()
        machines = db.query(Machine).filter(Machine.tenant_id == tenant_id).all()
        workers = db.query(Worker).filter(Worker.tenant_id == tenant_id).all()
        suppliers = db.query(Supplier).filter(Supplier.tenant_id == tenant_id).all()
        
        pred = predict_order_delay_risk(order, logs, machines, workers, suppliers, model_package, pipeline)
        
        # Recommendations
        recs = []
        shaps = pred["shap_values"]
        if shaps.get("Behind Schedule", 0.0) > 0.05:
            recs.append("Behind schedule. Assign high-productivity workers to next shift.")
        if shaps.get("Supplier Delivery Risk", 0.0) > 0.05:
            recs.append(f"Supplier Delay risk detected. Recommend buffer material procurement for {order.material_type}.")
        if shaps.get("High Machine Downtime Risk", 0.0) > 0.05:
            recs.append("Machine failure risk detected. Schedule preventive inspection immediately.")
        if shaps.get("Low Production Velocity", 0.0) > 0.05:
            recs.append("Production velocity too low. Reassign weaving tasks to a faster Loom.")
        if not recs:
            recs.append("Production is normal. Keep standard schedule.")
        pred["recommendations"] = recs
        
        PredictionRepository.save_prediction(
            db, tenant_id, order.id, pred["probability"], pred["risk"],
            pred["top_features"], pred["shap_values"], pred["recommendations"], version
        )
        return pred
