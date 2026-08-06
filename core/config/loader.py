import json
import os
from typing import Dict, Any

from .models import (
    PlatformConfig, AnalyticsConfig, DecisionPolicyConfig, 
    ContentConfig, RendererConfig, EnvironmentConfig, EnterpriseConfig
)
from .exceptions import ConfigurationLoadException
from core.foundation.enums import Environment

class ConfigurationLoader:
    """Loads and validates deterministic enterprise configuration."""

    @staticmethod
    def load_from_dict(data: Dict[str, Any], env: Environment) -> EnterpriseConfig:
        try:
            platform = PlatformConfig(**data.get("platform", {}))
            analytics_data = data.get("analytics", {})
            if "segmentation_keys" in analytics_data and isinstance(analytics_data["segmentation_keys"], list):
                analytics_data["segmentation_keys"] = tuple(analytics_data["segmentation_keys"])
            analytics = AnalyticsConfig(**analytics_data)
            decision = DecisionPolicyConfig(**data.get("decision", {}))
            content = ContentConfig(**data.get("content", {}))
            renderer = RendererConfig(**data.get("renderer", {}))
            
            env_data = data.get("environment", {})
            debug = env_data.get("debug_mode", False)
            mock = env_data.get("allow_mock_data", False)
            environment = EnvironmentConfig(environment=env, debug_mode=debug, allow_mock_data=mock)
            
            return EnterpriseConfig(
                platform=platform,
                analytics=analytics,
                decision=decision,
                content=content,
                renderer=renderer,
                environment=environment
            )
        except Exception as e:
            raise ConfigurationLoadException(f"Configuration resolution failed: {str(e)}")

    @staticmethod
    def load_from_file(filepath: str, env: Environment) -> EnterpriseConfig:
        if not os.path.exists(filepath):
            raise ConfigurationLoadException(f"Configuration file not found: {filepath}")
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            return ConfigurationLoader.load_from_dict(data, env)
        except json.JSONDecodeError as e:
            raise ConfigurationLoadException(f"Invalid JSON format in {filepath}: {str(e)}")
