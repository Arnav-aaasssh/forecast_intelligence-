from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass(frozen=True)
class ReportTable:
    headers: List[str]
    rows: List[List[Any]]

@dataclass(frozen=True)
class ChartDescriptor:
    chart_type: str
    title: str
    data_references: List[str]
    description: str

@dataclass(frozen=True)
class EvidenceMetric:
    name: str
    value: str

@dataclass(frozen=True)
class TraceabilityMetadata:
    source_layer: str
    originating_contract_types: List[str]
    
@dataclass(frozen=True)
class ReportSection:
    title: str
    business_question: str
    observation: str
    
    # Traceability
    traceability_metadata: TraceabilityMetadata
    
    # New V3 Fields
    primary_evidence: List[EvidenceMetric] = field(default_factory=list)
    supporting_evidence: List[EvidenceMetric] = field(default_factory=list)
    conclusion: str = ""
    decision_support: str = ""
    recommendation: Optional[str] = None
    
    is_condensed: bool = False
    recommendation_suppressed: bool = False
    
    tables: List[ReportTable] = field(default_factory=list)
    charts: List[ChartDescriptor] = field(default_factory=list)
    appendix_references: List[str] = field(default_factory=list)

@dataclass(frozen=True)
class ContentContract:
    executive_summary: ReportSection
    q1_assessment: Optional[ReportSection]
    q2_evaluation: Optional[ReportSection]
    q3_actuals: ReportSection
    q4_drivers: ReportSection
    appendix: ReportSection

@dataclass(frozen=True)
class DecisionContract:
    action: str
    deployment_scenario_name: str
    is_greenfield: bool

@dataclass(frozen=True)
class AnalyticsContract:
    overall_confidence: str
    baseline_wape: Optional[float]
    challenger_wape: float

@dataclass(frozen=True)
class Q1Contract:
    has_baseline: bool
    manual_wape: float
    ml_wape: float
    ml_won: bool
    confidence_level: str
    action_recommendation: str
