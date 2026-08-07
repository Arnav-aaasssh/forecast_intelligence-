import os
import json
import logging
from pathlib import Path
from fastapi.testclient import TestClient

# Must set before importing app
os.environ["PRIMARY_PROVIDER"] = "company"
os.environ["SECONDARY_PROVIDER"] = "gemini"
os.environ["COMPANY_LLM_ENDPOINT"] = "http://fake-company-endpoint/api/generate"

from api.app import app
from llm.provider_registry import ProviderRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IVV")

client = TestClient(app)

def run_audit():
    logger.info("=== Phase 7: FastAPI Health Check ===")
    response = client.get("/health")
    logger.info("Health Status: %d", response.status_code)
    logger.info("Health Payload: %s", json.dumps(response.json(), indent=2))
    
    logger.info("=== Phase 2 & 5: Pipeline & Analytics E2E ===")
    sample_path = Path("sample_data/FinalForecast_Imputed.xlsx")
    if not sample_path.exists():
        logger.error("Sample dataset not found!")
        return

    # To avoid actual LLM calls blocking or returning nonsense in the audit,
    # we will mock the provider chain in the registry.
    from unittest.mock import patch
    
    valid_json = '{"schema_version": "1.0", "summaries": {"executive_summary": "IVV Exec", "manager_summary": "IVV Mgr", "email_summary": "IVV Email", "teams_summary": "IVV Teams"}}'
    
    with patch("llm.company_provider.CompanyProvider.generate", return_value=valid_json):
        with open(sample_path, "rb") as f:
            logger.info("Uploading dataset to /review endpoint...")
            response = client.post("/review", files={"file": ("FinalForecast_Imputed.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
            
        logger.info("Review Status: %d", response.status_code)
        if response.status_code == 200:
            payload = response.json()
            logger.info("Pipeline Status: %s", payload["pipeline"]["status"])
            logger.info("Validation Errors: %d", payload["validation"]["errors"])
            logger.info("Artifacts Dir: %s", payload["artifacts"]["directory"])
            
            # Print analytics subsets to verify business logic
            logger.info("Performance: %s", json.dumps(payload["performance"], indent=2)[:500])
            logger.info("Risk: %s", json.dumps(payload["risk"], indent=2)[:500])
            logger.info("Recommendations Count: %d", len(payload["recommendations"]["actions"]))
        else:
            logger.error("Review Failed: %s", response.text)

    logger.info("=== Failure Injection Matrix ===")
    # Bad extension
    with open(sample_path, "rb") as f:
        res = client.post("/review", files={"file": ("test.txt", f, "text/plain")})
        logger.info("Bad Extension Status: %d, Response: %s", res.status_code, res.text)
        
    # Empty file
    res = client.post("/review", files={"file": ("empty.xlsx", b"", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    logger.info("Empty File Status: %d, Response: %s", res.status_code, res.text)

if __name__ == "__main__":
    run_audit()
