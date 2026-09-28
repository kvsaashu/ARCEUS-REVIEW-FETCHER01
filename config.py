import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "arceus_reviews.db"

# Server Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "5000"))

# Default Fetch Configuration
DEFAULT_COUNTRY = "in"
DEFAULT_LANG = "en"
BATCH_SIZE = 20
MAX_FETCH_SCAN = 1500  # maximum reviews scanned per run

# Integrations (Can be set via UI or environment variables)
GOOGLE_SHEET_WEBHOOK_URL = os.getenv("GOOGLE_SHEET_WEBHOOK_URL", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8630641097:AAHs7YiHtjiCmMvy3uOdEcfM5fe8Sz-OFSU")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7417323395")

# Auto-Fetch Interval (in minutes)
DEFAULT_AUTOFETCH_INTERVAL = 5

