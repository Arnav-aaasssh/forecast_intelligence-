from dataclasses import dataclass
from typing import Tuple, Optional
from datetime import datetime
import math
import uuid
from core.foundation.execution_context import ExecutionContext
from core.contracts.dataset import DatasetReference, WindowMetadata
from .exceptions import ContractValidationException

@dataclass(frozen=True)
class AnalyticsResult:
    """
    Represents the complete deterministic output of the Analytics Engine.
    Must not contain business policies, recommendations, or narrative text.
    """
    execution_context: ExecutionContext
    run_hash: str
    global_wape: float
    global_bias: float
    segment_metrics: Tuple[Tuple[str, float, float], ...]  # Tuple of (Segment Name, WAPE, Bias)
    model_rankings: Tuple[str, ...]
    warnings: Tuple[str, ...]
    
    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.run_hash, str) or not self.run_hash.strip():
            raise ContractValidationException("run_hash must be a non-empty string.")
        if not isinstance(self.global_wape, float):
            raise ContractValidationException("global_wape must be a float.")
        if not isinstance(self.global_bias, float):
            raise ContractValidationException("global_bias must be a float.")
        if not isinstance(self.segment_metrics, tuple):
            raise ContractValidationException("segment_metrics must be a tuple of tuples.")
        for item in self.segment_metrics:
            if not isinstance(item, tuple) or len(item) != 3:
                raise ContractValidationException("Each segment_metric must be a tuple of (str, float, float).")
        if not isinstance(self.model_rankings, tuple):
            raise ContractValidationException("model_rankings must be a tuple of strings.")
        if not isinstance(self.warnings, tuple):
            raise ContractValidationException("warnings must be a tuple of strings.")

@dataclass(frozen=True)
class MetricMetadata:
    engine_version: str
    calculation_timestamp: datetime
    zero_actuals_policy_applied: str
    acceptable_tolerance_applied: float

    def __post_init__(self):
        if not isinstance(self.engine_version, str) or not self.engine_version.strip():
            raise ContractValidationException("engine_version must be a non-empty string.")
        if not isinstance(self.calculation_timestamp, datetime):
            raise ContractValidationException("calculation_timestamp must be a datetime.")
        if not isinstance(self.zero_actuals_policy_applied, str) or not self.zero_actuals_policy_applied.strip():
            raise ContractValidationException("zero_actuals_policy_applied must be a non-empty string.")
        if not isinstance(self.acceptable_tolerance_applied, float) or not (0.0 <= self.acceptable_tolerance_applied <= 1.0):
            raise ContractValidationException("acceptable_tolerance_applied must be a float between 0.0 and 1.0.")

@dataclass(frozen=True)
class SegmentAccuracyMetrics:
    segment_id: str
    observation_count: int
    wape: float
    bias: float
    mae: float
    rmse: float
    hit_rate: float

    def __post_init__(self):
        if not isinstance(self.segment_id, str) or not self.segment_id.strip():
            raise ContractValidationException("segment_id must be a non-empty string.")
        if not isinstance(self.observation_count, int) or self.observation_count < 1:
            raise ContractValidationException("observation_count must be an int >= 1.")
        
        # Validations for metrics (non-finite values are legally permitted due to zero-actuals policy)
        if not isinstance(self.wape, float):
            raise ContractValidationException("wape must be a float.")
        if not isinstance(self.bias, float):
            raise ContractValidationException("bias must be a float.")
        if not isinstance(self.mae, float):
            raise ContractValidationException("mae must be a float.")
        if not isinstance(self.rmse, float):
            raise ContractValidationException("rmse must be a float.")
        if not isinstance(self.hit_rate, float):
            raise ContractValidationException("hit_rate must be a float.")

        if not math.isnan(self.wape) and self.wape < 0.0:
            raise ContractValidationException("wape cannot be negative.")
        if not math.isnan(self.mae) and self.mae < 0.0:
            raise ContractValidationException("mae cannot be negative.")
        if not math.isnan(self.rmse) and self.rmse < 0.0:
            raise ContractValidationException("rmse cannot be negative.")
        if not math.isnan(self.hit_rate) and not (0.0 <= self.hit_rate <= 1.0):
            raise ContractValidationException("hit_rate must be between 0.0 and 1.0.")

@dataclass(frozen=True)
class GlobalAccuracyMetrics:
    total_observation_count: int
    global_wape: float
    global_bias: float
    volume_weighted_mae: float
    volume_weighted_rmse: float
    volume_weighted_hit_rate: float

    def __post_init__(self):
        if not isinstance(self.total_observation_count, int) or self.total_observation_count < 1:
            raise ContractValidationException("total_observation_count must be an int >= 1.")
            
        if not isinstance(self.global_wape, float):
            raise ContractValidationException("global_wape must be a float.")
        if not isinstance(self.global_bias, float):
            raise ContractValidationException("global_bias must be a float.")
        if not isinstance(self.volume_weighted_mae, float):
            raise ContractValidationException("volume_weighted_mae must be a float.")
        if not isinstance(self.volume_weighted_rmse, float):
            raise ContractValidationException("volume_weighted_rmse must be a float.")
        if not isinstance(self.volume_weighted_hit_rate, float):
            raise ContractValidationException("volume_weighted_hit_rate must be a float.")

        if not math.isnan(self.global_wape) and self.global_wape < 0.0:
            raise ContractValidationException("global_wape cannot be negative.")
        if not math.isnan(self.volume_weighted_mae) and self.volume_weighted_mae < 0.0:
            raise ContractValidationException("volume_weighted_mae cannot be negative.")
        if not math.isnan(self.volume_weighted_rmse) and self.volume_weighted_rmse < 0.0:
            raise ContractValidationException("volume_weighted_rmse cannot be negative.")
        if not math.isnan(self.volume_weighted_hit_rate) and not (0.0 <= self.volume_weighted_hit_rate <= 1.0):
            raise ContractValidationException("volume_weighted_hit_rate must be between 0.0 and 1.0.")

@dataclass(frozen=True)
class ForecastAccuracyResult:
    execution_context: ExecutionContext
    prepared_dataset_reference: DatasetReference
    evaluation_window: WindowMetadata
    metric_metadata: MetricMetadata
    segment_metrics: Tuple[SegmentAccuracyMetrics, ...]
    global_metrics: GlobalAccuracyMetrics

    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.prepared_dataset_reference, DatasetReference):
            raise ContractValidationException("prepared_dataset_reference must be a DatasetReference.")
        if not isinstance(self.evaluation_window, WindowMetadata):
            raise ContractValidationException("evaluation_window must be a WindowMetadata.")
        if not isinstance(self.metric_metadata, MetricMetadata):
            raise ContractValidationException("metric_metadata must be a MetricMetadata.")
        if not isinstance(self.segment_metrics, tuple):
            raise ContractValidationException("segment_metrics must be a tuple.")
        if not isinstance(self.global_metrics, GlobalAccuracyMetrics):
            raise ContractValidationException("global_metrics must be a GlobalAccuracyMetrics.")

@dataclass(frozen=True)
class SegmentStatisticalMetrics:
    segment_id: str
    paired_observation_count: int
    p_value: float
    effect_size: float
    is_practically_significant: bool
    confidence_level: str  # HIGH, MEDIUM, LOW, INSUFFICIENT, SUPPRESSED
    suppression_reason: Optional[str]

    def __post_init__(self):
        if not isinstance(self.segment_id, str) or not self.segment_id.strip():
            raise ContractValidationException("segment_id must be a non-empty string.")
        if not isinstance(self.paired_observation_count, int) or self.paired_observation_count < 0:
            raise ContractValidationException("paired_observation_count must be a non-negative int.")
        if not isinstance(self.p_value, float):
            raise ContractValidationException("p_value must be a float.")
        if not math.isnan(self.p_value) and not (0.0 <= self.p_value <= 1.0):
            raise ContractValidationException("p_value must be between 0.0 and 1.0.")
        if not isinstance(self.effect_size, float):
            raise ContractValidationException("effect_size must be a float.")
        if not isinstance(self.is_practically_significant, bool):
            raise ContractValidationException("is_practically_significant must be a boolean.")
        if self.confidence_level not in ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT", "SUPPRESSED"):
            raise ContractValidationException("Invalid confidence_level.")

@dataclass(frozen=True)
class GlobalStatisticalMetrics:
    total_paired_observations: int
    global_p_value: float
    global_effect_size: float
    is_practically_significant: bool
    global_confidence_level: str
    
    def __post_init__(self):
        if not isinstance(self.total_paired_observations, int) or self.total_paired_observations < 0:
            raise ContractValidationException("total_paired_observations must be a non-negative int.")
        if not isinstance(self.global_p_value, float):
            raise ContractValidationException("global_p_value must be a float.")
        if not math.isnan(self.global_p_value) and not (0.0 <= self.global_p_value <= 1.0):
            raise ContractValidationException("global_p_value must be between 0.0 and 1.0.")
        if not isinstance(self.global_effect_size, float):
            raise ContractValidationException("global_effect_size must be a float.")
        if not isinstance(self.is_practically_significant, bool):
            raise ContractValidationException("is_practically_significant must be a boolean.")
        if self.global_confidence_level not in ("HIGH", "MEDIUM", "LOW", "INSUFFICIENT", "SUPPRESSED"):
            raise ContractValidationException("Invalid global_confidence_level.")

@dataclass(frozen=True)
class StatisticalAnalyticsResult:
    execution_context: ExecutionContext
    primary_dataset_reference: DatasetReference
    secondary_dataset_reference: DatasetReference
    segment_statistics: Tuple[SegmentStatisticalMetrics, ...]
    global_statistics: GlobalStatisticalMetrics
    warnings: Tuple[str, ...]

    def __post_init__(self):
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.primary_dataset_reference, DatasetReference):
            raise ContractValidationException("primary_dataset_reference must be a valid DatasetReference.")
        if not isinstance(self.secondary_dataset_reference, DatasetReference):
            raise ContractValidationException("secondary_dataset_reference must be a valid DatasetReference.")
        if not isinstance(self.segment_statistics, tuple):
            raise ContractValidationException("segment_statistics must be a tuple.")
        if not isinstance(self.global_statistics, GlobalStatisticalMetrics):
            raise ContractValidationException("global_statistics must be a GlobalStatisticalMetrics.")
        if not isinstance(self.warnings, tuple):
            raise ContractValidationException("warnings must be a tuple.")

@dataclass(frozen=True)
class ModelEvidence:
    model_identifier: str
    is_primary: bool
    accuracy_metrics: ForecastAccuracyResult
    statistical_metrics: Optional[StatisticalAnalyticsResult]

    def __post_init__(self):
        if not isinstance(self.model_identifier, str) or not self.model_identifier.strip():
            raise ContractValidationException("model_identifier must be a non-empty string.")
        if not isinstance(self.is_primary, bool):
            raise ContractValidationException("is_primary must be a boolean.")
        if not isinstance(self.accuracy_metrics, ForecastAccuracyResult):
            raise ContractValidationException("accuracy_metrics must be a ForecastAccuracyResult.")
        if self.statistical_metrics is not None and not isinstance(self.statistical_metrics, StatisticalAnalyticsResult):
            raise ContractValidationException("statistical_metrics must be a StatisticalAnalyticsResult or None.")

@dataclass(frozen=True)
class AnalyticalEvidenceBundle:
    primary_evidence: ModelEvidence
    secondary_evidence: Optional[ModelEvidence]
    execution_context: ExecutionContext
    traceability_id: uuid.UUID
    consolidation_timestamp: datetime

    def __post_init__(self):
        if not isinstance(self.primary_evidence, ModelEvidence):
            raise ContractValidationException("primary_evidence must be a valid ModelEvidence.")
        if not self.primary_evidence.is_primary:
            raise ContractValidationException("primary_evidence must have is_primary=True.")
        
        if self.secondary_evidence is not None:
            if not isinstance(self.secondary_evidence, ModelEvidence):
                raise ContractValidationException("secondary_evidence must be a valid ModelEvidence.")
            if self.secondary_evidence.is_primary:
                raise ContractValidationException("secondary_evidence must have is_primary=False.")
                
        if not isinstance(self.execution_context, ExecutionContext):
            raise ContractValidationException("execution_context must be a valid ExecutionContext.")
        if not isinstance(self.traceability_id, uuid.UUID):
            raise ContractValidationException("traceability_id must be a valid uuid.UUID.")
        if not isinstance(self.consolidation_timestamp, datetime):
            raise ContractValidationException("consolidation_timestamp must be a valid datetime.")

