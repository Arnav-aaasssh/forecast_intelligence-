"""
Module Contract
===============

Purpose:
    Generate a professional executive HTML report from the ReviewResult
    using a Jinja2 templating architecture.

Consumes:
    - models.review_models.ReviewResult
    - reports/templates/report.html (Jinja2 Template)
    - reports/assets/report.css (Styles)

Produces:
    - HTML file (forecast_review.html)

Does NOT:
    - Perform analytics or business calculations
    - Generate narrative or call Ollama
    - Modify data or dataframes

Downstream Consumers:
    - app.py
    - External stakeholders (via email, SharePoint, or PDF)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

from models.review_models import ReviewResult
from services.exceptions import ReportGenerationError

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """Generate a self-contained HTML report from pipeline execution results using Jinja2."""

    def __init__(self, review_result: ReviewResult):
        self.result = review_result
        
        # Setup Jinja2 environment
        self.reports_dir = Path(__file__).parent
        self.templates_dir = self.reports_dir / "templates"
        self.assets_dir = self.reports_dir / "assets"
        
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def generate(self) -> str:
        """Render the Jinja2 template with the execution data and embedded CSS."""
        template = self.env.get_template("report.html.j2")
        
        # Load CSS to embed it offline
        css_path = self.assets_dir / "report.css"
        css_content = css_path.read_text(encoding="utf-8") if css_path.exists() else ""

        # Build clean context dict to prevent KeyError cascading downstream
        context: Dict[str, Any] = {
            "css_content": css_content,
            "meta": self.result.pipeline_metadata,
            "perf": self.result.performance_summary or {},
            "risk": self.result.risk_summary or {},
            "insights": self.result.insight_summary or {},
            "recommendations": self.result.top_recommendations,
        }

        # Render template 100% cleanly
        return template.render(**context)


def generate_html_report(review_result: ReviewResult, output_path: Path) -> Path:
    """Public API to generate the HTML report from a ReviewResult.

    Args:
        review_result: Completed execution results from the ReviewEngine.
        output_path: Destination path for the generated HTML file.

    Returns:
        The path to the generated HTML file.
        
    Raises:
        ReportGenerationError: If the report generation fails.
    """
    try:
        logger.info("Generating HTML executive report to %s", output_path)
        
        generator = HTMLReportGenerator(review_result)
        html_content = generator.generate()
        
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file with UTF-8 encoding
        output_path.write_text(html_content, encoding="utf-8")
        
        logger.info("Successfully generated HTML report: %s", output_path)
        return output_path
        
    except Exception as e:
        logger.error("Failed to generate HTML report: %s", str(e), exc_info=True)
        raise ReportGenerationError(f"Failed to generate HTML report: {e}") from e
