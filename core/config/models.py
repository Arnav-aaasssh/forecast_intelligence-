from dataclasses import dataclass
from typing import Tuple
from core.foundation.enums import Environment
from .exceptions import ConfigurationValidationException

@dataclass(frozen=True)
class PlatformConfig:
    platform_version: str
    logging_level: str
    execution_timeout_seconds: int
    retry_policy_max_attempts: int
    schema_version: str

    def __post_init__(self):
        if not isinstance(self.platform_version, str) or not self.platform_version.strip():
            raise ConfigurationValidationException("platform_version must be a non-empty string.")
        if self.logging_level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ConfigurationValidationException("logging_level must be a valid log level (e.g. INFO).")
        if not isinstance(self.execution_timeout_seconds, int) or self.execution_timeout_seconds <= 0:
            raise ConfigurationValidationException("execution_timeout_seconds must be > 0.")
        if not isinstance(self.retry_policy_max_attempts, int) or self.retry_policy_max_attempts < 0:
            raise ConfigurationValidationException("retry_policy_max_attempts must be >= 0.")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ConfigurationValidationException("schema_version must be a non-empty string.")

@dataclass(frozen=True)
class AnalyticsConfig:
    enable_ml_metrics: bool
    winsorization_percentile: float
    coverage_threshold_percent: float
    minimum_sample_size: int
    segmentation_keys: Tuple[str, ...]
    acceptable_tolerance_percentage: float
    zero_actuals_policy: str
    standard_alpha: float
    high_confidence_alpha: float
    practical_improvement_threshold_percent: float
    minimum_statistical_sample_size: int
    minimum_effect_size: float

    def __post_init__(self):
        if not isinstance(self.enable_ml_metrics, bool):
            raise ConfigurationValidationException("enable_ml_metrics must be boolean.")
        if not isinstance(self.winsorization_percentile, float) or not (0.0 <= self.winsorization_percentile <= 1.0):
            raise ConfigurationValidationException("winsorization_percentile must be a float between 0.0 and 1.0.")
        if not isinstance(self.coverage_threshold_percent, float) or not (0.0 <= self.coverage_threshold_percent <= 1.0):
            raise ConfigurationValidationException("coverage_threshold_percent must be a float between 0.0 and 1.0.")
        if not isinstance(self.minimum_sample_size, int) or self.minimum_sample_size < 1:
            raise ConfigurationValidationException("minimum_sample_size must be an int >= 1.")
        if not isinstance(self.segmentation_keys, tuple) or not all(isinstance(k, str) for k in self.segmentation_keys):
            raise ConfigurationValidationException("segmentation_keys must be a tuple of strings.")
        if not isinstance(self.acceptable_tolerance_percentage, float) or not (0.0 <= self.acceptable_tolerance_percentage <= 1.0):
            raise ConfigurationValidationException("acceptable_tolerance_percentage must be a float between 0.0 and 1.0.")
        if self.zero_actuals_policy not in ("RETURN_INFINITY", "RETURN_NAN", "RETURN_ZERO", "RAISE_EXCEPTION", "SUPPRESS_METRIC"):
            raise ConfigurationValidationException("Invalid zero_actuals_policy.")
        if not isinstance(self.standard_alpha, float) or not (0.0 < self.standard_alpha < 1.0):
            raise ConfigurationValidationException("standard_alpha must be a float between 0 and 1.")
        if not isinstance(self.high_confidence_alpha, float) or not (0.0 < self.high_confidence_alpha < 1.0):
            raise ConfigurationValidationException("high_confidence_alpha must be a float between 0 and 1.")
        if not isinstance(self.practical_improvement_threshold_percent, float) or not (0.0 <= self.practical_improvement_threshold_percent <= 1.0):
            raise ConfigurationValidationException("practical_improvement_threshold_percent must be a float between 0 and 1.")
        if not isinstance(self.minimum_statistical_sample_size, int) or self.minimum_statistical_sample_size < 3:
            raise ConfigurationValidationException("minimum_statistical_sample_size must be an int >= 3 (minimum for Wilcoxon).")
        if not isinstance(self.minimum_effect_size, float) or not (0.0 <= self.minimum_effect_size <= 1.0):
            raise ConfigurationValidationException("minimum_effect_size must be a float between 0 and 1.")

@dataclass(frozen=True)
class DecisionPolicyConfig:
    ml_margin_threshold: float
    max_critical_warnings: int
    pilot_qualification_threshold: float
    champion_confidence_required: str
    tie_breaker_strategy: str

    def __post_init__(self):
        if not isinstance(self.ml_margin_threshold, float):
            raise ConfigurationValidationException("ml_margin_threshold must be a float.")
        if not isinstance(self.max_critical_warnings, int) or self.max_critical_warnings < 0:
            raise ConfigurationValidationException("max_critical_warnings must be >= 0.")
        if not isinstance(self.pilot_qualification_threshold, float):
            raise ConfigurationValidationException("pilot_qualification_threshold must be a float.")
        if not isinstance(self.champion_confidence_required, str) or not self.champion_confidence_required.strip():
            raise ConfigurationValidationException("champion_confidence_required must be a non-empty string.")
        if self.tie_breaker_strategy not in ("RECENT_ACCURACY", "HISTORICAL_STABILITY", "MANUAL_REVIEW"):
            raise ConfigurationValidationException("Invalid tie_breaker_strategy.")

@dataclass(frozen=True)
class ContentConfig:
    suppress_empty_sections: bool
    include_appendix: bool
    max_supporting_evidence_items: int

    def __post_init__(self):
        if not isinstance(self.suppress_empty_sections, bool):
            raise ConfigurationValidationException("suppress_empty_sections must be bool.")
        if not isinstance(self.include_appendix, bool):
            raise ConfigurationValidationException("include_appendix must be bool.")
        if not isinstance(self.max_supporting_evidence_items, int) or self.max_supporting_evidence_items < 0:
            raise ConfigurationValidationException("max_supporting_evidence_items must be >= 0.")

@dataclass(frozen=True)
class RendererConfig:
    output_format: str
    page_numbering: bool
    branding_theme: str

    def __post_init__(self):
        if self.output_format not in ("PDF", "JSON", "MARKDOWN"):
            raise ConfigurationValidationException("output_format must be PDF, JSON, or MARKDOWN.")
        if not isinstance(self.page_numbering, bool):
            raise ConfigurationValidationException("page_numbering must be bool.")
        if not isinstance(self.branding_theme, str) or not self.branding_theme.strip():
            raise ConfigurationValidationException("branding_theme must be a non-empty string.")

@dataclass(frozen=True)
class EnvironmentConfig:
    environment: Environment
    debug_mode: bool
    allow_mock_data: bool

    def __post_init__(self):
        if not isinstance(self.environment, Environment):
            raise ConfigurationValidationException("environment must be a valid Environment enum.")
        if not isinstance(self.debug_mode, bool):
            raise ConfigurationValidationException("debug_mode must be bool.")
        if not isinstance(self.allow_mock_data, bool):
            raise ConfigurationValidationException("allow_mock_data must be bool.")

@dataclass(frozen=True)
class EnterpriseConfig:
    """Root configuration object representing the entire platform state."""
    platform: PlatformConfig
    analytics: AnalyticsConfig
    decision: DecisionPolicyConfig
    content: ContentConfig
    renderer: RendererConfig
    environment: EnvironmentConfig

    def __post_init__(self):
        if not isinstance(self.platform, PlatformConfig):
            raise ConfigurationValidationException("platform must be PlatformConfig.")
        if not isinstance(self.analytics, AnalyticsConfig):
            raise ConfigurationValidationException("analytics must be AnalyticsConfig.")
        if not isinstance(self.decision, DecisionPolicyConfig):
            raise ConfigurationValidationException("decision must be DecisionPolicyConfig.")
        if not isinstance(self.content, ContentConfig):
            raise ConfigurationValidationException("content must be ContentConfig.")
        if not isinstance(self.renderer, RendererConfig):
            raise ConfigurationValidationException("renderer must be RendererConfig.")
        if not isinstance(self.environment, EnvironmentConfig):
            raise ConfigurationValidationException("environment must be EnvironmentConfig.")
