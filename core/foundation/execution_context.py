import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from .enums import Environment, ExecutionMode
from .exceptions import ContextValidationException

@dataclass(frozen=True)
class ExecutionContext:
    """
    Immutable root runtime object that accompanies every execution through the platform.
    Owns runtime metadata only. Contains zero business logic.
    """
    run_id: uuid.UUID
    correlation_id: str
    execution_timestamp: datetime
    platform_version: str
    environment: Environment
    execution_mode: ExecutionMode
    user_id: str
    request_source: str
    config_versions: Tuple[Tuple[str, str], ...]

    traceability_id: uuid.UUID
    job_id: Optional[str] = None

    def __post_init__(self):
        if not isinstance(self.run_id, uuid.UUID):
            raise ContextValidationException("run_id must be a valid uuid.UUID instance.")
        
        if not isinstance(self.traceability_id, uuid.UUID):
            raise ContextValidationException("traceability_id must be a valid uuid.UUID instance.")
            
        if not isinstance(self.correlation_id, str) or not self.correlation_id.strip():
            raise ContextValidationException("correlation_id must be a non-empty string.")
            
        if not isinstance(self.execution_timestamp, datetime):
            raise ContextValidationException("execution_timestamp must be a valid datetime object.")
            
        if not isinstance(self.environment, Environment):
            raise ContextValidationException("environment must be a valid Environment enum.")
            
        if not isinstance(self.execution_mode, ExecutionMode):
            raise ContextValidationException("execution_mode must be a valid ExecutionMode enum.")
            
        if not isinstance(self.platform_version, str) or not self.platform_version.strip():
            raise ContextValidationException("platform_version must be a non-empty string.")
            
        if not isinstance(self.user_id, str) or not self.user_id.strip():
            raise ContextValidationException("user_id must be a non-empty string.")
            
        if not isinstance(self.request_source, str) or not self.request_source.strip():
            raise ContextValidationException("request_source must be a non-empty string.")
            
        if not isinstance(self.config_versions, tuple):
            raise ContextValidationException("config_versions must be a tuple of string tuples.")
            
        if self.job_id is not None and not isinstance(self.job_id, str):
            raise ContextValidationException("job_id must be a string or None.")
