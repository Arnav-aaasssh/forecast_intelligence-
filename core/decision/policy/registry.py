from typing import Dict
from core.decision.policy.policies import PolicyEvaluator, MLSuperiorityPolicy, ConfidencePolicy, CoveragePolicy

class PolicyRegistry:
    def __init__(self):
        self._policies: Dict[str, PolicyEvaluator] = {}
        
    def register(self, policy: PolicyEvaluator):
        if policy.policy_name in self._policies:
            raise ValueError(f"Policy {policy.policy_name} is already registered.")
        self._policies[policy.policy_name] = policy
        
    def get_policy(self, policy_name: str) -> PolicyEvaluator:
        if policy_name not in self._policies:
            raise KeyError(f"Policy {policy_name} is not registered.")
        return self._policies[policy_name]
        
    def get_all_policies(self) -> Dict[str, PolicyEvaluator]:
        return self._policies.copy()
        
def create_default_registry() -> PolicyRegistry:
    registry = PolicyRegistry()
    registry.register(MLSuperiorityPolicy())
    registry.register(ConfidencePolicy())
    registry.register(CoveragePolicy())
    return registry
