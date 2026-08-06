import inspect
import os
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from .models import ReportSection, EvidenceMetric, TraceabilityMetadata
from analytics.models import ActualsAnalysis

def generate_volume_chart(bt: pd.DataFrame, actuals: ActualsAnalysis, out_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        if "Week_Ending" in bt.columns and "Actual_Offered" in bt.columns:
            bt_copy = bt.copy()
            bt_copy["Week_Ending"] = pd.to_datetime(bt_copy["Week_Ending"])
            weekly = bt_copy.groupby("Week_Ending")["Actual_Offered"].first().sort_index()
            
            plt.figure(figsize=(10, 4))
            plt.plot(weekly.index, weekly.values, marker='o', linestyle='-', color='#2b6cb0', linewidth=2, label="Actual Volume")
            
            anom_dates = []
            anom_vols = []
            if actuals and hasattr(actuals, 'anomalies'):
                for a in actuals.anomalies:
                    date = pd.to_datetime(a.week)
                    anom_dates.append(date)
                    anom_vols.append(a.volume)
                    
            if anom_dates:
                plt.scatter(anom_dates, anom_vols, color='red', s=100, zorder=5, label="Anomalies (Z > 2.5)")
                
            plt.title("Weekly Volume Trend (Actuals)", fontsize=14, color='#1a365d')
            plt.xlabel("Week Ending", fontsize=11)
            plt.ylabel("Actual Volume", fontsize=11)
            plt.grid(True, linestyle='--', alpha=0.6)
            plt.legend()
            plt.tight_layout()
            plt.savefig(out_path, dpi=150)
            plt.close()
            return True
    except Exception as e:
        print(f"Chart generation failed: {e}")
    return False

def build_q3_actuals(actuals: ActualsAnalysis, *args, **kwargs) -> ReportSection:
    """Builds the Business Context Analysis section with V3 content architecture."""
    
    trace_meta = TraceabilityMetadata(
        source_layer="Content Engine",
        originating_contract_types=["ActualsAnalysis"]
    )
    
    cv = actuals.volatility_cv
    anomalies_count = len(actuals.anomalies)
    trend = actuals.trend
    is_highly_volatile = cv > 0.15

    if is_highly_volatile:
        obs_cv = f"Demand variability was high (CV {cv:.2%})."
    else:
        obs_cv = f"Demand variability remained low (CV {cv:.2%})."

    if anomalies_count > 0:
        obs_anom = f"{anomalies_count} statistical anomalies were detected (Z > 2.5)."
    else:
        obs_anom = "No statistical anomalies were detected."

    obs_trend = f"Overall volume exhibits a {trend} trend."
    
    obs = f"{obs_cv} {obs_anom} {obs_trend}"
    
    if is_highly_volatile:
        conc = "Demand exhibited elevated statistical dispersion throughout the evaluation period."
        support = "Volume conditions should be considered when interpreting forecast accuracy from Models."
    else:
        conc = "Demand remained statistically stable throughout the evaluation period."
        support = "Volume conditions should be considered favorable when reviewing forecast accuracy results."

    # Extract backtest dataframe for charting using inspect
    frame = inspect.currentframe().f_back
    bt = None
    while frame:
        if 'bt' in frame.f_locals:
            bt = frame.f_locals.get('bt')
            break
        frame = frame.f_back

    chart_md = ""
    if bt is not None:
        chart_filename = "volume_trend.png"
        chart_path = os.path.join("reports", "charts", chart_filename)
        if generate_volume_chart(bt, actuals, chart_path):
            chart_abs = os.path.abspath(chart_path).replace("\\", "/")
            chart_md = f"\n\n**Charts**\n\n![Weekly Volume Trend]({chart_abs})"
            
    # Compile legacy formatted title with integrated charts to preserve rendering while using dataclass for logic
    full_md = f"""Business Context (Actuals)
{chart_md}
"""

    return ReportSection(
        title=full_md.strip(),
        business_question="Was the underlying demand volume stable enough to be forecasted?",
        observation=obs,
        traceability_metadata=trace_meta,
        primary_evidence=[
            EvidenceMetric(name="Coefficient of Variation", value=f"{cv:.2%}"),
            EvidenceMetric(name="Anomaly Count", value=str(anomalies_count)),
            EvidenceMetric(name="Trend Direction", value=trend)
        ],
        supporting_evidence=[
            EvidenceMetric(name="Mean Volume", value=f"{actuals.mean_volume:,.0f}")
        ],
        conclusion=conc,
        decision_support=support,
        recommendation=None,
        is_condensed=False,
        recommendation_suppressed=True,
        charts=[],
        tables=[],
        appendix_references=[]
    )
