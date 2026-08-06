"""
Module Contract
===============

Purpose:
    Transform the deterministic ReviewResult into structured LLM prompts.
    Serves as the data-binding layer between the analytics engine and language models.

Consumes:
    - models.review_models.ReviewResult
    - llm.prompts (Constants)

Produces:
    - Fully rendered prompt strings ready for LLM inference.

Does NOT:
    - Perform calculations or business rules.
    - Inspect pandas DataFrames directly.
    - Call any LLM API.
    - Modify the underlying ReviewResult data.

Downstream Consumers:
    - LLM orchestration layer (e.g., Azure OpenAI, LangChain wrapper)
"""

import logging
from typing import Any, Dict, List

from jinja2 import Template

from llm import prompts
from models.review_models import RecommendationCard, ReviewResult

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Transforms a ReviewResult into strictly formatted LLM prompts using Jinja2."""

    def __init__(self, review_result: ReviewResult) -> None:
        """
        Initialize the PromptBuilder with the pipeline results.
        
        Args:
            review_result: The complete, frozen analytical output.
        """
        logger.info("PromptBuilder initialized.")
        self.result = review_result
        self._context: Dict[str, Any] = self._build_context()

    def build_master_prompt(self) -> str:
        """Render the master prompt that requests all summaries in JSON."""
        prompt = self._render_prompt(prompts.MASTER_SUMMARY_PROMPT)
        logger.info("Master prompt built.")
        return prompt

    def build_executive_prompt(self) -> str:
        """Render the executive summary prompt."""
        prompt = self._render_prompt(prompts.EXECUTIVE_SUMMARY_PROMPT)
        logger.info("Executive prompt built.")
        return prompt

    def build_manager_prompt(self) -> str:
        """Render the manager/operational summary prompt."""
        prompt = self._render_prompt(prompts.MANAGER_SUMMARY_PROMPT)
        logger.info("Manager prompt built.")
        return prompt

    def build_email_prompt(self) -> str:
        """Render the email distribution prompt."""
        prompt = self._render_prompt(prompts.EMAIL_SUMMARY_PROMPT)
        logger.info("Email prompt built.")
        return prompt

    def build_teams_prompt(self) -> str:
        """Render the Microsoft Teams alert prompt."""
        prompt = self._render_prompt(prompts.TEAMS_SUMMARY_PROMPT)
        logger.info("Teams prompt built.")
        return prompt

    def _build_context(self) -> Dict[str, Any]:
        """Aggregate all required prompt variables into a single context dict."""
        perf = self.result.performance_summary or {}
        risk = self.result.risk_summary or {}
        insights = self.result.insight_summary or {}
        meta = self.result.pipeline_metadata

        context = {
            "pipeline_status": self._sanitize_value(meta.pipeline_status),
            "execution_date": self._sanitize_value(meta.execution_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')),
            "rows_processed": self._sanitize_value(meta.rows_processed),
            
            "overall_forecast_health": self._extract_summary(insights, "overall_forecast_health"),
            "critical_forecasts": self._extract_summary(insights, "critical_forecasts"),
            
            "manual_accuracy": self._extract_summary(perf, "manual_accuracy"),
            "ml_accuracy": self._extract_summary(perf, "ml_accuracy"),
            "winning_method": self._extract_summary(perf, "winner"),
            
            "highest_risk_region": self._extract_summary(risk, "highest_risk_region"),
            "highest_risk_offering": self._extract_summary(risk, "highest_risk_offering"),
            "top_risk_driver": self._extract_summary(risk, "top_primary_risk_driver"),
            "manager_reviews": self._extract_summary(risk, "manager_reviews_required"),
            
            "recommendations": self._serialize_recommendations(self.result.top_recommendations)
        }
        logger.info("Context generated.")
        return context

    def _extract_summary(self, summary_dict: dict, key: str) -> Any:
        """Safely extract a value from a summary dictionary."""
        if key not in summary_dict:
            logger.warning("Expected key '%s' not found in summary dictionary.", key)
        return self._sanitize_value(summary_dict.get(key))

    def _sanitize_value(self, value: Any) -> Any:
        """Ensure no Python 'None' or empty strings leak into the LLM context."""
        if value is None:
            return "Not Available"
        
        if isinstance(value, float):
            return f"{value:.2f}"
            
        if isinstance(value, str) and not value.strip():
            return "Not Available"
            
        return value

    def _serialize_recommendations(self, recommendations: List[RecommendationCard]) -> str:
        """Format recommendations into an ordered markdown business list."""
        if not recommendations:
            return "Not Available."
            
        serialized = []
        for i, rec in enumerate(recommendations, start=1):
            serialized.append(f"{i}. **{rec.action}** (Priority: {rec.priority})\n   *Reason: {rec.reason}*")
            
        return "\n\n".join(serialized)

    def _render_prompt(self, template_string: str) -> str:
        """Render a Jinja2 template safely with the loaded context."""
        try:
            template = Template(template_string)
            return template.render(**self._context)
        except Exception as e:
            logger.error("Failed to render prompt template: %s", str(e), exc_info=True)
            raise RuntimeError(f"Prompt rendering failed: {e}") from e
