import pytest
import uuid
from datetime import datetime
from enum import Enum
import dataclasses

from core.validation.exceptions import PlatformException, ValidationException
from core.validation.models import ValidationResult, ValidationError
from core.validation.validators import (
    UUIDValidator, VersionValidator, RangeValidator, 
    StringValidator, EnumValidator, DateTimeValidator, CollectionValidator
)
from core.validation.registry import ValidationRegistry

class StatusEnum(Enum):
    OK = "OK"
    FAIL = "FAIL"

def test_uuid_validator():
    val = UUIDValidator()
    assert val.validate(uuid.uuid4())[0] == True
    assert val.validate(str(uuid.uuid4()))[0] == True
    
    is_valid, msg = val.validate("not-a-uuid")
    assert is_valid == False
    assert "not a valid UUID" in msg

def test_version_validator():
    val = VersionValidator()
    assert val.validate("1.0")[0] == True
    assert val.validate("2.4.1")[0] == True
    
    is_valid, msg = val.validate("v1.0")
    assert is_valid == False
    assert "semantic format" in msg

def test_range_validator():
    val = RangeValidator(0.0, 1.0)
    assert val.validate(0.5)[0] == True
    assert val.validate(0.0)[0] == True
    assert val.validate(1.0)[0] == True
    
    is_valid, msg = val.validate(1.5)
    assert is_valid == False
    
    is_valid, msg = val.validate("string")
    assert is_valid == False

def test_string_validator():
    val = StringValidator(allow_empty=False)
    assert val.validate("hello")[0] == True
    assert val.validate("   ")[0] == False
    
    val2 = StringValidator(allow_empty=True)
    assert val2.validate("   ")[0] == True
    assert val2.validate(123)[0] == False

def test_enum_validator():
    val = EnumValidator(StatusEnum)
    assert val.validate(StatusEnum.OK)[0] == True
    assert val.validate("OK")[0] == False

def test_datetime_validator():
    val = DateTimeValidator()
    assert val.validate(datetime.now())[0] == True
    assert val.validate("2026-01-01")[0] == False

def test_collection_validator():
    val = CollectionValidator(StringValidator())
    assert val.validate(("a", "b", "c"))[0] == True
    
    is_valid, msg = val.validate(("a", 123, "c"))
    assert is_valid == False
    assert "Item at index 1 failed" in msg

def test_validation_registry():
    registry = ValidationRegistry()
    registry.register("uuid", UUIDValidator())
    registry.register("version", VersionValidator())
    
    data = {
        "id": uuid.uuid4(),
        "ver": "1.2.3"
    }
    
    result = registry.validate_object(data, {"id": "uuid", "ver": "version"}, traceability_id="trace-123")
    assert result.passed == True
    assert len(result.errors) == 0
    assert result.traceability_id == "trace-123"

def test_validation_registry_failures():
    registry = ValidationRegistry()
    registry.register("uuid", UUIDValidator())
    
    data = {"id": "invalid-uuid"}
    result = registry.validate_object(data, {"id": "uuid"})
    
    assert result.passed == False
    assert len(result.errors) == 1
    assert result.errors[0].field_name == "id"
    assert result.errors[0].validator_name == "uuid"

def test_unregistered_validator():
    registry = ValidationRegistry()
    data = {"id": "123"}
    
    result = registry.validate_object(data, {"id": "missing_validator"})
    assert result.passed == False
    assert len(result.errors) == 1
    assert "not found" in result.errors[0].error_message

def test_platform_exception():
    exc = PlatformException(
        error_code="ERR-001",
        category="TestCategory",
        message="A testing error occurred",
        suggested_resolution="Fix the test.",
        traceability_id="trace-99"
    )
    assert exc.error_code == "ERR-001"
    assert "TestCategory: A testing error occurred" in str(exc)

def test_invalid_registry_register():
    registry = ValidationRegistry()
    with pytest.raises(TypeError):
        registry.register("bad", "not-a-validator")

def test_immutability():
    err = ValidationError(validator_name="uuid", error_message="bad")
    with pytest.raises(dataclasses.FrozenInstanceError):
        err.error_message = "new"
