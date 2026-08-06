import pytest
import os
import json
import dataclasses
from core.foundation.enums import Environment
from core.config.exceptions import ConfigurationValidationException, ConfigurationLoadException
from core.config.loader import ConfigurationLoader
from core.config.models import (
    PlatformConfig, AnalyticsConfig, DecisionPolicyConfig,
    ContentConfig, RendererConfig, EnvironmentConfig, EnterpriseConfig
)

def get_valid_dict():
    return {
        "platform": {
            "platform_version": "1.2.0",
            "logging_level": "INFO",
            "execution_timeout_seconds": 300,
            "retry_policy_max_attempts": 3,
            "schema_version": "1.0"
        },
        "analytics": {
            "enable_ml_metrics": True,
            "winsorization_percentile": 0.95,
            "coverage_threshold_percent": 0.8,
            "minimum_sample_size": 12,
            "segmentation_keys": ["forecast_name", "region"],
            "acceptable_tolerance_percentage": 0.10,
            "zero_actuals_policy": "RETURN_INFINITY",
            "standard_alpha": 0.05,
            "high_confidence_alpha": 0.01,
            "practical_improvement_threshold_percent": 0.05,
            "minimum_statistical_sample_size": 5,
            "minimum_effect_size": 0.1
        },
        "decision": {
            "ml_margin_threshold": 0.05,
            "max_critical_warnings": 2,
            "pilot_qualification_threshold": 0.85,
            "champion_confidence_required": "HIGH",
            "tie_breaker_strategy": "RECENT_ACCURACY"
        },
        "content": {
            "suppress_empty_sections": True,
            "include_appendix": True,
            "max_supporting_evidence_items": 5
        },
        "renderer": {
            "output_format": "PDF",
            "page_numbering": True,
            "branding_theme": "ENTERPRISE_DARK"
        },
        "environment": {
            "debug_mode": False,
            "allow_mock_data": False
        }
    }

def test_valid_configuration_load():
    data = get_valid_dict()
    config = ConfigurationLoader.load_from_dict(data, Environment.PROD)
    
    assert config.platform.logging_level == "INFO"
    assert config.analytics.winsorization_percentile == 0.95
    assert config.decision.tie_breaker_strategy == "RECENT_ACCURACY"
    assert config.environment.environment == Environment.PROD

def test_missing_key_raises_exception():
    data = get_valid_dict()
    del data["platform"]["execution_timeout_seconds"]
    
    with pytest.raises(ConfigurationLoadException, match="missing 1 required positional argument"):
        ConfigurationLoader.load_from_dict(data, Environment.PROD)

def test_invalid_range_raises_exception():
    data = get_valid_dict()
    data["analytics"]["winsorization_percentile"] = 1.5 # Invalid float range
    
    with pytest.raises(ConfigurationLoadException, match="winsorization_percentile must be a float between 0.0 and 1.0"):
        ConfigurationLoader.load_from_dict(data, Environment.PROD)

def test_invalid_enum_raises_exception():
    data = get_valid_dict()
    data["platform"]["logging_level"] = "MAGIC"
    
    with pytest.raises(ConfigurationLoadException, match="logging_level must be a valid log level"):
        ConfigurationLoader.load_from_dict(data, Environment.PROD)

def test_immutability():
    data = get_valid_dict()
    config = ConfigurationLoader.load_from_dict(data, Environment.PROD)
    
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.platform.logging_level = "DEBUG"

def test_load_from_file(tmp_path):
    data = get_valid_dict()
    file_path = tmp_path / "config.json"
    file_path.write_text(json.dumps(data))
    
    config = ConfigurationLoader.load_from_file(str(file_path), Environment.DEV)
    assert config.environment.environment == Environment.DEV

def test_load_from_missing_file():
    with pytest.raises(ConfigurationLoadException, match="Configuration file not found"):
        ConfigurationLoader.load_from_file("does_not_exist.json", Environment.DEV)
