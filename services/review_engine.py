"""
Module: review_engine.py

Purpose:
    Coordinates the end-to-end forecast review pipeline.
    This class acts purely as an orchestrator. It does not perform analytics,
    computations, or AI generation itself.

Consumes:
    - Raw Forecast DataFrame
    - Instantiated analytics modules (via Dependency Injection)

Produces:
    - ReviewResult (strongly typed dataclass with enriched data and metadata)

Does NOT:
    - Perform calculations, ML, math, or analytics logic.
    - Read from or write to external systems (Excel, SharePoint, Teams).
    - Trigger external services (FastAPI, Power Automate, Ollama).

Downstream Consumers:
    - FastAPI endpoints
    - Prompt Builder / LLM integration layer
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any, Protocol, runtime_checkable

import pandas as pd

from models.review_models import PipelineMetadata, ReviewResult
from services.validation import DatasetValidator

# Try to import analytics modules if they exist; otherwise define dummy implementations
try:
    from analytics.performance import PerformanceAnalyzer
except ImportError:
    class PerformanceAnalyzer:
        def analyze(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]: return df, {}

try:
    from analytics.comparison import ComparisonAnalyzer
except ImportError:
    class ComparisonAnalyzer:
        def analyze(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]: return df, {}

try:
    from analytics.drift import DriftAnalyzer
except ImportError:
    class DriftAnalyzer:
        def analyze(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]: return df, {}

try:
    from analytics.risk import RiskAnalyzer
except ImportError:
    class RiskAnalyzer:
        def analyze(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]: return df, {}

try:
    from analytics.insights import InsightsAnalyzer
except ImportError:
    class InsightsAnalyzer:
        def analyze(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]: return df, {}

try:
    from analytics.recommendations import RecommendationAnalyzer
except ImportError:
    class RecommendationAnalyzer:
        def analyze(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]: return df, {}


logger = logging.getLogger(__name__)


# --- Protocols (Type Safety) ---

@runtime_checkable
class AnalyzerProtocol(Protocol):
    """Protocol enforcing the standard interface for all analytics modules."""
    def analyze(self, dataframe: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        ...


@runtime_checkable
class ValidatorProtocol(Protocol):
    """Protocol enforcing the standard interface for dataset validation."""
    def validate(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        ...


# --- Internal State ---

@dataclass
class ExecutionState:
    """
    Encapsulates the runtime state for a single pipeline execution.
    This guarantees that ReviewEngine is entirely stateless and thread-safe.
    """
    dataframe: pd.DataFrame
    start_time: float = field(default_factory=perf_counter)
    execution_timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    modules_executed: list[str] = field(default_factory=list)
    failed_module: str | None = None
    status: str = "SUCCESS"
    
    # Summaries
    validation_summary: dict[str, Any] | None = None
    performance_summary: dict[str, Any] | None = None
    comparison_summary: dict[str, Any] | None = None
    drift_summary: dict[str, Any] | None = None
    risk_summary: dict[str, Any] | None = None
    insight_summary: dict[str, Any] | None = None
    recommendation_summary: dict[str, Any] | None = None


# --- Engine ---

class ReviewEngine:
    """
    Orchestration engine for the Forecast Review system.
    
    Strictly follows the Single Responsibility Principle: its only job is
    to coordinate the sequential execution of dependency-injected analytics
    modules and collect their outputs into a unified ReviewResult.
    
    This class is completely stateless and safe for use as a singleton
    in FastAPI across highly concurrent workloads.
    """

    def __init__(
        self,
        validator: ValidatorProtocol | Any | None = None,
        performance: AnalyzerProtocol | None = None,
        comparison: AnalyzerProtocol | None = None,
        drift: AnalyzerProtocol | None = None,
        risk: AnalyzerProtocol | None = None,
        insights: AnalyzerProtocol | None = None,
        recommendations: AnalyzerProtocol | None = None,
    ) -> None:
        """
        Initialize the ReviewEngine with full dependency injection.
        """
        # Dependencies are saved to self, but NO execution data is stored here.
        self.validator = validator
        self.performance = performance or PerformanceAnalyzer()
        self.comparison = comparison or ComparisonAnalyzer()
        self.drift = drift or DriftAnalyzer()
        self.risk = risk or RiskAnalyzer()
        self.insights = insights or InsightsAnalyzer()
        self.recommendations = recommendations or RecommendationAnalyzer()

        logger.info("ReviewEngine initialized statelessly with full dependency injection.")

    def run(self, dataframe: pd.DataFrame) -> ReviewResult:
        """
        Execute the analytics pipeline strictly as an orchestrator.

        Args:
            dataframe (pd.DataFrame): Raw forecast dataset.

        Returns:
            ReviewResult: A unified dataclass containing enriched data, summaries,
                          and execution telemetry.
        """
        logger.info("Pipeline Started.")
        
        # Instantiate localized thread-safe state for this run
        state = ExecutionState(dataframe=dataframe)

        try:
            state = self._validate_dataset(state)
            state = self._run_performance(state)
            state = self._run_comparison(state)
            state = self._run_drift(state)
            state = self._run_risk(state)
            state = self._run_insights(state)
            state = self._run_recommendations(state)
            
            logger.info("Pipeline Completed Successfully.")
        except Exception as e:
            state.status = "FAILED"
            logger.error(
                "Pipeline execution failed critically at module: %s. Error: %s", 
                state.failed_module, 
                str(e),
                exc_info=True
            )
            # Fail-fast: The pipeline halts and immediately returns the result built so far.

        return self._build_result(state)

    def _validate_dataset(self, state: ExecutionState) -> ExecutionState:
        """Execute validation module and halt if dataset violates the schema."""
        start_time = perf_counter()
        state.failed_module = "validation"
        logger.info("Executing Validation...")
        
        if self.validator is not None and hasattr(self.validator, "validate"):
            # Handle standardized ValidatorProtocol safely
            state.dataframe = self.validator.validate(state.dataframe)
        else:
            if self.validator is not None:
                logger.warning("Injected validator does not satisfy ValidatorProtocol. Using default DatasetValidator.")
                
            # Instantiate the default implementation safely per-run to ensure thread safety
            default_validator = DatasetValidator(dataset=state.dataframe)
            report = default_validator.validate_dataset()
            
            if default_validator.validated_dataset is not None:
                state.dataframe = default_validator.validated_dataset
                
            state.validation_summary = {
                "status": report.status,
                "errors": report.errors,
                "warnings": getattr(report, "warnings", []),
            }
                
            if report.status == "FAILED":
                for error in report.errors:
                    logger.error("Validation Error: %s", error)
                # Halt pipeline immediately
                raise ValueError(f"Dataset validation failed: {len(report.errors)} errors found.")
            
        state.modules_executed.append("validation")
        logger.info("Validation Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _run_performance(self, state: ExecutionState) -> ExecutionState:
        """Execute performance analysis module."""
        start_time = perf_counter()
        state.failed_module = "performance"
        logger.info("Executing Performance...")
        state.dataframe, state.performance_summary = self.performance.analyze(state.dataframe)
        state.modules_executed.append("performance")
        logger.info("Performance Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _run_comparison(self, state: ExecutionState) -> ExecutionState:
        """Execute forecast comparison module."""
        start_time = perf_counter()
        state.failed_module = "comparison"
        logger.info("Executing Comparison...")
        state.dataframe, state.comparison_summary = self.comparison.analyze(state.dataframe)
        state.modules_executed.append("comparison")
        logger.info("Comparison Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _run_drift(self, state: ExecutionState) -> ExecutionState:
        """Execute forecast drift module."""
        start_time = perf_counter()
        state.failed_module = "drift"
        logger.info("Executing Drift...")
        state.dataframe, state.drift_summary = self.drift.analyze(state.dataframe)
        state.modules_executed.append("drift")
        logger.info("Drift Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _run_risk(self, state: ExecutionState) -> ExecutionState:
        """Execute risk intelligence module."""
        start_time = perf_counter()
        state.failed_module = "risk"
        logger.info("Executing Risk...")
        state.dataframe, state.risk_summary = self.risk.analyze(state.dataframe)
        state.modules_executed.append("risk")
        logger.info("Risk Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _run_insights(self, state: ExecutionState) -> ExecutionState:
        """Execute insights generation module."""
        start_time = perf_counter()
        state.failed_module = "insights"
        logger.info("Executing Insights...")
        state.dataframe, state.insight_summary = self.insights.analyze(state.dataframe)
        state.modules_executed.append("insights")
        logger.info("Insights Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _run_recommendations(self, state: ExecutionState) -> ExecutionState:
        """Execute recommendations generation module."""
        start_time = perf_counter()
        state.failed_module = "recommendations"
        logger.info("Executing Recommendations...")
        state.dataframe, state.recommendation_summary = self.recommendations.analyze(state.dataframe)
        state.modules_executed.append("recommendations")
        logger.info("Recommendations Complete in %.4fs.", perf_counter() - start_time)
        return state

    def _build_result(self, state: ExecutionState) -> ReviewResult:
        """Assemble the final ReviewResult dataclass."""
        execution_duration = perf_counter() - state.start_time
        logger.info("Total execution time: %.4f seconds.", execution_duration)

        rows = len(state.dataframe) if state.dataframe is not None else 0
        
        metadata = PipelineMetadata(
            rows_processed=rows,
            pipeline_status=state.status,
            execution_timestamp=datetime.fromisoformat(state.execution_timestamp),
            modules_executed=state.modules_executed,
            failed_module=state.failed_module if state.status == "FAILED" else None,
            execution_time_seconds=round(execution_duration, 4),
        )

        return ReviewResult(
            dataframe=state.dataframe,
            validation_summary=state.validation_summary or {
                "status": state.status,
                "warnings": [],
                "errors": [state.failed_module] if state.failed_module else []
            },
            performance_summary=state.performance_summary,
            comparison_summary=state.comparison_summary,
            drift_summary=state.drift_summary,
            risk_summary=state.risk_summary,
            insight_summary=state.insight_summary,
            recommendation_summary=state.recommendation_summary,
            top_recommendations=state.recommendation_summary.get("top_recommendations", []) if state.recommendation_summary else [],
            pipeline_metadata=metadata
        )