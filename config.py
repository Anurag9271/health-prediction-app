"""Central configuration. Secrets are read from environment variables / .env only."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "patients.db"))

# External AI API (Google Gemini). The key is NEVER hard-coded.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
AI_TIMEOUT_SECONDS = 60

# Accepted ranges for blood-test values (sanity limits, not diagnostic limits)
RANGES = {
    "glucose": (20.0, 800.0),        # mg/dL
    "haemoglobin": (3.0, 25.0),      # g/dL
    "cholesterol": (50.0, 600.0),    # mg/dL
}
MAX_AGE_YEARS = 120
DATE_FORMAT = "%d/%m/%Y"
