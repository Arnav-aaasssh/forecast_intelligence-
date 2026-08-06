"""
Module Contract
===============

Purpose:
    Machine-readable reporting layer for the Forecast Review & Decision Support System.
    Generates a canonical JSON representation of the ReviewResult.

Consumes:
    - models.review_models.ReviewResult
    - models.review_models.PipelineMetadata
    - models.review_models.RecommendationCard
    - config.settings

Produces:
    - JSON file containing enterprise reporting schema

Does NOT:
    - Execute analytics
    - Modify the ReviewResult
    - Interact with LLMs
    - Generate HTML

Downstream Consumers:
    - FastAPI endpoints
    - Power Automate
    - Microsoft Teams
    - SharePoint
    - Power BI
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import settings
from models.review_models import RecommendationCard
from models.execution_models import ForecastReviewExecution

logger = logging.getLogger(__name__)


class JSONReportGenerator:
    """
    Stateful generator for transforming ReviewResult into an enterprise JSON contract.
    """

    def __init__(self, execution: ForecastReviewExecution, output_dir: Path) -> None:
        self.execution = execution
        self.output_dir = output_dir

    def generate(self) -> dict[str, Any]:
        """
        Constructs the stable JSON schema from the deterministic review results.
        """
        from services.serialization import serialize_review_result
        return serialize_review_result(self.execution)


def generate_json_report(execution: ForecastReviewExecution, output_path: Path) -> Path:
    """
    Generate a deterministic, machine-readable JSON report from the execution results.

    Args:
        execution: The complete execution object representing the entire pipeline run.
        output_path: Directory where the JSON file should be saved.

    Returns:
        The Path to the newly created JSON file.
    """
    logger.info("Generating JSON report...")
    
    file_path = output_path
    
    try:
        # Create the stable schema
        generator = JSONReportGenerator(execution, output_path.parent)
        json_data = generator.generate()
        
        # Ensure the directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize to disk
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4, ensure_ascii=False)
            
        logger.info("JSON report successfully generated at %s", file_path)
        
    except Exception:
        # Using exception() preserves full traceback
        logger.exception("Failed to generate JSON report.")
        
    return file_path
