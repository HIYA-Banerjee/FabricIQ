import pandas as pd
import numpy as np
from datetime import datetime

def engineer_order_features(orders_df: pd.DataFrame, logs_df: pd.DataFrame, 
                             machines_df: pd.DataFrame, workers_df: pd.DataFrame, 
                             suppliers_df: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """
    Computes advanced features for order delay prediction:
    - days_to_due
    - progress
    - qty_remaining
    - required_rate
    - avg_daily_rate
    - schedule_variance
    - machine_avg_failure_prob
    - worker_avg_productivity
    - supplier_delay_rate
    """
    if reference_date is None:
        reference_date = datetime.utcnow()
        
    df = orders_df.copy()
    
    # Cast dates
    df["start_date"] = pd.to_datetime(df["start_date"])
    df["due_date"] = pd.to_datetime(df["due_date"])
    
    # Time-based features
    df["total_duration_days"] = (df["due_date"] - df["start_date"]).dt.days.clip(lower=1)
    df["days_elapsed"] = (reference_date - df["start_date"]).dt.days.clip(lower=0)
    df["days_to_due"] = (df["due_date"] - reference_date).dt.days
    
    # Progress features
    df["qty_remaining"] = df["quantity"] * (1.0 - df["progress"])
    
    # Required production rate to hit deadline
    df["required_rate"] = df.apply(
        lambda row: row["qty_remaining"] / max(0.5, row["days_to_due"]) if row["days_to_due"] > 0 else row["qty_remaining"] * 2.0, 
        axis=1
    )
    
    # Schedule Variance (progress relative to time elapsed)
    df["expected_progress"] = (df["days_elapsed"] / df["total_duration_days"]).clip(upper=1.0)
    df["schedule_variance"] = df["progress"] - df["expected_progress"]
    
    # Calculate avg daily rate from production logs
    daily_rates = {}
    if not logs_df.empty:
        logs_df["date"] = pd.to_datetime(logs_df["date"])
        grouped_logs = logs_df.groupby("order_id")
        for order_id, group in grouped_logs:
            unique_days = group["date"].dt.date.nunique()
            total_produced = group["quantity_produced"].sum()
            daily_rates[order_id] = total_produced / max(1, unique_days)
            
    df["avg_daily_rate"] = df["id"].map(daily_rates).fillna(0.0)
    # Velocity Ratio (actual daily production vs required daily rate)
    df["velocity_ratio"] = df.apply(
        lambda row: row["avg_daily_rate"] / max(0.1, row["required_rate"]),
        axis=1
    )

    # Machine-linked features
    avg_mach_fail = 0.15
    if not machines_df.empty:
        avg_mach_fail = machines_df["failure_probability"].mean()
        
    df["machine_avg_failure_prob"] = avg_mach_fail
    
    # Worker-linked features
    avg_wrk_prod = 0.85
    if not workers_df.empty:
        avg_wrk_prod = workers_df["productivity"].mean()
        
    df["worker_avg_productivity"] = avg_wrk_prod
    
    # Supplier-linked features
    supplier_delay_rates = {}
    if not suppliers_df.empty:
        for idx, row in suppliers_df.iterrows():
            supplier_delay_rates[row["material"]] = row["delay_rate"]
            
    df["supplier_delay_rate"] = df["material_type"].map(supplier_delay_rates).fillna(0.10)
    
    # Drop timestamp columns for training, keep relevant float/int features
    return df
