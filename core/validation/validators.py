import uuid
import re
from typing import Any, Tuple
from datetime import datetime
from enum import Enum

class BaseValidator:
    """Stateless base validator."""
    def validate(self, value: Any) -> Tuple[bool, str]:
        raise NotImplementedError

class UUIDValidator(BaseValidator):
    def validate(self, value: Any) -> Tuple[bool, str]:
        if isinstance(value, uuid.UUID):
            return True, ""
        try:
            uuid.UUID(str(value))
            return True, ""
        except (ValueError, TypeError, AttributeError):
            return False, f"Value '{value}' is not a valid UUID."

class VersionValidator(BaseValidator):
    def validate(self, value: Any) -> Tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Version must be a string."
        if not re.match(r"^\d+\.\d+(\.\d+)?$", value):
            return False, "Version must follow semantic format (e.g. 1.0 or 1.0.0)."
        return True, ""

class RangeValidator(BaseValidator):
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val
        
    def validate(self, value: Any) -> Tuple[bool, str]:
        if not isinstance(value, (int, float)):
            return False, "Value must be numeric."
        if not (self.min_val <= value <= self.max_val):
            return False, f"Value must be between {self.min_val} and {self.max_val}."
        return True, ""

class StringValidator(BaseValidator):
    def __init__(self, allow_empty: bool = False):
        self.allow_empty = allow_empty
        
    def validate(self, value: Any) -> Tuple[bool, str]:
        if not isinstance(value, str):
            return False, "Value must be a string."
        if not self.allow_empty and not value.strip():
            return False, "String cannot be empty."
        return True, ""

class EnumValidator(BaseValidator):
    def __init__(self, enum_class: Type[Enum]):
        self.enum_class = enum_class
        
    def validate(self, value: Any) -> Tuple[bool, str]:
        if not isinstance(value, self.enum_class):
            return False, f"Value must be a member of enum {self.enum_class.__name__}."
        return True, ""

class DateTimeValidator(BaseValidator):
    def validate(self, value: Any) -> Tuple[bool, str]:
        if not isinstance(value, datetime):
            return False, "Value must be a valid datetime object."
        return True, ""

class CollectionValidator(BaseValidator):
    def __init__(self, item_validator: BaseValidator):
        self.item_validator = item_validator
        
    def validate(self, value: Any) -> Tuple[bool, str]:
        if not isinstance(value, (tuple, list, set)):
            return False, "Value must be a collection (tuple, list, set)."
        for idx, item in enumerate(value):
            is_valid, msg = self.item_validator.validate(item)
            if not is_valid:
                return False, f"Item at index {idx} failed: {msg}"
        return True, ""
