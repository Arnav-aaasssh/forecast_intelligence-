import os
import logging
import sys
from unittest.mock import patch, MagicMock

# Force environment variables for testing
os.environ["PRIMARY_PROVIDER"] = "gemini"
os.environ["SECONDARY_PROVIDER"] = "company"
os.environ["MAX_RETRIES"] = "3"
os.environ["BASE_BACKOFF_SECONDS"] = "0.01" # Fast backoff for tests
os.environ["MAX_BACKOFF_SECONDS"] = "0.1"
os.environ["CIRCUIT_BREAKER_FAILURE_THRESHOLD"] = "3"
os.environ["COMPANY_LLM_ENDPOINT"] = "http://fake-company-endpoint/api/generate"

from llm.llm_provider import LLMNetworkError, LLMProviderError
from llm.provider_registry import ProviderRegistry

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger("Test")

def run_scenarios():
    print("="*60)
    print("SCENARIO 1: Gemini Healthy")
    print("="*60)
    
    chain = ProviderRegistry.build_provider_chain()
    
    # Mock Gemini to succeed
    with patch("llm.llm_provider.GeminiProvider.generate", return_value='{"schema_version": "1.0", "summaries": {"executive_summary": "12345678901234567890", "manager_summary": "12345678901234567890", "email_summary": "12345678901234567890", "teams_summary": "12345678901234567890"}}'):
        res = chain.generate("test prompt")
        logger.info("Final Result: %s", res)

    print("\n" + "="*60)
    print("SCENARIO 2: Gemini fails with 503 (Network Error), Retries, then Failover to Company")
    print("="*60)
    
    chain = ProviderRegistry.build_provider_chain()
    
    with patch("llm.llm_provider.GeminiProvider.generate", side_effect=LLMNetworkError("503 Service Unavailable")):
        with patch("llm.company_provider.CompanyProvider.generate", return_value="Company Success JSON"):
            res = chain.generate("test prompt")
            logger.info("Final Result: %s", res)
            
    print("\n" + "="*60)
    print("SCENARIO 3: Total Outage (Gemini and Company both fail)")
    print("="*60)
    
    chain = ProviderRegistry.build_provider_chain()
    
    with patch("llm.llm_provider.GeminiProvider.generate", side_effect=LLMNetworkError("503 Gemini Down")):
        with patch("llm.company_provider.CompanyProvider.generate", side_effect=LLMNetworkError("503 Company Down")):
            try:
                chain.generate("test prompt")
            except Exception as e:
                logger.info("Exception correctly raised: %s", type(e).__name__)

    print("\n" + "="*60)
    print("SCENARIO 4: Gemini Circuit Already Open")
    print("="*60)
    
    chain = ProviderRegistry.build_provider_chain()
    # Force Gemini circuit open
    gemini_proxy = chain.providers[0]
    gemini_proxy.circuit_breaker.state = __import__("llm.circuit_breaker", fromlist=["CircuitState"]).CircuitState.OPEN
    
    with patch("llm.company_provider.CompanyProvider.generate", return_value="Instant Company Success"):
        res = chain.generate("test prompt")
        logger.info("Final Result: %s", res)

if __name__ == "__main__":
    run_scenarios()
