"""Domain exceptions used by forecast dataset validation services."""


class ValidationRuntimeError(RuntimeError):
    """Raised when validation stops because of an unexpected runtime failure."""


class DatasetLoadError(ValidationRuntimeError):
    """Raised by ingestion code when a dataset cannot be loaded."""


class ConfigurationError(RuntimeError):
    """Raised when application configuration is missing or invalid."""


class ReportGenerationError(RuntimeError):
    """Raised when generating a report artifact fails."""

class LLMProviderError(RuntimeError):
    """Raised when the LLM provider fails to generate a response."""
