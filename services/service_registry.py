"""
Module Contract
===============

Purpose:
    Centralized dependency composition layer.
    Serves as the ONLY place responsible for constructing application services,
    injecting dependencies, and reusing configuration.

Consumes:
    - config.settings
    - models.review_models.ReviewResult
    - All analytical, reporting, and LLM services

Produces:
    - Fully assembled, ready-to-use application services

Does NOT:
    - Perform analytics
    - Execute business rules
    - Call external APIs
    - Read datasets
    - Generate reports

Downstream Consumers:
    - app.py
    - FastAPI endpoints
    - Power Automate interfaces
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Protocol

from config import settings
from models.review_models import ReviewResult
from services.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


# =========================================================
# Protocols
# =========================================================

class ReportGenerator(Protocol):
    """Protocol for all deterministic report generators (HTML, JSON, etc.)."""
    def __call__(self, payload: Any, output_path: Path) -> Path:
        ...


class NullReportGenerator:
    """Null Object implementation for safely skipping unavailable reports."""
    def __init__(self, message: str) -> None:
        self.message = message

    def __call__(self, payload: Any, output_path: Path) -> Path:
        logger.info("Report generation skipped: %s", self.message)
        return output_path


# =========================================================
# LLM Services
# =========================================================

def build_llm_service(review_result: ReviewResult) -> "LLMService":  # type: ignore[name-defined]
    """
    Construct and return a fully wired LLMService using the Resilient Provider Chain.
    
    The registry dynamically builds a fallback chain (e.g. Gemini -> Company) with
    embedded retries, circuit breaking, and structured metric logging.

    Args:
        review_result: The completed ReviewResult used to build contextual prompts.

    Returns:
        A fully initialised LLMService ready to generate narrative summaries.

    Raises:
        ConfigurationError: If no providers could be successfully constructed.
    """
    from llm.llm_service import LLMService
    from llm.prompt_builder import PromptBuilder
    from llm.provider_registry import ProviderRegistry
    from llm.gateway import LLMGateway

    try:
        provider_chain = ProviderRegistry.build_provider_chain()
    except ValueError as e:
        raise ConfigurationError(f"Failed to build provider chain: {e}") from e

    prompt_builder = PromptBuilder(review_result)
    gateway = LLMGateway(provider_chain)
    return LLMService(prompt_builder, gateway)


# =========================================================
# Reporting Services
# =========================================================

def create_html_report_generator() -> ReportGenerator:
    """Constructs the HTML Report Generator."""
    logger.info("Creating HTML Report Generator...")
    try:
        from reports.html_report import generate_html_report
        return generate_html_report
    except ImportError:
        return NullReportGenerator("HTML report generation is unavailable.")


def create_json_report_generator() -> ReportGenerator:
    """Constructs the JSON Report Generator."""
    logger.info("Creating JSON Report Generator...")
    try:
        from reports.json_report import generate_json_report
        return generate_json_report
    except ImportError:
        return NullReportGenerator("JSON report generation is unavailable.")


def create_teams_summary_generator() -> ReportGenerator:
    """Constructs the Teams Summary Generator."""
    logger.info("Creating Teams Summary Generator...")
    try:
        from reports.teams_summary import generate_teams_summary
        return generate_teams_summary
    except ImportError:
        return NullReportGenerator("Teams summary module not found.")


# =========================================================
# Core Analytics
# =========================================================

def create_review_engine() -> "ReviewEngine":  # type: ignore[name-defined]
    """Constructs the core deterministic Review Engine."""
    logger.info("Creating ReviewEngine...")
    from services.review_engine import ReviewEngine
    return ReviewEngine()


# =========================================================
# Application Services
# =========================================================

def create_forecast_review_service() -> "ForecastReviewService":  # type: ignore[name-defined]
    """Constructs the main ForecastReviewService orchestrator with injected dependencies."""
    logger.info("Creating ForecastReviewService...")
    from services.forecast_review_service import ForecastReviewService
    
    engine = create_review_engine()
    html_generator = create_html_report_generator()
    json_generator = create_json_report_generator()
    teams_generator = create_teams_summary_generator()
    
    service = ForecastReviewService(
        engine=engine,
        html_generator=html_generator,
        json_generator=json_generator,
        teams_generator=teams_generator,
        llm_service_factory=build_llm_service
    )
    logger.info("ForecastReviewService assembled successfully.")
    return service
