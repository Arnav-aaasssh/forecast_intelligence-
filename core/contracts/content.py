from dataclasses import dataclass
from typing import Tuple
from core.foundation.execution_context import ExecutionContext
from .exceptions import ContractValidationException

@dataclass(frozen=True)
class ReportMetadata:
    title: str
    executive_summary: str
    generated_at: str
    version: str

@dataclass(frozen=True)
class ReportDocument:
    execution_context_id: str
    traceability_id: str
    metadata: ReportMetadata
    sections: Tuple['StructuredSection', ...]
    assets: Tuple[str, ...]
    appendices: Tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.execution_context_id, str):
            raise ContractValidationException("execution_context_id must be a string.")
        if not isinstance(self.traceability_id, str):
            raise ContractValidationException("traceability_id must be a string.")
        if not isinstance(self.metadata, ReportMetadata):
            raise ContractValidationException("metadata must be ReportMetadata.")
        if not isinstance(self.sections, tuple):
            raise ContractValidationException("sections must be a tuple.")
        if not isinstance(self.assets, tuple):
            raise ContractValidationException("assets must be a tuple.")
        if not isinstance(self.appendices, tuple):
            raise ContractValidationException("appendices must be a tuple.")

@dataclass(frozen=True)
class EvidenceMetric:
    name: str
    value: float
    unit: str
    is_primary: bool

@dataclass(frozen=True)
class BusinessQuestionContract:
    business_question_id: str
    primary_evidence_keys: Tuple[str, ...]
    supporting_evidence_keys: Tuple[str, ...]
    observation_template: str
    conclusion_template: str
    decision_support_template: str

@dataclass(frozen=True)
class StructuredSection:
    business_question_id: str
    
    # Textual Content
    observation: str
    conclusion: str
    decision_support: str
    
    # Evidence
    primary_evidence: Tuple[EvidenceMetric, ...]
    supporting_evidence: Tuple[EvidenceMetric, ...]
    
    # Recommendation
    recommendation: str
    recommendation_suppressed: bool
    
    # Assets
    charts_referenced: Tuple[str, ...]
    
    # Audit & Traceability
    execution_context_id: str # Keep string representation of UUID for simplicity
    traceability_id: str
    version: str
    
    def __post_init__(self):
        if not isinstance(self.business_question_id, str):
            raise ContractValidationException("business_question_id must be a string.")
        if not isinstance(self.primary_evidence, tuple):
            raise ContractValidationException("primary_evidence must be a tuple.")
        if len(self.primary_evidence) > 3:
            raise ContractValidationException("primary_evidence cannot exceed 3 metrics.")
        if not isinstance(self.supporting_evidence, tuple):
            raise ContractValidationException("supporting_evidence must be a tuple.")
        if len(self.supporting_evidence) > 5:
            raise ContractValidationException("supporting_evidence cannot exceed 5 metrics.")
        if self.recommendation_suppressed and self.recommendation != "NONE":
            raise ContractValidationException("If recommendation is suppressed, recommendation must be NONE.")
