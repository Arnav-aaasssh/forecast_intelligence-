# ExecutionContext Developer Guide

## Overview
The `ExecutionContext` is the root runtime object for the Enterprise Decision Intelligence platform. It accompanies every execution through the platform.

### Core Architectural Principle
The `ExecutionContext` owns **runtime metadata only**. 
It MUST NOT contain:
- Business logic
- Analytics metrics
- Policies or configurations
- Evidence or Narrative text
- Decision states

## Object Contract
The `ExecutionContext` is implemented as an **immutable dataclass** (`frozen=True`). It has no setters and permits no runtime modifications.

### Required Fields
| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | `uuid.UUID` | Unique identifier for the platform execution run. |
| `correlation_id` | `str` | Trace identifier for cross-system logging. |
| `execution_timestamp` | `datetime` | The precise time the job initialized. |
| `platform_version` | `str` | The semantic version of the platform codebase. |
| `environment` | `Environment` | Enum: `DEV`, `STAGE`, `PROD`, `TEST`. |
| `execution_mode` | `ExecutionMode` | Enum: `INTERACTIVE`, `BATCH`, `API`, `SYSTEM`. |
| `user_id` | `str` | The identifier of the requesting user or system. |
| `request_source` | `str` | The originating system (e.g., UI, Scheduler, API). |
| `config_versions` | `Dict[str, str]` | Version mapping of loaded configurations. |
| `traceability_id` | `uuid.UUID` | The IV&V audit ID for end-to-end traceability. |
| `job_id` | `Optional[str]` | Optional batch job identifier. |

## Validation
Validation is strictly enforced during initialization via the `__post_init__` method.
If any field violates type or format constraints, a `ContextValidationException` is raised instantly.

## Usage Example
```python
import uuid
from datetime import datetime
from core.foundation.execution_context import ExecutionContext
from core.foundation.enums import Environment, ExecutionMode

ctx = ExecutionContext(
    run_id=uuid.uuid4(),
    correlation_id="req-9912",
    execution_timestamp=datetime.now(),
    platform_version="1.0.0",
    environment=Environment.PROD,
    execution_mode=ExecutionMode.API,
    user_id="user_admin",
    request_source="api-gateway",
    config_versions={"decision": "v1.2", "analytics": "v3.0"},
    traceability_id=uuid.uuid4()
)
```
