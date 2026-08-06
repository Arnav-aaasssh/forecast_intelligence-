from typing import Optional

class PlatformException(Exception):
    """
    Root exception for all enterprise platform errors.
    Requires deterministic traceability fields.
    """
    def __init__(
        self, 
        error_code: str, 
        category: str, 
        message: str, 
        suggested_resolution: str, 
        root_cause: Optional[str] = None, 
        execution_context_id: Optional[str] = None, 
        traceability_id: Optional[str] = None
    ):
        self.error_code = error_code
        self.category = category
        self.message = message
        self.suggested_resolution = suggested_resolution
        self.root_cause = root_cause
        self.execution_context_id = execution_context_id
        self.traceability_id = traceability_id
        super().__init__(f"[{error_code}] {category}: {message}")

class ValidationException(PlatformException): pass
class ConfigurationException(PlatformException): pass
class ContractValidationException(PlatformException): pass
class DatasetValidationException(PlatformException): pass
class AnalyticsException(PlatformException): pass
class DecisionEngineException(PlatformException): pass
class ContentEngineException(PlatformException): pass
class RendererException(PlatformException): pass
class OrchestratorException(PlatformException): pass
class SerializationException(PlatformException): pass
class VersionCompatibilityException(PlatformException): pass
