"""Centralised configuration for the Forecast Review application."""

from __future__ import annotations

from typing import Any, Final, Mapping

REQUIRED_COLUMNS: Final[tuple[str, ...]] = (
    "Forecast_Name",
    "Model",
    "Family",
    "Fiscal_Year",
    "Week_Ending",
    "Fiscal_Week",
    "Month_Number",
    "Week_Number",
    "Country",
    "Region",
    "SubRegion",
    "Offering",
    "Channel",
    "Forecaster",
    "Planned_ASU",
    "Actual_ASU",
    "Final_Units",
    "Final_Y1",
    "Final_Y2",
    "Final_Y3",
    "Final_Y4",
    "Final_Y5",
    "Final_upp_units",
    "Holiday_Count",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
    "Volume_Category",
    "Manual_Adh",
    "ML_Adh",
    "Manual_±10%",
    "ML_±10%",
    "ML≥Manual_or_±10%",
    "Mean (Hist. Contacts) (Last 1 yr.)",
    "Std Dev (Hist. Contacts)",
    "RISK Cat (w/ Holiday)",
    "RISK Flag (w/ Holiday)",
    "Actual_Offered",
    "Manual_Forecast",
    "Previous_Forecast",
    "ML_Forecast",
)

EXPECTED_DTYPES: Final[Mapping[str, str]] = {
    "Forecast_Name": "String",
    "Model": "String",
    "Family": "String",
    "Fiscal_Year": "Integer",
    "Week_Ending": "Datetime",
    "Fiscal_Week": "Integer",
    "Month_Number": "Integer",
    "Week_Number": "Integer",
    "Country": "String",
    "Region": "String",
    "SubRegion": "String",
    "Offering": "String",
    "Channel": "String",
    "Forecaster": "String",
    "Planned_ASU": "Float",
    "Actual_ASU": "Float",
    "Final_Units": "Float",
    "Final_Y1": "Float",
    "Final_Y2": "Float",
    "Final_Y3": "Float",
    "Final_Y4": "Float",
    "Final_Y5": "Float",
    "Final_upp_units": "Float",
    "Holiday_Count": "Integer",
    "Monday": "Integer",
    "Tuesday": "Integer",
    "Wednesday": "Integer",
    "Thursday": "Integer",
    "Friday": "Integer",
    "Saturday": "Integer",
    "Sunday": "Integer",
    "Volume_Category": "String",
    "Manual_Adh": "Float",
    "ML_Adh": "Float",
    "Manual_±10%": "Boolean",
    "ML_±10%": "Boolean",
    "ML≥Manual_or_±10%": "Boolean",
    "Mean (Hist. Contacts) (Last 1 yr.)": "Float",
    "Std Dev (Hist. Contacts)": "Float",
    "RISK Cat (w/ Holiday)": "String",
    "RISK Flag (w/ Holiday)": "String",
    "Actual_Offered": "Float",
    "Manual_Forecast": "Float",
    "Previous_Forecast": "Float",
    "ML_Forecast": "Float",
}

DEFAULT_VALUES: Final[Mapping[str, Any]] = {"Holiday_Count": 0}

DATASET_REJECTION_FIELDS: Final[tuple[str, ...]] = (
    "Actual_Offered",
    "Manual_Forecast",
    "ML_Forecast",
)

ROW_REJECTION_FIELDS: Final[tuple[str, ...]] = (
    "Previous_Forecast",
    "Mean (Hist. Contacts) (Last 1 yr.)",
    "Std Dev (Hist. Contacts)",
)

NON_EMPTY_FIELDS: Final[tuple[str, ...]] = (
    "Region",
    "Offering",
    "Channel",
    "Forecaster",
)

FORECAST_COLUMNS: Final[tuple[str, ...]] = (
    "Manual_Forecast",
    "ML_Forecast",
    "Previous_Forecast",
)

DUPLICATE_KEY_COLUMNS: Final[tuple[str, ...]] = (
    "Forecast_Name",
    "Fiscal_Year",
    "Fiscal_Week",
    "Country",
    "Region",
    "SubRegion",
    "Offering",
    "Channel",
    "Forecaster",
)

# =========================================================
# Application Configuration
# =========================================================

import os
from dotenv import load_dotenv

load_dotenv()

INPUT_DIRECTORY: Final[str] = "sample_data"
OUTPUT_DIRECTORY: Final[str] = "reports/output"
APP_NAME: Final[str] = "Forecast Review System"
APP_VERSION: Final[str] = "0.9.0"
APP_ENVIRONMENT: Final[str] = os.environ.get("APP_ENVIRONMENT", "development")

REPORT_SCHEMA_VERSION: Final[str] = "1.0"
JSON_REPORT_NAME: Final[str] = "forecast_review.json"

SUPPORTED_EXTENSIONS: Final[tuple[str, ...]] = (".xlsx", ".xls", ".csv")

LOG_LEVEL: Final[str] = "INFO"
LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# =========================================================
# LLM Configuration
# =========================================================

import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER: Final[str] = os.environ.get("LLM_PROVIDER", "gemini")
PRIMARY_PROVIDER: Final[str] = os.environ.get("PRIMARY_PROVIDER", "gemini")
SECONDARY_PROVIDER: Final[str] = os.environ.get("SECONDARY_PROVIDER", "company")

GEMINI_API_KEY: Final[str | None] = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL: Final[str] = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
GEMINI_TEMPERATURE: Final[float] = float(os.environ.get("GEMINI_TEMPERATURE", "0.2"))
GEMINI_MAX_OUTPUT_TOKENS: Final[int] = int(os.environ.get("GEMINI_MAX_OUTPUT_TOKENS", "2048"))
GEMINI_TIMEOUT_SECONDS: Final[int] = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "60"))

# =========================================================
# Company Internal LLM Configuration
# =========================================================

COMPANY_LLM_ENDPOINT: Final[str | None] = os.environ.get("COMPANY_LLM_ENDPOINT")
COMPANY_MODEL: Final[str] = os.environ.get("COMPANY_MODEL", "llama3.1:8b")
COMPANY_TEMPERATURE: Final[float] = float(os.environ.get("COMPANY_TEMPERATURE", "0.25"))
COMPANY_TIMEOUT_SECONDS: Final[int] = int(os.environ.get("COMPANY_TIMEOUT_SECONDS", "120"))

# =========================================================
# Enterprise Resilience Configuration
# =========================================================

MAX_RETRIES: Final[int] = int(os.environ.get("MAX_RETRIES", "3"))
BASE_BACKOFF_SECONDS: Final[float] = float(os.environ.get("BASE_BACKOFF_SECONDS", "2.0"))
MAX_BACKOFF_SECONDS: Final[float] = float(os.environ.get("MAX_BACKOFF_SECONDS", "30.0"))
CIRCUIT_BREAKER_FAILURE_THRESHOLD: Final[int] = int(os.environ.get("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "3"))
CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS: Final[int] = int(os.environ.get("CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS", "30"))
