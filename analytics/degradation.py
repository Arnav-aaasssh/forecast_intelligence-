import pandas as pd
from typing import List
from .models import DegradationEvidence, Anomaly

def associate_degradation(bt: pd.DataFrame, recommended_model: str, actual_anomalies: List[Anomaly]) -> List[DegradationEvidence]:
    """
    Identifies Forecast Degradation Drivers.
    Associates high model error with deterministic environmental anomalies.
    Returns purely analytical evidence, no English strings.
    """
    if bt.empty or not actual_anomalies:
        return []
        
    sub = bt[bt["Model"] == recommended_model]
    if sub.empty:
        return []
        
    weekly = sub.groupby("Week_Ending").apply(
        lambda g: g["abs_err"].sum() / g["Actual_Offered"].sum() if g["Actual_Offered"].sum() else 0
    )
    
    mean_wape = weekly.mean()
    std_wape = weekly.std()
    
    indicators = []
    
    anomaly_weeks = [a.week for a in actual_anomalies]
    
    for week_ending, wape in weekly.items():
        week_str = str(week_ending)[:10]
        if week_str in anomaly_weeks:
            if wape > mean_wape + std_wape:
                matching_anomaly = next((a for a in actual_anomalies if a.week == week_str), None)
                if matching_anomaly:
                    z = matching_anomaly.z_score
                    direction = "spike" if z > 0 else "drop"
                    
                    indicators.append(DegradationEvidence(
                        model_name=recommended_model,
                        week_ending=week_str,
                        wape=wape,
                        volatility=0.0,
                        anomaly_flag=True,
                        z_score=z,
                        direction=direction
                    ))
                    
    return indicators
