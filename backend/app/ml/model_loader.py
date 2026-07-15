import os
import pickle
import json
from loguru import logger
from app.core.config import settings

class ModelLoader:
    @staticmethod
    def save_model_artifact(model, pipeline, metrics: dict, version: str = "v1"):
        """
        Saves the model classifier, preprocessing pipeline and evaluation metrics 
        to a specific version folder in the model registry.
        """
        version_dir = os.path.join(settings.MODEL_REGISTRY_DIR, version)
        os.makedirs(version_dir, exist_ok=True)
        
        model_path = os.path.join(version_dir, "model.pkl")
        pipeline_path = os.path.join(version_dir, "pipeline.pkl")
        metrics_path = os.path.join(version_dir, "metrics.json")
        
        # Save model
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
            
        # Save pipeline
        with open(pipeline_path, "wb") as f:
            pickle.dump(pipeline, f)
            
        # Save metrics
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)
            
        # Save general registry metadata
        registry_meta = os.path.join(settings.MODEL_REGISTRY_DIR, "metadata.json")
        meta = {}
        if os.path.exists(registry_meta):
            try:
                with open(registry_meta, "r") as f:
                    meta = json.load(f)
            except Exception:
                pass
        
        meta["latest_version"] = version
        meta[version] = {
            "created_at": str(os.path.getmtime(model_path)),
            "metrics": metrics
        }
        with open(registry_meta, "w") as f:
            json.dump(meta, f, indent=4)
            
        logger.info(f"Model version {version} saved successfully to registry.")

    @staticmethod
    def load_model_artifact(version: str = None):
        """
        Loads the classifier and preprocessor. If version is None, loads the latest version.
        Falls back to a newly initialized dummy model if registry is empty.
        """
        registry_meta = os.path.join(settings.MODEL_REGISTRY_DIR, "metadata.json")
        
        if not version and os.path.exists(registry_meta):
            try:
                with open(registry_meta, "r") as f:
                    meta = json.load(f)
                    version = meta.get("latest_version", "v1")
            except Exception:
                version = "v1"
        elif not version:
            version = "v1"
            
        version_dir = os.path.join(settings.MODEL_REGISTRY_DIR, version)
        model_path = os.path.join(version_dir, "model.pkl")
        pipeline_path = os.path.join(version_dir, "pipeline.pkl")
        
        if os.path.exists(model_path) and os.path.exists(pipeline_path):
            try:
                with open(model_path, "rb") as f:
                    model = pickle.load(f)
                with open(pipeline_path, "rb") as f:
                    pipeline = pickle.load(f)
                logger.info(f"Loaded model version {version} from registry.")
                return model, pipeline, version
            except Exception as e:
                logger.error(f"Failed to load model {version}: {str(e)}")
                
        # Return fallback dummy model to ensure FastAPI doesn't crash on startup
        logger.warning("No model found in registry. Generating simple rule-based fallback mock.")
        from xgboost import XGBClassifier
        from app.ml.preprocessing import PreprocessingPipeline
        
        dummy_model = XGBClassifier()
        dummy_pipeline = PreprocessingPipeline()
        return dummy_model, dummy_pipeline, "mock_fallback"
