"""
Enterprise Logging Module for the Forecast Review System.
Configures split log streams for application, provider, analytics, api, and audit logs.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from config import settings


class ExecutionContextFilter(logging.Filter):
    """
    Injects the active execution_id into log records.
    """
    def __init__(self):
        super().__init__()
        self.execution_id = "N/A"

    def filter(self, record: logging.LogRecord) -> bool:
        record.execution_id = getattr(self, "execution_id", "N/A")
        return True

_context_filter = ExecutionContextFilter()

def set_execution_id(execution_id: str) -> None:
    """Sets the execution ID for all subsequent log entries on this thread/process."""
    _context_filter.execution_id = execution_id


def configure_enterprise_logging() -> None:
    """
    Sets up the logging infrastructure, splitting streams into appropriate files.
    """
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Base formatter that includes execution_id
    base_format = "%(asctime)s | %(levelname)-8s | EXEC:%(execution_id)s | %(name)s | %(message)s"
    formatter = logging.Formatter(base_format, datefmt=settings.LOG_DATE_FORMAT)

    # Root Logger Configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    
    # Remove existing handlers to prevent duplicates during testing/reloads
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    # Console Handler (Stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(_context_filter)
    root_logger.addHandler(console_handler)

    # Helper function to create file handlers
    def create_file_handler(filename: str) -> logging.FileHandler:
        fh = logging.FileHandler(log_dir / filename)
        fh.setFormatter(formatter)
        fh.addFilter(_context_filter)
        return fh

    # 1. Application Log (Catch-all)
    app_handler = create_file_handler("application.log")
    root_logger.addHandler(app_handler)

    # 2. Provider Log (Targeted to LLM/Provider modules)
    provider_logger = logging.getLogger("llm")
    provider_logger.propagate = False
    provider_logger.setLevel(logging.INFO)
    provider_handler = create_file_handler("provider.log")
    provider_logger.addHandler(provider_handler)
    provider_logger.addHandler(console_handler)

    # 3. Analytics Log (Targeted to analytics and review engine)
    analytics_logger = logging.getLogger("analytics")
    analytics_logger.propagate = False
    analytics_logger.setLevel(logging.INFO)
    analytics_handler = create_file_handler("analytics.log")
    analytics_logger.addHandler(analytics_handler)
    analytics_logger.addHandler(console_handler)
    
    engine_logger = logging.getLogger("services.review_engine")
    engine_logger.propagate = False
    engine_logger.setLevel(logging.INFO)
    engine_logger.addHandler(analytics_handler)
    engine_logger.addHandler(console_handler)

    # 4. API Log (Targeted to FastAPI/web interactions)
    api_logger = logging.getLogger("api")
    api_logger.propagate = False
    api_logger.setLevel(logging.INFO)
    api_handler = create_file_handler("api.log")
    api_logger.addHandler(api_handler)
    api_logger.addHandler(console_handler)

    # 5. Audit Log (Targeted to core lifecycle events, storage persistence, trace events)
    audit_logger = logging.getLogger("audit")
    audit_logger.propagate = False
    audit_logger.setLevel(logging.INFO)
    audit_handler = create_file_handler("audit.log")
    audit_logger.addHandler(audit_handler)
    audit_logger.addHandler(console_handler)

    audit_logger.info("Enterprise logging configured successfully.")
