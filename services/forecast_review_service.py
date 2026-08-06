"""
Module Contract
===============

Purpose:
    Application Service layer that acts as the SINGLE orchestration point
    for the Forecast Review & Decision Support System. Coordinates dataset
    loading, deterministic analytics, reporting, and AI narrative generation.

Consumes:
    - config.settings
    - models.review_models.ReviewResult
    - services.review_engine.ReviewEngine
    - services.exceptions.DatasetLoadError
    - reports.html_report (optional)
    - reports.teams_summary (optional)
    - services.llm_factory (optional)

Produces:
    - ReviewResult (final pipeline object)
    - Artifacts (HTML, LLM Summaries) in the output directory

Does NOT:
    - Implement CLI logic.
    - Implement FastAPI endpoints.
    - Perform business logic or calculations directly.
    - Expose internal pipeline components.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from datetime import datetime
from config import settings
from models.review_models import ReviewResult
from models.execution_models import ForecastReviewExecution
from models.execution_context import ExecutionContext
from models.pipeline_metrics import PipelineExecutionMetrics, StageTiming, ExecutionSummary
from services.exceptions import DatasetLoadError
from services.review_engine import ReviewEngine
from services.service_registry import ReportGenerator
from reports.markdown_generator import MarkdownGenerator
from models.summary_models import SummaryBundleFactory
from llm.llm_provider import LLMProviderError, LLMParseError, ValidationError
from services.storage_manager import StorageManager
import time

logger = logging.getLogger(__name__)

# File extension → pandas reader mapping
_READERS: dict[str, Any] = {
    ".xlsx": pd.read_excel,
    ".xls": pd.read_excel,
    ".csv": pd.read_csv,
}


class ForecastReviewService:
    """
    Central orchestration service for the forecast review pipeline.
    """

    def __init__(
        self,
        engine: ReviewEngine,
        html_generator: ReportGenerator,
        json_generator: ReportGenerator,
        teams_generator: ReportGenerator,
        llm_service_factory: Any,
    ) -> None:
        self.engine = engine
        self.html_generator = html_generator
        self.json_generator = json_generator
        self.teams_generator = teams_generator
        self.llm_service_factory = llm_service_factory
        self.storage_manager = StorageManager()
        logger.info("ForecastReviewService Started with injected dependencies.")

    def run(self, input_path: Path) -> ForecastReviewExecution:
        """
        Execute the full forecast review orchestration pipeline.

        Args:
            input_path: Path to the input dataset file.

        Returns:
            The complete ForecastReviewExecution record.

        Raises:
            FileNotFoundError: If the input file is missing.
            DatasetLoadError: If the input file is unsupported or corrupt.
        """
        started_at = datetime.utcnow()
        context = self.storage_manager.generate_execution_context()
        self.storage_manager.initialize_run_directory(context)
        reports_dir = self.storage_manager.get_run_reports_directory(context)
        
        logger.info("ForecastReviewService Execution Started for %s", context.execution_id)
        
        stage_timings = []
        
        def record_stage(name: str, start: float, exc=None):
            duration = time.monotonic() - start
            status = "SUCCESS" if not exc else "FAILED"
            stage_timings.append(StageTiming(
                stage_name=name,
                start_time=start,
                end_time=start + duration,
                duration_seconds=duration,
                status=status,
                exception_metadata=str(exc) if exc else None
            ))

        # 1. Load dataset
        t0 = time.monotonic()
        try:
            dataframe = self._load_dataset(input_path)
            record_stage("Dataset Loading", t0)
        except Exception as e:
            record_stage("Dataset Loading", t0, e)
            raise

        # 2. Execute deterministic analytics
        t0 = time.monotonic()
        try:
            result = self.engine.run(dataframe)
            result.pipeline_metadata.execution_id = context.execution_id
            record_stage("Analytics", t0)
        except Exception as e:
            record_stage("Analytics", t0, e)
            raise

        html_path = None
        json_path = None
        teams_path = None
        exec_summary = None
        mgr_summary = None
        email_summary = None

        if result.pipeline_metadata.pipeline_status == "SUCCESS":
            # 4. Generate HTML report
            t0 = time.monotonic()
            html_path = reports_dir / "forecast_review.html"
            try:
                self.html_generator(result, html_path)
                record_stage("HTML Generator", t0)
            except Exception as e:
                logger.warning("HTML reporting failed: %s", e)
                record_stage("HTML Generator", t0, e)
                html_path = None

            # 5. Generate AI summaries
            t0 = time.monotonic()
            try:
                exec_summary, mgr_summary, email_summary, teams_path = self._generate_llm_outputs(result, reports_dir, context)
                record_stage("LLM Generation", t0)
            except Exception as e:
                record_stage("LLM Generation", t0, e)
            
            # If teams summary from LLM was skipped/failed, try deterministic one
            if not teams_path:
                teams_path_fallback = reports_dir / "teams_summary.json"
                try:
                    self.teams_generator(result, teams_path_fallback)
                    teams_path = teams_path_fallback
                    logger.info("Deterministic Teams summary generated: %s", teams_path)
                except Exception as e:
                    logger.warning("Teams summary failed: %s", e)
                    teams_path = None

        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        
        json_path_predicted = reports_dir / getattr(settings, "JSON_REPORT_NAME", "forecast_review.json") if result.pipeline_metadata.pipeline_status == "SUCCESS" else None
        
        execution_summary = ExecutionSummary(
            execution_id=context.execution_id,
            total_duration_seconds=duration,
            pipeline_status=result.pipeline_metadata.pipeline_status,
            stages_executed=len(stage_timings)
        )
        
        pipeline_metrics = PipelineExecutionMetrics(
            execution_summary=execution_summary,
            stage_timings=stage_timings
        )
        
        # Save pipeline metrics
        self.storage_manager.save_json(context, "pipeline_metrics.json", pipeline_metrics.as_dict())
        
        execution_record = ForecastReviewExecution(
            review_result=result,
            html_report_path=html_path,
            json_report_path=json_path_predicted,
            executive_summary_path=exec_summary,
            manager_summary_path=mgr_summary,
            email_summary_path=email_summary,
            teams_summary_path=teams_path,
            started_at=started_at,
            completed_at=completed_at,
            execution_duration=duration,
            pipeline_status=result.pipeline_metadata.pipeline_status
        )
        # Monkey patch reports_dir for output printer
        if execution_record.review_result:
            execution_record.review_result.pipeline_metadata.reports_dir = reports_dir

        if result.pipeline_metadata.pipeline_status == "SUCCESS":
            # Generate JSON Report LAST so it can serialize the full execution state
            t0 = time.monotonic()
            try:
                self.json_generator(execution_record, json_path_predicted)
                record_stage("JSON Generator", t0)
                logger.info("JSON report generated.")
            except Exception as e:
                logger.warning("JSON reporting failed: %s", e)
                record_stage("JSON Generator", t0, e)

        logger.info("ForecastReviewService Completed.")
        return execution_record

    def _load_dataset(self, file_path: Path) -> pd.DataFrame:
        """Helper to load a forecast dataset."""
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset not found: {file_path}")

        reader = _READERS.get(file_path.suffix.lower())
        if reader is None:
            raise DatasetLoadError(
                f"Unsupported file type '{file_path.suffix}'. "
                f"Supported: {', '.join(settings.SUPPORTED_EXTENSIONS)}"
            )

        logger.info("Loading dataset from %s", file_path)
        dataframe: pd.DataFrame = reader(file_path)

        if dataframe.empty:
            raise DatasetLoadError(f"Dataset is empty: {file_path}")

        logger.info("Dataset loaded: %d rows, %d columns.", len(dataframe), len(dataframe.columns))
        return dataframe

    def _generate_llm_outputs(self, result: ReviewResult, output_dir: Path, context: ExecutionContext) -> tuple[Path | None, Path | None, Path | None, Path | None]:
        """Helper to orchestrate LLM outputs securely with granular step logging."""
        logger.info("Generating AI narratives...")

        try:
            # ── LLM Service ───────────────────────────────────────────
            logger.info("Step 1: Creating LLM service via factory")
            llm_service = self.llm_service_factory(result)
            logger.info("Step 2: LLM service created successfully")
            
            logger.info("Step 3: Generating All Summaries via Master Prompt")
            bundle = llm_service.generate_all_summaries(context)
            logger.info("Step 4: SummaryBundle received successfully")

        except (LLMProviderError, LLMParseError, ValidationError) as exc:
            logger.warning("LLM narrative generation failed — writing deterministic placeholders.")
            logger.error("LLM Exception: %s", exc)

            # ── Deterministic Fallback ─────────────────────────────────
            # Guarantee downstream consumers always receive a complete
            # artifact set regardless of external provider availability.
            reason = str(exc).split("\n")[0]  # First line only — safe for file content
            bundle = SummaryBundleFactory.create_placeholder_bundle(reason)
            logger.info("Placeholder SummaryBundle generated successfully.")

        # Finally, generate the files using MarkdownGenerator
        return MarkdownGenerator.generate_markdown_reports(bundle, output_dir)
