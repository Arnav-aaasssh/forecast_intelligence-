"""
Parses and validates cleaned JSON strings into immutable SummaryBundle models.
"""

import json
import logging
from datetime import datetime
from typing import Any

from llm.llm_provider import LLMParseError, ValidationError
from models.summary_models import (EmailSummary, ExecutiveSummary,
                                   ManagerSummary, SummaryBundle, TeamsSummary)

logger = logging.getLogger(__name__)


class ResponseParser:
    """Parses strictly formatted JSON responses into SummaryBundles."""

    @staticmethod
    def parse_bundle(clean_json_str: str, provider_name: str, model_name: str) -> SummaryBundle:
        """
        Parses JSON and applies strict domain validations.
        
        Args:
            clean_json_str: The cleaned JSON string from ResponseCleaner.
            provider_name: The name of the LLM provider (e.g. "Gemini Flash").
            model_name: The internal model identifier.
            
        Returns:
            A populated, immutable SummaryBundle.
            
        Raises:
            LLMParseError: If the string is not valid JSON.
            ValidationError: If the JSON structure or types fail strict constraints.
        """
        try:
            data = json.loads(clean_json_str)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response: %s", e)
            raise LLMParseError(f"Invalid JSON response: {e}") from e

        if not isinstance(data, dict):
            raise ValidationError("Root JSON element must be an object (dict).")

        if data.get("schema_version") != "1.0":
            raise ValidationError(f"Missing or unsupported schema_version: {data.get('schema_version')}")

        summaries = data.get("summaries")
        if not isinstance(summaries, dict):
            raise ValidationError("'summaries' key must be an object (dict).")

        required_keys = ["executive_summary", "manager_summary", "email_summary", "teams_summary"]
        for key in required_keys:
            if key not in summaries:
                raise ValidationError(f"Missing required summary key: '{key}'")
            
            val = summaries[key]
            
            # Strict validation
            if val is None:
                raise ValidationError(f"Summary '{key}' cannot be null.")
            if not isinstance(val, str):
                raise ValidationError(f"Summary '{key}' must be a string, not {type(val).__name__}.")
            
            val = val.strip()
            if not val:
                raise ValidationError(f"Summary '{key}' cannot be empty.")
            
            if len(val) < 20:
                raise ValidationError(f"Summary '{key}' is too short (length: {len(val)}). Minimum is 20.")
            
            if len(val) > 10000:
                raise ValidationError(f"Summary '{key}' is too long (length: {len(val)}). Maximum is 10000.")

        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

        return SummaryBundle(
            executive=ExecutiveSummary(content=summaries["executive_summary"].strip(), generated_at=now_str, provider=provider_name, model=model_name),
            manager=ManagerSummary(content=summaries["manager_summary"].strip(), generated_at=now_str, provider=provider_name, model=model_name),
            email=EmailSummary(content=summaries["email_summary"].strip(), generated_at=now_str, provider=provider_name, model=model_name),
            teams=TeamsSummary(content=summaries["teams_summary"].strip(), generated_at=now_str, provider=provider_name, model=model_name)
        )
