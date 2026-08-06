import uuid
from datetime import datetime
import pytest

from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment, ExecutionMode
from core.foundation.exceptions import ContextValidationException

def test_valid_execution_context():
    ctx = ExecutionContext(
        run_id=uuid.uuid4(),
        correlation_id="corr-123",
        execution_timestamp=datetime.now(),
        platform_version="1.0.0",
        environment=Environment.PROD,
        execution_mode=ExecutionMode.API,
        user_id="user_admin",
        request_source="postman",
        config_versions=(("decision", "v1"),),
        traceability_id=uuid.uuid4()
    )
    assert ctx.correlation_id == "corr-123"

def test_invalid_uuid():
    with pytest.raises(ContextValidationException, match="run_id must be a valid uuid.UUID instance."):
        ExecutionContext(
            run_id="not-a-uuid",
            correlation_id="corr-123",
            execution_timestamp=datetime.now(),
            platform_version="1.0.0",
            environment=Environment.PROD,
            execution_mode=ExecutionMode.API,
            user_id="user_admin",
            request_source="postman",
            config_versions=(("decision", "v1"),),
            traceability_id=uuid.uuid4()
        )

def test_missing_timestamp():
    with pytest.raises(ContextValidationException, match="execution_timestamp must be a valid datetime object."):
        ExecutionContext(
            run_id=uuid.uuid4(),
            correlation_id="corr-123",
            execution_timestamp="2026-07-08",
            platform_version="1.0.0",
            environment=Environment.PROD,
            execution_mode=ExecutionMode.API,
            user_id="user_admin",
            request_source="postman",
            config_versions=(("decision", "v1"),),
            traceability_id=uuid.uuid4()
        )

def test_invalid_environment():
    with pytest.raises(ContextValidationException, match="environment must be a valid Environment enum."):
        ExecutionContext(
            run_id=uuid.uuid4(),
            correlation_id="corr-123",
            execution_timestamp=datetime.now(),
            platform_version="1.0.0",
            environment="PROD",  # Should be Environment.PROD
            execution_mode=ExecutionMode.API,
            user_id="user_admin",
            request_source="postman",
            config_versions=(("decision", "v1"),),
            traceability_id=uuid.uuid4()
        )

def test_empty_string_validation():
    with pytest.raises(ContextValidationException, match="platform_version must be a non-empty string."):
        ExecutionContext(
            run_id=uuid.uuid4(),
            correlation_id="corr-123",
            execution_timestamp=datetime.now(),
            platform_version="   ",
            environment=Environment.PROD,
            execution_mode=ExecutionMode.API,
            user_id="user_admin",
            request_source="postman",
            config_versions=(("decision", "v1"),),
            traceability_id=uuid.uuid4()
        )

def test_immutability():
    ctx = ExecutionContext(
        run_id=uuid.uuid4(),
        correlation_id="corr-123",
        execution_timestamp=datetime.now(),
        platform_version="1.0.0",
        environment=Environment.PROD,
        execution_mode=ExecutionMode.API,
        user_id="user_admin",
        request_source="postman",
        config_versions=(("decision", "v1"),),
        traceability_id=uuid.uuid4()
    )
    from dataclasses import FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        ctx.correlation_id = "corr-456"

def test_equality_and_hashability():
    run_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    ts = datetime.now()
    
    ctx1 = ExecutionContext(
        run_id=run_id,
        correlation_id="corr",
        execution_timestamp=ts,
        platform_version="1.0",
        environment=Environment.DEV,
        execution_mode=ExecutionMode.BATCH,
        user_id="usr",
        request_source="src",
        config_versions=(),
        traceability_id=trace_id
    )
    
    ctx2 = ExecutionContext(
        run_id=run_id,
        correlation_id="corr",
        execution_timestamp=ts,
        platform_version="1.0",
        environment=Environment.DEV,
        execution_mode=ExecutionMode.BATCH,
        user_id="usr",
        request_source="src",
        config_versions=(),
        traceability_id=trace_id
    )
    
    assert ctx1 == ctx2
    assert hash(ctx1) == hash(ctx2)
