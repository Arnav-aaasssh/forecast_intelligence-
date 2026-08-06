import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Dict

from core.contracts.decision import PolicyEvaluationMatrix, DecisionContract
from core.config.models import EnterpriseConfig
from core.validation.exceptions import AnalyticsException

@dataclass(frozen=True)
class DecisionEvaluation:
    decision_state: str
    deployment_strategy: str
    selected_model: str

class DecisionValidator:
    """
    Validates the integrity of the PolicyEvaluationMatrix before synthesis.
    """
    def validate(self, matrix: PolicyEvaluationMatrix):
        if not isinstance(matrix, PolicyEvaluationMatrix):
            raise AnalyticsException("SYN-001", "SYNTHESIS_ERROR", "Input must be a PolicyEvaluationMatrix.", "Provide valid matrix.")
        if not matrix.evaluations:
            raise AnalyticsException("SYN-002", "SYNTHESIS_ERROR", "PolicyEvaluationMatrix is empty.", "Run policy engine first.")
            
        policy_names = [ev.policy_name for ev in matrix.evaluations]
        if len(policy_names) != len(set(policy_names)):
            raise AnalyticsException("SYN-003", "SYNTHESIS_ERROR", "Duplicate policy evaluations found.", "Ensure policies are unique.")

class DecisionStateMachine:
    """
    Deterministic state machine for synthesizing business decisions.
    """
    def synthesize(self, matrix: PolicyEvaluationMatrix) -> DecisionEvaluation:
        evals: Dict[str, str] = {ev.policy_name: ev.status for ev in matrix.evaluations}
        
        # 1. Check for Suppression
        if any(status == "SUPPRESSED" for status in evals.values()):
            return DecisionEvaluation("NO_DECISION", "NONE", "NONE")
            
        superiority = evals.get("ML_SUPERIORITY_POLICY", "NOT_APPLICABLE")
        confidence = evals.get("CONFIDENCE_POLICY", "NOT_APPLICABLE")
        coverage = evals.get("COVERAGE_POLICY", "NOT_APPLICABLE")
        
        # 2. Baseline Superiority Failure
        if superiority == "FAIL":
            return DecisionEvaluation("RETAIN", "NONE", "BASELINE")
            
        # 3. Greenfield (No baseline)
        if superiority == "NOT_APPLICABLE":
            if confidence == "FAIL" or coverage == "FAIL":
                return DecisionEvaluation("DEPLOY", "PILOT", "PRIMARY")
            return DecisionEvaluation("DEPLOY", "GLOBAL", "PRIMARY")

        # 4. Standard Flow (Superiority passed)
        if superiority == "PASS":
            if confidence == "PASS" and coverage == "PASS":
                return DecisionEvaluation("DEPLOY", "GLOBAL", "PRIMARY")
            elif confidence == "PASS" and coverage == "FAIL":
                return DecisionEvaluation("DEPLOY", "PILOT", "PRIMARY")
            elif confidence == "FAIL":
                # Failing confidence implies we pilot it to gather more data, or retain.
                # In standard practices, failing confidence might retain, but let's pilot.
                return DecisionEvaluation("DEPLOY", "PILOT", "PRIMARY")
                
        raise AnalyticsException("SYN-004", "SYNTHESIS_ERROR", "Unknown state machine transition.", "Check policy outcomes.")

class DecisionSynthesizer:
    def __init__(self, config: EnterpriseConfig):
        self.config = config
        self.validator = DecisionValidator()
        self.state_machine = DecisionStateMachine()
        
    def execute(self, matrix: PolicyEvaluationMatrix) -> DecisionContract:
        self.validator.validate(matrix)
        
        evaluation = self.state_machine.synthesize(matrix)
        
        return DecisionContract(
            decision_state=evaluation.decision_state,
            deployment_strategy=evaluation.deployment_strategy,
            selected_model=evaluation.selected_model,
            policy_evaluation_reference=matrix.evaluations,
            decision_evaluation_reference=uuid.uuid4(),
            execution_context=matrix.execution_context,
            configuration_version="1.0",
            decision_timestamp=datetime.now(timezone.utc),
            traceability_id=uuid.uuid4(),
            version="1.0"
        )
