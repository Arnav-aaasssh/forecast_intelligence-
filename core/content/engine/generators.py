import math
from typing import Tuple, Dict, Any
from core.contracts.analytics import AnalyticalEvidenceBundle
from core.contracts.decision import DecisionContract
from core.contracts.content import BusinessQuestionContract, EvidenceMetric
from core.validation.exceptions import AnalyticsException

class EvidenceGenerator:
    """Extracts evidence from AnalyticalEvidenceBundle based on keys in BusinessQuestionContract."""
    def generate(self, bundle: AnalyticalEvidenceBundle, contract: BusinessQuestionContract) -> Tuple[Tuple[EvidenceMetric, ...], Tuple[EvidenceMetric, ...]]:
        primary = []
        for key in contract.primary_evidence_keys:
            val, unit = self._extract_metric(bundle, key)
            primary.append(EvidenceMetric(name=key, value=val, unit=unit, is_primary=True))
            
        supporting = []
        for key in contract.supporting_evidence_keys:
            val, unit = self._extract_metric(bundle, key)
            supporting.append(EvidenceMetric(name=key, value=val, unit=unit, is_primary=False))
            
        return tuple(primary), tuple(supporting)
        
    def _extract_metric(self, bundle: AnalyticalEvidenceBundle, key: str) -> Tuple[float, str]:
        if key == "primary_wape" and bundle.primary_evidence:
            return bundle.primary_evidence.accuracy_metrics.global_metrics.global_wape, "%"
        if key == "secondary_wape" and bundle.secondary_evidence:
            return bundle.secondary_evidence.accuracy_metrics.global_metrics.global_wape, "%"
        if key == "p_value" and bundle.primary_evidence and bundle.primary_evidence.statistical_metrics:
            return bundle.primary_evidence.statistical_metrics.global_statistics.global_p_value, "p"
        if key == "hit_rate" and bundle.primary_evidence:
            return bundle.primary_evidence.accuracy_metrics.global_metrics.volume_weighted_hit_rate, "%"
            
        return float('nan'), "N/A"

class ObservationGenerator:
    """Generates observation text using templates."""
    def generate(self, contract: BusinessQuestionContract, primary: Tuple[EvidenceMetric, ...], supporting: Tuple[EvidenceMetric, ...]) -> str:
        context = {m.name: (f"{m.value:.2f}" if not math.isnan(m.value) else "N/A") for m in primary + supporting}
        try:
            return contract.observation_template.format(**context)
        except KeyError as e:
            raise AnalyticsException("CON-001", "CONTENT_ERROR", f"Missing metric for template: {e}", "Ensure evidence keys cover template vars.")

class ConclusionGenerator:
    """Generates conclusion and decision support text."""
    def generate(self, contract: BusinessQuestionContract, primary: Tuple[EvidenceMetric, ...], supporting: Tuple[EvidenceMetric, ...]) -> Tuple[str, str]:
        context = {m.name: (f"{m.value:.2f}" if not math.isnan(m.value) else "N/A") for m in primary + supporting}
        try:
            conclusion = contract.conclusion_template.format(**context)
            decision_support = contract.decision_support_template.format(**context)
            return conclusion, decision_support
        except KeyError as e:
            raise AnalyticsException("CON-001", "CONTENT_ERROR", f"Missing metric for template: {e}", "Ensure evidence keys cover template vars.")

class DecisionProjectionGenerator:
    """Projects the DecisionContract recommendation."""
    def generate(self, decision: DecisionContract, is_suppressed: bool = False) -> Tuple[str, bool]:
        if is_suppressed or decision.decision_state == "NO_DECISION":
            return "NONE", True
            
        if decision.decision_state == "DEPLOY" and decision.deployment_strategy == "GLOBAL":
            return "DEPLOY", False
        if decision.decision_state == "DEPLOY" and decision.deployment_strategy == "PILOT":
            return "PILOT", False
        if decision.decision_state == "RETAIN":
            return "RETAIN", False
            
        return "NONE", True
