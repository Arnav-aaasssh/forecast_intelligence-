from dataclasses import dataclass
from typing import Tuple, Optional
import uuid
from datetime import datetime
from core.foundation.execution_context import ExecutionContext
from .exceptions import ContractValidationException

@dataclass(frozen=True)
class Q1DecisionContract:
    primary_model: str
    is_retained: bool
    confidence_level: str

@dataclass(frozen=True)
class Q2DecisionContract:
    overall_health: str
    degraded_segments: Tuple[str, ...]

@dataclass(frozen=True)
class Q3DecisionContract:
    forecastability_index: str
    structural_breaks: int

@dataclass(frozen=True)
class Q4DecisionContract:
    shock_detected: bool
    recovery_time: int

@dataclass(frozen=True)
class ExecutiveDecisionContract:
    critical_warnings: int
    requires_manual_intervention: bool

@dataclass(frozen=True)
class DecisionBundle:
    """
    Represents the complete output of the Decision Engine.
    No presentation text is permitted.
    """
    execution_context: ExecutionContext
    policy_version: str
    decision_version: str
    analytics_run_hash: str
    q1: Q1DecisionContract
    q2: Q2DecisionContract
    q3: Q3DecisionContract
    q4: Q4DecisionContract
    executive: ExecutiveDecisionContract

    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ContractValidationException("policy_version must be a non-empty string.")
        if not isinstance(self.decision_version, str) or not self.decision_version.strip():
            raise ContractValidationException("decision_version must be a non-empty string.")
        if not isinstance(self.analytics_run_hash, str) or not self.analytics_run_hash.strip():
            raise ContractValidationException("analytics_run_hash must be a non-empty string.")
        if not isinstance(self.q1, Q1DecisionContract):
            raise ContractValidationException("q1 must be a Q1DecisionContract.")
        if not isinstance(self.q2, Q2DecisionContract):
            raise ContractValidationException("q2 must be a Q2DecisionContract.")
        if not isinstance(self.q3, Q3DecisionContract):
            raise ContractValidationException("q3 must be a Q3DecisionContract.")
        if not isinstance(self.q4, Q4DecisionContract):
            raise ContractValidationException("q4 must be a Q4DecisionContract.")
        if not isinstance(self.executive, ExecutiveDecisionContract):
            raise ContractValidationException("executive must be a ExecutiveDecisionContract.")

@dataclass(frozen=True)
class PolicyEvaluation:
    policy_name: str
    status: str # PASS, FAIL, NOT_APPLICABLE, SUPPRESSED
    reason_code: str
    evaluated_metric_value: float
    applied_threshold: float
    
    def __post_init__(self):
        if not isinstance(self.policy_name, str) or not self.policy_name.strip():
            raise ContractValidationException("policy_name must be a non-empty string.")
        if self.status not in ("PASS", "FAIL", "NOT_APPLICABLE", "SUPPRESSED"):
            raise ContractValidationException("status must be PASS, FAIL, NOT_APPLICABLE, or SUPPRESSED.")
        if not isinstance(self.reason_code, str) or not self.reason_code.strip():
            raise ContractValidationException("reason_code must be a non-empty string.")
        if not isinstance(self.evaluated_metric_value, float):
            raise ContractValidationException("evaluated_metric_value must be a float.")
        if not isinstance(self.applied_threshold, float):
            raise ContractValidationException("applied_threshold must be a float.")

@dataclass(frozen=True)
class PolicyEvaluationMatrix:
    evaluations: Tuple[PolicyEvaluation, ...]
    execution_context: ExecutionContext
    evidence_traceability_id: uuid.UUID
    policy_version: str
    evaluation_timestamp: datetime
    
    def __post_init__(self):
        if not isinstance(self.evaluations, tuple):
            raise ContractValidationException("evaluations must be a tuple of PolicyEvaluation.")
        for ev in self.evaluations:
            if not isinstance(ev, PolicyEvaluation):
                raise ContractValidationException("Every item in evaluations must be a PolicyEvaluation.")
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.evidence_traceability_id, uuid.UUID):
            raise ContractValidationException("evidence_traceability_id must be a uuid.UUID.")
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ContractValidationException("policy_version must be a non-empty string.")
        if not isinstance(self.evaluation_timestamp, datetime):
            raise ContractValidationException("evaluation_timestamp must be a datetime.")

@dataclass(frozen=True)
class DecisionContract:
    decision_state: str  # e.g., DEPLOY, RETAIN, NO_DECISION
    deployment_strategy: str  # e.g., GLOBAL, PILOT, NONE
    selected_model: str
    
    policy_evaluation_reference: Tuple[PolicyEvaluation, ...]
    decision_evaluation_reference: uuid.UUID
    
    execution_context: ExecutionContext
    configuration_version: str
    decision_timestamp: datetime
    traceability_id: uuid.UUID
    version: str
    
    def __post_init__(self):
        if self.decision_state not in ("DEPLOY", "RETAIN", "NO_DECISION"):
            raise ContractValidationException("decision_state must be DEPLOY, RETAIN, or NO_DECISION.")
        if self.deployment_strategy not in ("GLOBAL", "SEGMENTED", "PILOT", "NONE"):
            raise ContractValidationException("deployment_strategy must be GLOBAL, SEGMENTED, PILOT, or NONE.")
        if not isinstance(self.selected_model, str):
            raise ContractValidationException("selected_model must be a string.")
            
        if not isinstance(self.policy_evaluation_reference, tuple):
            raise ContractValidationException("policy_evaluation_reference must be a tuple of PolicyEvaluation.")
        if not isinstance(self.decision_evaluation_reference, uuid.UUID):
            raise ContractValidationException("decision_evaluation_reference must be a uuid.UUID.")
            
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.configuration_version, str) or not self.configuration_version.strip():
            raise ContractValidationException("configuration_version must be a non-empty string.")
        if not isinstance(self.decision_timestamp, datetime):
            raise ContractValidationException("decision_timestamp must be a datetime.")
        if not isinstance(self.traceability_id, uuid.UUID):
            raise ContractValidationException("traceability_id must be a uuid.UUID.")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ContractValidationException("version must be a non-empty string.")
