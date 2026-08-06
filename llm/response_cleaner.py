"""
Cleans raw LLM strings into parseable JSON payloads.
"""

import logging
import re

logger = logging.getLogger(__name__)


class ResponseCleaner:
    """Removes conversational wrappers and markdown fences from LLM responses."""

    @staticmethod
    def clean(raw_response: str) -> str:
        """
        Strips markdown code fences (e.g. ```json ... ```) and leading/trailing whitespace.
        
        Args:
            raw_response: The raw string from the LLM.
            
        Returns:
            A cleaned string that should be valid JSON.
        """
        if not raw_response:
            return ""

        cleaned = raw_response.strip()

        # Remove markdown JSON code blocks if present
        # Match ```json (or just ```) at start, and ``` at end, ignoring surrounding whitespace
        pattern = re.compile(r"^```(?:json)?\s*(.*?)\s*```$", re.DOTALL | re.IGNORECASE)
        match = pattern.search(cleaned)
        
        if match:
            cleaned = match.group(1).strip()
            logger.debug("Stripped markdown code fences from response.")

        # Sometimes models might add "Here is the JSON:" before the block, even though instructed not to.
        # If it doesn't start with { but has a { inside, we might need to extract it.
        # Given our strict prompting, we assume the model behaves, but just in case:
        if not cleaned.startswith("{") and "{" in cleaned:
            # Find the first { and the last }
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end+1]
                logger.debug("Extracted JSON substring from conversational wrapper.")

        return cleaned
