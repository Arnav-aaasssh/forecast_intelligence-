from dataclasses import dataclass
from typing import Tuple, Optional
from core.foundation.execution_context import ExecutionContext

@dataclass(frozen=True)
class ValidationError:
    validator_name: str
    error_message: str
    field_name: Optional[str] = None

@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: Tuple[ValidationError, ...]
    warnings: Tuple[str, ...]
    execution_time_ms: float
    traceability_id: Optional[str] = None
    execution_context_ref: Optional[str] = None
