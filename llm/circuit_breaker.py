"""
Implements an infrastructure-level Circuit Breaker pattern for providers.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable

from config import settings
from llm.retry import NON_RETRIABLE_ERRORS
from llm.llm_provider import LLMProviderError

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "CLOSED"       # Normal operation, requests flow through
    OPEN = "OPEN"           # Failing, requests are blocked immediately
    HALF_OPEN = "HALF_OPEN" # Testing recovery, allow one request through


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is OPEN, blocking the request."""


class CircuitBreaker:
    """
    Maintains health state of a provider to prevent cascading failures.
    Transitions:
        - CLOSED -> OPEN after `failure_threshold` consecutive failures.
        - OPEN -> HALF_OPEN after `reset_timeout` seconds.
        - HALF_OPEN -> CLOSED on first success.
        - HALF_OPEN -> OPEN on first failure.
    """

    def __init__(
        self,
        provider_name: str,
        failure_threshold: int = settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        reset_timeout: int = settings.CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS,
    ):
        self.provider_name = provider_name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def execute(self, func: Callable[[], Any]) -> Any:
        """
        Executes the function if the circuit allows it.
        """
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self.last_failure_time > self.reset_timeout:
                logger.info("[%s] Circuit transitioning OPEN -> HALF_OPEN.", self.provider_name)
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(f"Circuit is OPEN for {self.provider_name}.")

        try:
            result = func()
        except Exception as e:
            self._record_failure(e)
            raise

        self._record_success()
        return result

    def _record_failure(self, exc: Exception) -> None:
        """Records a failure and transitions state if necessary."""
        # We only count transient errors towards circuit breaking.
        # If it's a validation error or safety block, the provider isn't strictly "down".
        if isinstance(exc, NON_RETRIABLE_ERRORS) or not isinstance(exc, LLMProviderError):
            return

        self.last_failure_time = time.monotonic()
        
        if self.state == CircuitState.HALF_OPEN:
            logger.warning("[%s] Circuit transitioning HALF_OPEN -> OPEN (Failed probe).", self.provider_name)
            self.state = CircuitState.OPEN
            return

        self.failure_count += 1
        logger.debug("[%s] Failure recorded. Count: %d/%d", self.provider_name, self.failure_count, self.failure_threshold)
        
        if self.failure_count >= self.failure_threshold:
            logger.error("[%s] Circuit transitioning CLOSED -> OPEN (Threshold reached).", self.provider_name)
            self.state = CircuitState.OPEN

    def _record_success(self) -> None:
        """Resets the circuit on success."""
        if self.state == CircuitState.HALF_OPEN:
            logger.info("[%s] Circuit transitioning HALF_OPEN -> CLOSED (Successful probe).", self.provider_name)
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
