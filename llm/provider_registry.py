"""
Centralized factory for constructing and wrapping LLM providers with resilience.
"""

import logging
import time
import json
from typing import Optional

from config import settings
from llm.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from llm.llm_provider import BaseLLMProvider, GeminiProvider
from llm.company_provider import CompanyProvider
from llm.provider_chain import ProviderChain
from llm.retry import RetryPolicy
from models.provider_metrics import ProviderMetrics
from utils.logger import _context_filter

logger = logging.getLogger(__name__)


class ResilientProviderProxy(BaseLLMProvider):
    """
    Wraps an underlying provider with Retry, Circuit Breaker, and Metrics collection.
    """

    def __init__(self, provider: BaseLLMProvider):
        super().__init__()
        self.provider = provider
        self.retry_policy = RetryPolicy()
        self.circuit_breaker = CircuitBreaker(provider.provider_name)
        
        # Telemetry for Health Endpoint
        self.total_calls = 0
        self.total_latency_ms = 0.0
        self.last_success: Optional[str] = None
        self.last_failure: Optional[str] = None
        self.total_retries = 0
        
    @property
    def provider_name(self) -> str:
        return self.provider.provider_name
        
    @property
    def model_name(self) -> str:
        return getattr(self.provider, "model_name", "Unknown Model")

    def generate(self, prompt: str) -> str:
        start_time = time.monotonic()
        retry_count = 0
        success = False
        error_type = None
        response_size = 0
        
        try:
            # We wrap the provider.generate call inside the circuit breaker, 
            # and the circuit breaker executes the retry policy.
            
            def execute_with_retries():
                nonlocal retry_count
                res, count = self.retry_policy.execute(lambda: self.provider.generate(prompt), self.provider_name)
                retry_count = count
                return res

            result = self.circuit_breaker.execute(execute_with_retries)
            response_size = len(result)
            success = True
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            # If the circuit breaker opened, it didn't even attempt, so retry count is 0 for that execution
            if isinstance(e, CircuitBreakerOpenError):
                logger.warning("[%s] Skipped execution (Circuit OPEN).", self.provider_name)
            raise
            
        finally:
            duration_ms = (time.monotonic() - start_time) * 1000
            
            outcome = "SUCCESS" if success else "FAILED"
            if error_type == "CircuitBreakerOpenError":
                outcome = "CIRCUIT_OPEN"
                
            metrics = ProviderMetrics(
                execution_id=getattr(_context_filter, "execution_id", "N/A"),
                provider_name=self.provider_name,
                model_name=self.model_name,
                request_duration_ms=duration_ms,
                retry_count=retry_count,
                response_size_bytes=response_size,
                success=success,
                provider_outcome=outcome,
                circuit_state=self.circuit_breaker.state.name,
                error_type=error_type,
            )
            
            # Emit metrics to the dedicated provider log
            logger.info("PROVIDER_METRICS | %s", json.dumps(metrics.as_dict()))
            
            # Update telemetry for health check
            self.total_calls += 1
            self.total_latency_ms += duration_ms
            self.total_retries += retry_count
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            if success:
                self.last_success = now_iso
            else:
                self.last_failure = now_iso

    def get_health_stats(self) -> dict:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "circuit_state": self.circuit_breaker.state.name,
            "average_latency_ms": round(self.total_latency_ms / self.total_calls, 2) if self.total_calls > 0 else 0.0,
            "total_calls": self.total_calls,
            "total_retries": self.total_retries,
            "last_success": self.last_success,
            "last_failure": self.last_failure,
        }


class ProviderRegistry:
    """
    Constructs providers based on configuration and links them into a resilient chain.
    """

    _instances: dict[str, ResilientProviderProxy] = {}

    @classmethod
    def _build_provider(cls, key: str) -> Optional[BaseLLMProvider]:
        key = key.lower().strip()
        
        if key in cls._instances:
            return cls._instances[key]
        
        try:
            if key == "gemini":
                provider = GeminiProvider(
                    api_key=settings.GEMINI_API_KEY or "",
                    model=settings.GEMINI_MODEL,
                    temperature=settings.GEMINI_TEMPERATURE,
                    max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
                    timeout_seconds=settings.GEMINI_TIMEOUT_SECONDS,
                )
                cls._instances[key] = ResilientProviderProxy(provider)
                return cls._instances[key]
                
            elif key == "company":
                provider = CompanyProvider(
                    endpoint=settings.COMPANY_LLM_ENDPOINT or "",
                    model=settings.COMPANY_MODEL,
                    temperature=settings.COMPANY_TEMPERATURE,
                    timeout=settings.COMPANY_TIMEOUT_SECONDS,
                )
                cls._instances[key] = ResilientProviderProxy(provider)
                return cls._instances[key]
                
        except Exception as e:
            logger.error("Failed to construct provider '%s': %s", key, str(e))
            
        return None

    @classmethod
    def build_provider_chain(cls) -> ProviderChain:
        """
        Reads PRIMARY_PROVIDER and SECONDARY_PROVIDER from settings, constructs them,
        wraps them in resilience proxies, and returns the chain.
        """
        providers = []
        
        # Primary
        primary_key = settings.PRIMARY_PROVIDER
        if primary_key:
            primary = cls._build_provider(primary_key)
            if primary:
                providers.append(primary)
                
        # Secondary
        secondary_key = settings.SECONDARY_PROVIDER
        if secondary_key and secondary_key != primary_key:
            secondary = cls._build_provider(secondary_key)
            if secondary:
                providers.append(secondary)
                
        if not providers:
            raise ValueError("ProviderRegistry could not successfully construct any configured providers.")
            
        return ProviderChain(providers)

    @classmethod
    def get_registry_health(cls) -> dict[str, dict]:
        """Returns the health stats for all memoized providers."""
        return {
            key: proxy.get_health_stats() 
            for key, proxy in cls._instances.items()
        }
