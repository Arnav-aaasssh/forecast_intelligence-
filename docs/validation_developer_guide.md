# Validation & Exception Framework Developer Guide

## Overview
The `core.validation` module provides the shared infrastructure for validating data and handling exceptions across the entire Enterprise Decision Intelligence platform. It prevents logic duplication and guarantees that all layers throw deterministic errors.

## Core Architectural Principles
1. **Stateless Validators:** Validators hold zero business logic and zero state. They simply answer: *Does this value match this format?*
2. **Central Registry:** The `ValidationRegistry` acts as the execution engine. It accepts a mapping of object fields to validators and executes them safely, returning an aggregate `ValidationResult`.
3. **Deterministic Exceptions:** Every exception in the platform must inherit from `PlatformException` and provide structured context (e.g. error codes, suggested resolutions).

## The Exception Hierarchy
All errors inherit from `PlatformException`. This root exception enforces that the following fields are always populated:
*   `error_code`: Unique identifier (e.g. `CFG-001`).
*   `category`: Broad classification (e.g. `Configuration`, `Analytics`).
*   `message`: Human-readable error description.
*   `suggested_resolution`: Actionable advice for the operator.
*   `root_cause` (Optional)
*   `execution_context_id` / `traceability_id`: Pointers back to the IV&V audit trail.

**Sub-Exceptions:**
*   `ValidationException`, `ConfigurationException`, `ContractValidationException`, `AnalyticsException`, `DecisionEngineException`, `ContentEngineException`, `RendererException`, `OrchestratorException`.

## Using the Validation Registry

Instead of writing custom `if` statements, register standard validators and run objects through the registry.

```python
from core.validation.registry import ValidationRegistry
from core.validation.validators import UUIDValidator, RangeValidator

registry = ValidationRegistry()
registry.register("uuid", UUIDValidator())
registry.register("percentile", RangeValidator(0.0, 1.0))

data = {
    "job_id": "invalid-id",
    "score": 1.5
}

# Execute
result = registry.validate_object(data, {"job_id": "uuid", "score": "percentile"})

if not result.passed:
    for error in result.errors:
        print(f"Failed {error.field_name}: {error.error_message}")
```

## Adding Custom Validators
To add a new validator, simply inherit from `BaseValidator` and implement the `validate(self, value: Any) -> Tuple[bool, str]` method. No state should be persisted on `self` during the validation execution.
