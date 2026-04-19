"""
Central configuration for the Gmail AI Agent.
Keep all project-wide constants here.
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = DATA_DIR / "reports"
MEMORY_FILE = DATA_DIR / "memory.json"

# Gmail scan settings
INITIAL_EMAIL_FETCH_COUNT = 50  # first-run safety limit
MAX_EMAILS_PER_RUN = 500
SCAN_SIZE_OPTIONS = [50, 100, 250, 500]
MAX_LLM_EMAILS_PER_RUN = 15

# Safety controls
DELETE_MODE = "trash"  # only trash, never permanent delete
SAFE_CATEGORIES = ["bank", "job", "utility", "personal"]
USE_LLM = True

# Classification labels
VALID_CATEGORIES = [
    "self",
    "promotions",
    "bank",
    "job",
    "utility",
    "personal",
    "AMBIGUOUS",
]

# Report filenames
SUMMARY_REPORT_FILE = REPORTS_DIR / "summary_report.csv"
DETAILED_REPORT_FILE = REPORTS_DIR / "detailed_report.xlsx"
DETAILED_REPORT_CSV_FILE = REPORTS_DIR / "detailed_report.csv"

# Gemini settings
GEMINI_MODEL = "gemini-1.5-flash"

# Logging
LOG_FILE = DATA_DIR / "agent.log"