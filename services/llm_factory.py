"""
Module Contract
===============

Purpose:
    Serve as the single source of truth for constructing the LLM orchestration layer.
    Assembles the dependencies (PromptBuilder, LLMProvider, LLMService) into a cohesive,
    ready-to-use service.

Consumes:
    - config.settings
    - models.review_models.ReviewResult
    - llm.prompt_builder.PromptBuilder
    - llm.llm_provider.GeminiProvider
    - llm.llm_service.LLMService

Produces:
    - A fully initialized, stateless LLMService.

Does NOT:
    - Execute LLM calls.
    - Perform analytics.
    - Read files directly.

Downstream Consumers:
    - app.py
    - FastAPI endpoints
"""

import logging

from config import settings
from llm.llm_provider import GeminiProvider
from llm.llm_service import LLMService
from llm.prompt_builder import PromptBuilder
from models.review_models import ReviewResult

logger = logging.getLogger(__name__)


def create_llm_service(review_result: ReviewResult) -> LLMService:
    """
    Factory function to assemble the LLM orchestration layer using dependency injection.
    
    Reads all provider configurations securely from the centralized settings module.
    
    Args:
        review_result: The completed deterministic pipeline result.
        
    Returns:
        A fully configured LLMService instance.
        
    Raises:
        ValueError: If essential configuration like GEMINI_API_KEY is missing.
    """
    logger.info("Configuration loaded. Assembling LLM components.")
    
    # 1. Validate critical configuration
    if settings.LLM_PROVIDER.lower() == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not defined. The LLMService cannot be started "
                "with an invalid or missing API key."
            )
            
        # 2. Instantiate Provider
        provider = GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
            temperature=settings.GEMINI_TEMPERATURE,
            max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS
        )
    else:
        # Fallback or extension point for OpenAIProvider, etc.
        raise NotImplementedError(f"Provider '{settings.LLM_PROVIDER}' is not currently supported.")

    # 3. Instantiate Builder
    prompt_builder = PromptBuilder(review_result)
    
    # 4. Assemble Service
    llm_service = LLMService(prompt_builder, provider)
    logger.info("LLMService created successfully.")
    
    return llm_service
