class FoundationException(Exception):
    """Base exception for all Foundation layer errors."""
    pass

class ContextValidationException(FoundationException):
    """Raised when ExecutionContext validation fails."""
    pass
