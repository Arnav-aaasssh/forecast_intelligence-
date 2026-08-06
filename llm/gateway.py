"""
LLM Gateway
===========

The single orchestration point for all AI providers. Handles:
- Caching (placeholder)
- Metric aggregation
- Interfacing with ProviderChain for failover
- Returning telemetry to the execution context
"""

import logging
import time
from typing import Optional

from llm.provider_chain import ProviderChain
from llm.llm_provider import LLMProviderError
from models.execution_context import ExecutionContext
from models.provider_metrics import ProviderMetrics

logger = logging.getLogger("llm")


class LLMGateway:
    """
    Central orchestration point for LLM interactions.
    """

    def __init__(self, provider_chain: ProviderChain):
        self.provider_chain = provider_chain
        # Future: self.cache = RedisCache()
        self.metrics_log: list[ProviderMetrics] = []

    def _check_cache(self, prompt: str) -> Optional[str]:
        """Placeholder for a cache check (e.g., semantic or exact match)."""
        # Currently disabled/noop
        return None

    def _store_cache(self, prompt: str, response: str) -> None:
        """Placeholder for caching a successful response."""
        # Currently disabled/noop
        pass

    def generate(self, prompt: str, context: ExecutionContext) -> tuple[str, list[ProviderMetrics]]:
        """
        Executes the prompt through the configured provider chain, capturing comprehensive metrics.
        """
        logger.info("Gateway received prompt for execution ID: %s", context.execution_id)

        # 1. Check Cache
        cached_response = self._check_cache(prompt)
        if cached_response:
            logger.info("Cache hit. Serving from cache.")
            metrics = ProviderMetrics(
                execution_id=context.execution_id,
                provider_name="Cache",
                model_name="Cache",
                request_duration_ms=0.0,
                retry_count=0,
                response_size_bytes=len(cached_response),
                success=True,
                provider_outcome="SUCCESS",
                circuit_state="CLOSED",
                cache_status="HIT"
            )
            return cached_response, [metrics]

        # 2. Execute via Provider Chain
        # The chain internally handles failover. However, to capture metrics per provider 
        # attempted, we need to let the ResilientProviderProxy log them, and we can also track 
        # overall gateway success.
        
        # Currently, ResilientProviderProxy logs to the file. We want to capture those logs 
        # or have the proxy return the metrics. Since `generate` returns a string, we will 
        # rely on the proxy emitting structured logs, or we can just capture the outcome here.
        # For full observability, we will track the primary gateway outcome here.
        
        start_time = time.monotonic()
        response_str = ""
        success = False
        error_msg = None
        
        try:
            response_str = self.provider_chain.generate(prompt)
            success = True
            self._store_cache(prompt, response_str)
        except LLMProviderError as e:
            error_msg = str(e)
            logger.error("Gateway execution failed: %s", error_msg)
            raise
        finally:
            duration = (time.monotonic() - start_time) * 1000
            outcome = "SUCCESS" if success else "FAILED"
            
            # Record Gateway-level metrics
            gateway_metrics = ProviderMetrics(
                execution_id=context.execution_id,
                provider_name="Gateway (Chain)",
                model_name="Multiple",
                request_duration_ms=duration,
                retry_count=0,
                response_size_bytes=len(response_str),
                success=success,
                provider_outcome=outcome,
                circuit_state="N/A",
                cache_status="MISS",
                error_type=error_msg
            )
            self.metrics_log.append(gateway_metrics)
            
        return response_str, self.metrics_log
