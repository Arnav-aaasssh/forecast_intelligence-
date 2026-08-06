from datetime import datetime, timezone
import uuid
from typing import Tuple

from core.contracts.analytics import AnalyticalEvidenceBundle
from core.contracts.decision import PolicyEvaluation, PolicyEvaluationMatrix
from core.config.models import EnterpriseConfig
from core.validation.exceptions import AnalyticsException
from core.decision.policy.registry import PolicyRegistry, create_default_registry

class DecisionPolicyEngine:
    """
    Executes business policies against analytical evidence to produce deterministic
    PolicyEvaluations, assembled into an immutable PolicyEvaluationMatrix.
    This engine does NOT synthesize the final decision.
    """
    def __init__(self, config: EnterpriseConfig, registry: PolicyRegistry = None):
        self.config = config
        self.registry = registry or create_default_registry()
        
    def evaluate(self, bundle: AnalyticalEvidenceBundle) -> PolicyEvaluationMatrix:
        if not isinstance(bundle, AnalyticalEvidenceBundle):
            raise AnalyticsException("DEC-001", "POLICY_ERROR", 
                                     "Input must be an AnalyticalEvidenceBundle", 
                                     "Provide valid evidence.")
            
        evaluations = []
        decision_config = self.config.decision
        
        for name, policy in self.registry.get_all_policies().items():
            try:
                result = policy.evaluate(bundle, decision_config)
                if not isinstance(result, PolicyEvaluation):
                    raise AnalyticsException("DEC-002", "POLICY_ERROR", 
                                             f"Policy {name} returned invalid evaluation.", 
                                             "Policies must return PolicyEvaluation.")
                evaluations.append(result)
            except Exception as e:
                raise AnalyticsException("DEC-003", "POLICY_ERROR", 
                                         f"Policy {name} execution failed: {str(e)}", 
                                         "Check policy implementation.", 
                                         execution_context_id=str(bundle.execution_context.run_id)) from e
                
        return PolicyEvaluationMatrix(
            evaluations=tuple(evaluations),
            execution_context=bundle.execution_context,
            evidence_traceability_id=bundle.traceability_id,
            policy_version="1.0", 
            evaluation_timestamp=datetime.now(timezone.utc)
        )
