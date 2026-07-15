import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

NUMERIC_FEATURES = [
    "quantity", "progress", "days_elapsed", "days_to_due", "qty_remaining",
    "required_rate", "schedule_variance", "avg_daily_rate", "velocity_ratio",
    "machine_avg_failure_prob", "worker_avg_productivity", "supplier_delay_rate"
]

CATEGORICAL_FEATURES = [
    "material_type", "priority"
]

class PreprocessingPipeline:
    def __init__(self):
        self.scaler = StandardScaler()
        self.material_categories = ["Cotton", "Polyester", "Silk", "Wool", "Linen"]
        self.priority_categories = ["Low", "Medium", "High"]
        
    def fit(self, df: pd.DataFrame):
        # Fit numerical features
        available_numeric = [f for f in NUMERIC_FEATURES if f in df.columns]
        if available_numeric:
            # fill na with median
            self.scaler.fit(df[available_numeric].fillna(0.0))
            
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        df_out = df.copy()
        
        # Numeric scaling
        available_numeric = [f for f in NUMERIC_FEATURES if f in df_out.columns]
        if available_numeric:
            df_out[available_numeric] = df_out[available_numeric].fillna(0.0)
            df_out[available_numeric] = self.scaler.transform(df_out[available_numeric])
            
        # Manual one-hot encoding to guarantee stable shapes for XGBoost
        for cat in self.material_categories:
            df_out[f"material_{cat}"] = (df_out["material_type"] == cat).astype(float)
            
        for p in self.priority_categories:
            df_out[f"priority_{p}"] = (df_out["priority"] == p).astype(float)
            
        # Select final feature columns list
        cols_to_keep = available_numeric + [f"material_{c}" for c in self.material_categories] + [f"priority_{p}" for p in self.priority_categories]
        
        return df_out[cols_to_keep]
