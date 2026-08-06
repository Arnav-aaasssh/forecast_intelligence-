from abc import ABC, abstractmethod
import math

from core.contracts.analytics import AnalyticalEvidenceBundle
from core.contracts.decision import PolicyEvaluation
from core.config.models import DecisionPolicyConfig

class PolicyEvaluator(ABC):
    @property
    @abstractmethod
    def policy_name(self) -> str:
        pass
        
    @abstractmethod
    def evaluate(self, bundle: AnalyticalEvidenceBundle, config: DecisionPolicyConfig) -> PolicyEvaluation:
        pass

class MLSuperiorityPolicy(PolicyEvaluator):
    """
    Evaluates whether the primary model is superior to the baseline (secondary model)
    by a margin greater than or equal to the ml_margin_threshold.
    """
    @property
    def policy_name(self) -> str:
        return "ML_SUPERIORITY_POLICY"
        
    def evaluate(self, bundle: AnalyticalEvidenceBundle, config: DecisionPolicyConfig) -> PolicyEvaluation:
        if not bundle.secondary_evidence:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="NOT_APPLICABLE",
                reason_code="NOT_APPLICABLE_GREENFIELD",
                evaluated_metric_value=0.0,
                applied_threshold=config.ml_margin_threshold
            )
        
        primary_wape = bundle.primary_evidence.accuracy_metrics.global_metrics.global_wape
        secondary_wape = bundle.secondary_evidence.accuracy_metrics.global_metrics.global_wape
        
        if math.isnan(primary_wape) or math.isnan(secondary_wape):
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="NOT_APPLICABLE",
                reason_code="NOT_APPLICABLE_NONFINITE",
                evaluated_metric_value=float('nan'),
                applied_threshold=config.ml_margin_threshold
            )
            
        # Absolute difference (secondary_wape - primary_wape) 
        # A positive difference means primary is better (lower WAPE)
        diff = secondary_wape - primary_wape
        
        if diff >= config.ml_margin_threshold:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="PASS",
                reason_code="PASSED",
                evaluated_metric_value=diff,
                applied_threshold=config.ml_margin_threshold
            )
        else:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="FAIL",
                reason_code="FAILED_MARGIN",
                evaluated_metric_value=diff,
                applied_threshold=config.ml_margin_threshold
            )

class ConfidencePolicy(PolicyEvaluator):
    """
    Evaluates whether the primary model's statistical improvement has the required
    confidence level to be trusted.
    """
    @property
    def policy_name(self) -> str:
        return "CONFIDENCE_POLICY"
        
    def evaluate(self, bundle: AnalyticalEvidenceBundle, config: DecisionPolicyConfig) -> PolicyEvaluation:
        stat_metrics = bundle.primary_evidence.statistical_metrics
        if not stat_metrics:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="NOT_APPLICABLE",
                reason_code="NOT_APPLICABLE_NO_STATS",
                evaluated_metric_value=0.0,
                applied_threshold=0.0
            )
            
        global_stats = stat_metrics.global_statistics
        
        if global_stats.global_confidence_level == "SUPPRESSED":
             return PolicyEvaluation(
                policy_name=self.policy_name,
                status="SUPPRESSED",
                reason_code="SUPPRESSED_STATS",
                evaluated_metric_value=global_stats.global_p_value,
                applied_threshold=0.0
            )
            
        # A simple string match on the required confidence level (e.g., HIGH == HIGH)
        if global_stats.global_confidence_level == config.champion_confidence_required:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="PASS",
                reason_code="PASSED",
                evaluated_metric_value=global_stats.global_p_value,
                applied_threshold=0.0 
            )
        else:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="FAIL",
                reason_code="FAILED_CONFIDENCE",
                evaluated_metric_value=global_stats.global_p_value,
                applied_threshold=0.0
            )

class CoveragePolicy(PolicyEvaluator):
    """
    Evaluates whether the primary model's prediction coverage across all segments
    meets the required threshold, reducing localized segment risk.
    """
    @property
    def policy_name(self) -> str:
        return "COVERAGE_POLICY"
        
    def evaluate(self, bundle: AnalyticalEvidenceBundle, config: DecisionPolicyConfig) -> PolicyEvaluation:
        hit_rate = bundle.primary_evidence.accuracy_metrics.global_metrics.volume_weighted_hit_rate
        
        if math.isnan(hit_rate):
             return PolicyEvaluation(
                policy_name=self.policy_name,
                status="NOT_APPLICABLE",
                reason_code="NOT_APPLICABLE_NONFINITE",
                evaluated_metric_value=float('nan'),
                applied_threshold=config.pilot_qualification_threshold
            )
            
        if hit_rate >= config.pilot_qualification_threshold:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="PASS",
                reason_code="PASSED",
                evaluated_metric_value=hit_rate,
                applied_threshold=config.pilot_qualification_threshold
            )
        else:
            return PolicyEvaluation(
                policy_name=self.policy_name,
                status="FAIL",
                reason_code="FAILED_COVERAGE",
                evaluated_metric_value=hit_rate,
                applied_threshold=config.pilot_qualification_threshold
            )
