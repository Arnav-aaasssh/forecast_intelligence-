"""
Implements an infrastructure-level exponential backoff retry mechanism.
"""

import logging
import random
import time
from typing import Callable, Type, Tuple, Any

from config import settings
from llm.llm_provider import (
    LLMProviderError,
    LLMAuthenticationError,
    LLMSafetyError,
    LLMParseError,
    ValidationError,
    LLMEmptyResponseError
)

logger = logging.getLogger(__name__)

# Exceptions that indicate client errors or unrecoverable states
NON_RETRIABLE_ERRORS: Tuple[Type[Exception], ...] = (
    LLMAuthenticationError,
    LLMSafetyError,
    LLMParseError,
    ValidationError,
    LLMEmptyResponseError
)


class RetryPolicy:
    """
    Executes a callable with exponential backoff and jitter.
    Only retries on transient network and server errors.
    """

    def __init__(
        self,
        max_retries: int = settings.MAX_RETRIES,
        base_backoff: float = settings.BASE_BACKOFF_SECONDS,
        max_backoff: float = settings.MAX_BACKOFF_SECONDS,
    ):
        self.max_retries = max_retries
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff

    def execute(self, func: Callable[[], Any], provider_name: str) -> tuple[Any, int]:
        """
        Executes the function with retries.
        
        Args:
            func: The callable to execute (e.g., provider.generate).
            provider_name: Used for logging context.
            
        Returns:
            A tuple of (result, retry_count).
            
        Raises:
            Exception: The last exception encountered if all retries are exhausted,
                       or immediately if a non-retriable error occurs.
        """
        attempt = 0
        while True:
            try:
                result = func()
                return result, attempt
            except Exception as e:
                # Determine if we should retry
                if isinstance(e, NON_RETRIABLE_ERRORS):
                    logger.warning("[%s] Non-retriable error encountered: %s", provider_name, type(e).__name__)
                    raise

                if not isinstance(e, LLMProviderError):
                    # We only automatically retry domain-mapped provider errors (which include network/server errors).
                    # If it's a completely unmapped built-in exception, we probably shouldn't retry it blindly.
                    logger.warning("[%s] Unmapped exception encountered: %s", provider_name, type(e).__name__)
                    raise

                if attempt >= self.max_retries:
                    logger.error("[%s] Max retries (%d) exhausted.", provider_name, self.max_retries)
                    raise

                attempt += 1
                
                # Exponential backoff: 2^attempt * base_backoff
                sleep_time = min(self.max_backoff, self.base_backoff * (2 ** attempt))
                
                # Add jitter (randomize between 50% and 100% of sleep_time) to prevent thundering herd
                jitter_sleep = random.uniform(sleep_time * 0.5, sleep_time)
                
                logger.warning(
                    "[%s] Transient error: %s. Retrying attempt %d/%d in %.2fs...",
                    provider_name, str(e), attempt, self.max_retries, jitter_sleep
                )
                time.sleep(jitter_sleep)
