import os
import numpy as np
import pandas as pd
# pyrefly: ignore [missing-import]
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sqlalchemy.orm import Session  # pyrefly: ignore [missing-import]
from app.db.session import SessionLocal
from app.simulator.factory_simulator import seed_database
from app.ml.dataset import load_ml_dataset
from app.ml.preprocessing import PreprocessingPipeline
from app.ml.model_loader import ModelLoader
from loguru import logger  # pyrefly: ignore [missing-import]

def train_and_register_models(version: str = "v1"):
    """
    Trained models:
    - XGBoost for Order Delay Prediction
    - Random Forest for Machine Failure (Predictive Maintenance)
    """
    db = SessionLocal()
    try:
        # Seed if empty
        orders_count = db.query(load_ml_dataset).count() if hasattr(load_ml_dataset, "count") else 0
        from app.models.models import Order
        if db.query(Order).count() == 0:
            logger.info("Database is empty. Seeding database with synthetic simulator data...")
            seed_database(db, "factory_alpha")
            seed_database(db, "factory_beta")
            
        # 1. Delay Prediction Dataset
        df = load_ml_dataset(db)
        if df.empty or len(df) < 5:
            logger.error("Insufficient dataset rows to train models.")
            return False
            
        X = df.drop(columns=["target"])
        y = df["target"]
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Fit Preprocessor
        pipeline = PreprocessingPipeline()
        pipeline.fit(X_train)
        
        X_train_processed = pipeline.transform(X_train)
        X_test_processed = pipeline.transform(X_test)
        
        # Train XGBoost
        logger.info("Training XGBoost Classifier for Delay Prediction...")
        delay_model = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
        delay_model.fit(X_train_processed, y_train)
        
        # Evaluate Delay Model
        y_pred = delay_model.predict(X_test_processed)
        y_prob = delay_model.predict_proba(X_test_processed)[:, 1] if hasattr(delay_model, "predict_proba") else y_pred
        
        # Calculate metrics
        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        try:
            auc = float(roc_auc_score(y_test, y_prob))
        except Exception:
            auc = 0.5
            
        metrics = {
            "delay_model": {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "roc_auc": auc
            }
        }
        
        logger.info(f"Delay Model Metrics: Accuracy={acc:.3f}, F1={f1:.3f}, ROC-AUC={auc:.3f}")
        
        # 2. Predictive Maintenance (Machine Failure)
        # We synthesize machine state predictors (runtimes, efficiency, maintenance logs)
        from app.models.models import Machine
        machines = db.query(Machine).all()
        mac_data = []
        for m in machines:
            # Simulate historical runs
            for _ in range(50):
                runtime = np.random.uniform(10.0, 3000.0)
                util = np.random.uniform(0.1, 1.0)
                maint = np.random.randint(0, 10)
                # Failure condition (1 = failure, 0 = active)
                fail = 1 if (runtime / 2500.0) * util + (0.1 * maint) > np.random.uniform(0.6, 1.2) else 0
                mac_data.append([runtime, util, maint, fail])
                
        mac_df = pd.DataFrame(mac_data, columns=["runtime", "utilization", "maintenance_count", "failed"])
        
        X_mac = mac_df[["runtime", "utilization", "maintenance_count"]]
        y_mac = mac_df["failed"]
        
        X_mac_train, X_mac_test, y_mac_train, y_mac_test = train_test_split(X_mac, y_mac, test_size=0.2, random_state=42)
        
        logger.info("Training Random Forest Classifier for Predictive Maintenance...")
        maint_model = RandomForestClassifier(n_estimators=50, random_state=42)
        maint_model.fit(X_mac_train, y_mac_train)
        
        y_mac_pred = maint_model.predict(X_mac_test)
        m_acc = float(accuracy_score(y_mac_test, y_mac_pred))
        m_f1 = float(f1_score(y_mac_test, y_mac_pred, zero_division=0))
        
        metrics["maintenance_model"] = {
            "accuracy": m_acc,
            "f1_score": m_f1
        }
        
        logger.info(f"Predictive Maintenance Metrics: Accuracy={m_acc:.3f}, F1={m_f1:.3f}")
        
        # Save both inside a container object or save delay model as main, maintenance model as separate attribute
        # We can wrap both in a dictionary and save it as the pickle payload, or save it inside the same model.pkl
        package = {
            "delay_model": delay_model,
            "maintenance_model": maint_model
        }
        
        ModelLoader.save_model_artifact(package, pipeline, metrics, version)
        
        # Save model_metrics.json for root evaluate logs
        with open("model_metrics.json", "w") as f:
            import json
            json.dump(metrics, f, indent=4)
            
        return True
    except Exception as e:
        logger.exception(f"Error during training process: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    train_and_register_models()
