import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Auto-Fetch Interval (in minutes)
DEFAULT_AUTOFETCH_INTERVAL = 5

