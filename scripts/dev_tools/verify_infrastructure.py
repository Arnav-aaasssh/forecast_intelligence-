import os
import logging
import json
from unittest.mock import patch

# Force environment variables for testing
os.environ["PRIMARY_PROVIDER"] = "company"
os.environ["SECONDARY_PROVIDER"] = "gemini"
os.environ["MAX_RETRIES"] = "3"
os.environ["BASE_BACKOFF_SECONDS"] = "0.01" # Fast backoff for tests
os.environ["MAX_BACKOFF_SECONDS"] = "0.1"
os.environ["CIRCUIT_BREAKER_FAILURE_THRESHOLD"] = "3"
os.environ["COMPANY_LLM_ENDPOINT"] = "http://fake-company-endpoint/api/generate"

from llm.llm_provider import LLMNetworkError, LLMProviderError, LLMParseError
from llm.provider_registry import ProviderRegistry
from llm.gateway import LLMGateway
from models.execution_context import ExecutionContext
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger("Test")

def run_scenarios():
    context = ExecutionContext(execution_id="RUN-TEST", request_id="TEST-REQ", run_directory=Path("/tmp"))
    
    print("="*80)
    print("SCENARIO 1: Primary Provider Healthy (Company)")
    print("="*80)
    
    chain = ProviderRegistry.build_provider_chain()
    gateway = LLMGateway(chain)
    
    valid_json = '{"schema_version": "1.0", "summaries": {"executive_summary": "Exec", "manager_summary": "Mgr", "email_summary": "Email", "teams_summary": "Teams"}}'
    
    with patch("llm.company_provider.CompanyProvider.generate", return_value=valid_json):
        res, metrics = gateway.generate("test prompt", context)
        logger.info("Result Success. Active Provider Metrics: %s", json.dumps([m.as_dict() for m in metrics]))
        logger.info("Health Stats: %s", json.dumps(ProviderRegistry.get_registry_health(), indent=2))

    print("\n" + "="*80)
    print("SCENARIO 2: Primary Timeout -> Retries -> Failover to Secondary (Gemini)")
    print("="*80)
    
    with patch("llm.company_provider.CompanyProvider.generate", side_effect=LLMNetworkError("Timeout during request")):
        with patch("llm.llm_provider.GeminiProvider.generate", return_value=valid_json):
            res, metrics = gateway.generate("test prompt", context)
            logger.info("Result Success on Failover. Metrics: %s", json.dumps([m.as_dict() for m in metrics]))
            logger.info("Health Stats: %s", json.dumps(ProviderRegistry.get_registry_health(), indent=2))
            
    print("\n" + "="*80)
    print("SCENARIO 3: Malformed JSON from Primary -> Failover to Secondary")
    print("="*80)
    
    # We simulate parse error by throwing it explicitly or letting the ResponseCleaner fail
    # Gateway doesn't parse JSON, the LLMService does. So this scenario is better tested at LLMService level.
    from llm.llm_service import LLMService
    from llm.prompt_builder import PromptBuilder
    from models.review_models import ReviewResult
    import pandas as pd
    from models.review_models import PipelineMetadata
    
    rr = ReviewResult(
        dataframe=pd.DataFrame(),
        validation_summary={}, performance_summary={}, comparison_summary={},
        drift_summary={}, risk_summary={}, insight_summary={}, recommendation_summary={},
        top_recommendations=[],
        pipeline_metadata=PipelineMetadata(rows_processed=0, pipeline_status="SUCCESS", execution_timestamp=pd.Timestamp.now())
    )
    pb = PromptBuilder(rr)
    llm_service = LLMService(pb, gateway)
    
    with patch("llm.company_provider.CompanyProvider.generate", return_value="THIS IS NOT JSON"):
        with patch("llm.llm_provider.GeminiProvider.generate", return_value=valid_json):
            try:
                bundle = llm_service.generate_all_summaries(context)
                logger.info("Successfully recovered from Malformed JSON using failover!")
            except Exception as e:
                logger.info("If the chain doesn't catch parse errors (because it just returns text), the LLMService will fail: %s", e)
                # Since the provider just returns string, it doesn't know it's bad JSON. 
                # LLMService tries to parse it and fails. 

if __name__ == "__main__":
    run_scenarios()
