import pandas as pd
import numpy as np
from .models import ActualsAnalysis, Anomaly

def analyze_actuals(bt: pd.DataFrame) -> ActualsAnalysis:
    """
    Analyzes actuals across time for trend, volatility, and anomalies.
    Does NOT infer seasonality due to short timeframes.
    """
    if bt.empty:
        return ActualsAnalysis(0.0, 0.0, "Unknown", [])

    # Get weekly volume sums across all queues to represent total demand
    weekly_actuals = bt.groupby("Week_Ending")["Actual_Offered"].sum().sort_index()
    
    if len(weekly_actuals) < 3:
        return ActualsAnalysis(0.0, 0.0, "Unknown", [])

    mean_vol = weekly_actuals.mean()
    std_vol = weekly_actuals.std()
    
    # 1. Volatility
    cv = std_vol / mean_vol if mean_vol else 0
    
    # 2. Trend (simple linear fit on time index)
    x = np.arange(len(weekly_actuals))
    y = weekly_actuals.values
    
    trend_direction = "Flat"
    if len(weekly_actuals) >= 4:
        poly = np.polyfit(x, y, 1)
        slope = poly[0]
        # Normalize slope as % of mean
        norm_slope = slope / mean_vol if mean_vol else 0
        if norm_slope > 0.02:
            trend_direction = "Increasing"
        elif norm_slope < -0.02:
            trend_direction = "Decreasing"
            
    # 3. Anomalies (Z-Score > 2.5)
    anomalies = []
    if std_vol > 0:
        z_scores = (weekly_actuals - mean_vol) / std_vol
        anomaly_weeks = z_scores[z_scores.abs() > 2.5]
        for date, z in anomaly_weeks.items():
            anomalies.append(Anomaly(
                week=str(date)[:10],
                z_score=float(z),
                volume=float(weekly_actuals.loc[date])
            ))
            
    return ActualsAnalysis(
        mean_volume=float(mean_vol),
        volatility_cv=float(cv),
        trend=trend_direction,
        anomalies=anomalies
    )
