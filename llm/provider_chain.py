"""
Implements the failover chain to abstract multi-provider resilience.
"""

import logging
from typing import Sequence

from llm.llm_provider import BaseLLMProvider, LLMProviderError
from models.summary_models import SummaryBundleFactory

logger = logging.getLogger(__name__)


class ProviderChain(BaseLLMProvider):
    """
    Acts as a single virtual provider that sequentially attempts a chain
    of underlying providers until one succeeds. If all fail, raises an error.
    """

    def __init__(self, providers: Sequence[BaseLLMProvider]):
        super().__init__()
        self.providers = providers
        if not self.providers:
            raise ValueError("ProviderChain requires at least one provider.")
        logger.info("ProviderChain initialized with %d providers.", len(self.providers))

    @property
    def provider_name(self) -> str:
        return "ProviderChain"

    def generate(self, prompt: str) -> str:
        """
        Iterate through the configured providers. Return on first success.
        
        Args:
            prompt: The full prompt payload.
            
        Returns:
            The raw string response from the first successful provider.
            
        Raises:
            LLMProviderError: If ALL providers in the chain fail.
        """
        last_exception = None

        for idx, provider in enumerate(self.providers):
            try:
                logger.info("[ProviderChain] Attempting %s (%d/%d)", provider.provider_name, idx + 1, len(self.providers))
                return provider.generate(prompt)
            except Exception as e:
                logger.error("[ProviderChain] Provider %s failed: %s", provider.provider_name, type(e).__name__)
                last_exception = e

        logger.error("[ProviderChain] All configured providers have failed.")
        
        # Raise the last exception to trigger the deterministic fallback at the service layer
        if last_exception:
            raise LLMProviderError(f"All providers in the chain failed. Last error: {str(last_exception)}") from last_exception
        
        raise LLMProviderError("All providers failed.")
