from typing import List, Optional
from .models import ReportSection, ReportTable, EvidenceMetric, TraceabilityMetadata
from analytics.models import DegradationEvidence

def build_q4_drivers(anomalies_count: int, degradations: List[DegradationEvidence]) -> ReportSection:
    """Builds the Q4 Forecast Degradation analysis section."""
    
    trace_meta = TraceabilityMetadata(
        source_layer="Content Engine",
        originating_contract_types=["DegradationEvidence"]
    )
    
    if anomalies_count == 0:
        return ReportSection(
            title="Forecast Degradation Analysis",
            business_question="Did unexpected volume spikes or drops cause the forecast to fail?",
            observation="No statistical anomalies were detected in the volume actuals.",
            traceability_metadata=trace_meta,
            primary_evidence=[
                EvidenceMetric(name="Anomalies Detected", value="0")
            ],
            supporting_evidence=[],
            conclusion="Volume remained statistically stable.",
            decision_support="Accuracy results represent the true capability of the models.",
            recommendation=None,
            is_condensed=True,
            recommendation_suppressed=True,
            charts=[],
            tables=[],
            appendix_references=[]
        )
        
    severe_degradations = [d for d in degradations if abs(d.wape) >= 0.15]
    
    if severe_degradations:
        obs = f"Detected {len(severe_degradations)} severe forecast degradation events coinciding with volume anomalies."
        conc = "Anomalous business events contributed to substantial degradation in forecast accuracy."
        support = "Model accuracy metrics were penalised by non-repeating external shocks."
    else:
        obs = f"Detected {anomalies_count} volume anomalies, but none coincided with severe forecast degradation."
        conc = "The champion model successfully maintained accuracy despite anomalous volume events."
        support = "The evaluated model demonstrated resilience against external volume shocks."

    tables = []
    if degradations:
        headers = ["Week", "Z-Score", "Direction", "Associated Error (WAPE)"]
        rows = []
        for d in degradations:
            rows.append([
                d.week_ending,
                f"{d.z_score:.2f}",
                d.direction,
                f"{d.wape:.2%}"
            ])
        tables.append(ReportTable(headers=headers, rows=rows))

    return ReportSection(
        title="Forecast Degradation Analysis",
        business_question="Did unexpected volume spikes or drops cause the forecast to fail?",
        observation=obs,
        traceability_metadata=trace_meta,
        primary_evidence=[
            EvidenceMetric(name="Total Anomalies", value=str(anomalies_count)),
            EvidenceMetric(name="Severe Degradation Events", value=str(len(severe_degradations)))
        ],
        supporting_evidence=[
        ],
        conclusion=conc,
        decision_support=support,
        recommendation=None,
        is_condensed=False,
        recommendation_suppressed=True,
        charts=[],
        tables=tables,
        appendix_references=["Appendix B: Detailed Event Timeline"]
    )
