from core.foundation.exceptions import FoundationException

class ConfigurationException(FoundationException):
    """Base exception for all configuration errors."""
    pass

class ConfigurationValidationException(ConfigurationException):
    """Raised when configuration values are invalid or out of bounds."""
    pass

class ConfigurationLoadException(ConfigurationException):
    """Raised when configuration files cannot be found or parsed."""
    pass
