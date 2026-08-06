# Runtime Contracts Developer Guide

## Overview
The `core.contracts` module provides the immutable Data Transfer Objects (DTOs) that form the strict boundaries between architectural layers in the Enterprise Decision Intelligence Platform.

## Core Architectural Principles
1. **Immutability:** Every contract is a frozen dataclass (`@dataclass(frozen=True)`). No setters exist.
2. **Deterministic Handoffs:** Contracts must contain all required information to recreate state. 
3. **No Math/Logic:** Contracts hold data only. They do not compute math or contain business policies.
4. **No Side Effects:** Validation occurs during `__post_init__`. Invalid data raises `ContractValidationException` immediately, preventing poison data from moving downstream.

## The Contract Pipeline

### 1. `ValidatedDataset`
*   **Owner:** Data Validation Layer
*   **Purpose:** Proves dataset has been sanitized before entering Analytics.
*   **Key Fields:** `schema_version`, `row_count`, `data_hash`.

### 2. `AnalyticsResult`
*   **Owner:** Analytics Engine
*   **Purpose:** Contains the deterministic outputs of WAPE, Bias, and ML models.
*   **Key Fields:** `run_hash`, `global_wape`, `segment_metrics` (Tuple of Tuples).

### 3. `DecisionBundle`
*   **Owner:** Decision Engine
*   **Purpose:** The culmination of business policy rules evaluating `AnalyticsResult`.
*   **Key Fields:** `policy_version`, `q1`, `q2`, `q3`, `q4`, `executive`.

### 4. `ContentDocument`
*   **Owner:** Content Engine
*   **Purpose:** The assembled structural document representing the final report prior to rendering.
*   **Key Fields:** `sections` (Tuple of `ContentSection`).

### 5. `RenderedDocument`
*   **Owner:** Renderers
*   **Purpose:** The final raw bytes (PDF/JSON) outputted by the presentation layer.
*   **Key Fields:** `mime_type`, `document_bytes`, `checksum`.

## Working with Collections
Because contracts must remain fully hashable and immutable, standard python `list` and `dict` types are **strictly forbidden**.
*   Lists must be converted to `Tuple`.
*   Dictionaries must be converted to `Tuple[Tuple[Key, Value], ...]`.

## Validation
Any instantiation error will instantly raise a `core.contracts.exceptions.ContractValidationException`. Always instantiate contracts with a `try/except` block at the boundary edges.
