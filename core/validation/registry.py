import time
from typing import Dict, Any, List

from .validators import BaseValidator
from .models import ValidationResult, ValidationError
from .exceptions import ValidationException

class ValidationRegistry:
    """Central registry for reusable, stateless validators."""
    
    def __init__(self):
        self._validators: Dict[str, BaseValidator] = {}
        
    def register(self, name: str, validator: BaseValidator):
        """Register a validator instance."""
        if not isinstance(validator, BaseValidator):
            raise TypeError("Validator must inherit from BaseValidator.")
        self._validators[name] = validator
        
    def get_validator(self, name: str) -> BaseValidator:
        val = self._validators.get(name)
        if not val:
            raise ValidationException(
                error_code="VAL-001",
                category="Configuration",
                message=f"Validator '{name}' not found.",
                suggested_resolution="Ensure validator is registered before execution."
            )
        return val

    def validate_object(self, target: Any, validations: Dict[str, str], traceability_id: str = None) -> ValidationResult:
        """
        Executes registered validators against target attributes or dictionary keys.
        validations format: {"field_name": "validator_name"}
        """
        start = time.time()
        errors: List[ValidationError] = []
        
        for field, v_name in validations.items():
            try:
                val = self.get_validator(v_name)
            except ValidationException as e:
                errors.append(ValidationError(v_name, e.message, field))
                continue
                
            # Extract value from object attribute or dict key
            if isinstance(target, dict):
                value = target.get(field)
            else:
                value = getattr(target, field, None)
                
            is_valid, msg = val.validate(value)
            if not is_valid:
                errors.append(ValidationError(v_name, msg, field))
                
        execution_time_ms = (time.time() - start) * 1000
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=tuple(errors),
            warnings=(),
            execution_time_ms=execution_time_ms,
            traceability_id=traceability_id
        )
