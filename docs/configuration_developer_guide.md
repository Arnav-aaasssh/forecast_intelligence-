# Enterprise Configuration Developer Guide

## Overview
The `core.config` module is the single source of truth for all configurable thresholds, policies, and parameters in the Enterprise Decision Intelligence Platform. 
It rigorously extracts all hardcoded logic from the application and centralizes it in deterministic, immutable dataclasses.

## Core Architectural Principles
1. **Absolute Immutability:** Once loaded, configuration objects cannot be altered (`frozen=True`).
2. **Zero Business Logic:** Configuration only holds primitive values. It never evaluates those values.
3. **No Defaults in Code:** Configurations must explicitly supply values (except for dynamic environmental overrides like `Environment`).
4. **Validation at Rest:** When loaded, the config validates all schema types and boundaries (e.g., ensuring `winsorization_percentile` is between 0.0 and 1.0).

## Configuration Hierarchy

The `EnterpriseConfig` object acts as the root node and contains exactly five domain-specific configurations plus the runtime environment config:

1. **`PlatformConfig`:** 
    *   **Scope:** System execution limits.
    *   **Parameters:** Logging levels, timeouts, retry attempts.
2. **`AnalyticsConfig`:** 
    *   **Scope:** Data science constraints.
    *   **Parameters:** Sample sizes, percentile cutoffs, coverage limits.
3. **`DecisionPolicyConfig`:** 
    *   **Scope:** The definitive business rules for evaluation.
    *   **Parameters:** Win margins, champion selection thresholds, tie-breaker strategies (e.g. `RECENT_ACCURACY`).
4. **`ContentConfig`:**
    *   **Scope:** Rules for content presentation that are medium-agnostic.
    *   **Parameters:** Evidence limits, section suppression toggles.
5. **`RendererConfig`:**
    *   **Scope:** Visual styling.
    *   **Parameters:** Formats (PDF/JSON/MARKDOWN), themes, page numbering.
6. **`EnvironmentConfig`:**
    *   **Scope:** Execution context metadata.
    *   **Parameters:** `DEV`/`STAGE`/`PROD`, `debug_mode`.

## Usage
Always use the `ConfigurationLoader` to securely load and validate the configuration from disk.

```python
from core.foundation.enums import Environment
from core.config.loader import ConfigurationLoader
from core.config.exceptions import ConfigurationLoadException

try:
    config = ConfigurationLoader.load_from_file("config.json", Environment.PROD)
    print(config.decision.ml_margin_threshold)
except ConfigurationLoadException as e:
    print(f"Failed to boot: {e}")
```
