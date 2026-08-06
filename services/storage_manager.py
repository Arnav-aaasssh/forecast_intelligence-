"""
StorageManager Service
======================

Responsible for persisting all execution artifacts into an immutable 
timestamp-based directory hierarchy.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from config import settings
from models.execution_context import ExecutionContext
from utils.logger import set_execution_id

logger = logging.getLogger("audit")


class StorageManager:
    """
    Manages the lifecycle and persistence of execution artifacts in the storage hierarchy.
    """

    def __init__(self, base_storage_dir: str = "storage/runs"):
        self.base_storage_dir = Path(base_storage_dir)

    def generate_execution_context(self) -> ExecutionContext:
        """
        Creates a new ExecutionContext with a unique UUID-based execution ID
        and prepares the corresponding run directory.
        """
        now = datetime.utcnow()
        short_uuid = str(uuid.uuid4())[:4].upper()
        
        # Format: RUN-YYYYMMDD-HHMMSS-XXXX
        exec_id = f"RUN-{now.strftime('%Y%m%d-%H%M%S')}-{short_uuid}"
        
        # Path: storage/runs/YYYY/MM/DD/RUN-.../
        run_dir = self.base_storage_dir / now.strftime("%Y") / now.strftime("%m") / now.strftime("%d") / exec_id
        
        # Snapshot the current environment settings
        config_snapshot = {
            "APP_VERSION": getattr(settings, "APP_VERSION", "Unknown"),
            "APP_ENVIRONMENT": getattr(settings, "APP_ENVIRONMENT", "Unknown"),
            "PRIMARY_PROVIDER": getattr(settings, "PRIMARY_PROVIDER", "Unknown"),
            "SECONDARY_PROVIDER": getattr(settings, "SECONDARY_PROVIDER", "Unknown"),
            "GEMINI_MODEL": getattr(settings, "GEMINI_MODEL", "Unknown"),
            "COMPANY_MODEL": getattr(settings, "COMPANY_MODEL", "Unknown"),
            "MAX_RETRIES": getattr(settings, "MAX_RETRIES", "Unknown"),
        }
        
        context = ExecutionContext(
            execution_id=exec_id,
            request_id=str(uuid.uuid4()),
            run_directory=run_dir,
            started_at=now,
            config_snapshot=config_snapshot
        )
        
        return context

    def initialize_run_directory(self, context: ExecutionContext) -> None:
        """
        Creates the run directory and writes the initial config snapshot.
        """
        context.run_directory.mkdir(parents=True, exist_ok=True)
        set_execution_id(context.execution_id)
        
        logger.info("Initializing run directory: %s", context.run_directory)
        self.save_json(context, "config_snapshot.json", context.config_snapshot)
        self.save_json(context, "metadata.json", context.as_dict())

    def save_json(self, context: ExecutionContext, filename: str, data: dict[str, Any] | list[Any]) -> Path:
        """
        Persists a JSON file into the run directory.
        """
        file_path = context.run_directory / filename
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, default=str)
            logger.info("Saved artifact: %s", file_path.name)
        except Exception as e:
            logger.error("Failed to save artifact %s: %s", filename, str(e), exc_info=True)
            
        return file_path
        
    def get_run_reports_directory(self, context: ExecutionContext) -> Path:
        """
        Returns the path to the reports sub-directory for this execution, creating it if needed.
        """
        reports_dir = context.run_directory / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir
