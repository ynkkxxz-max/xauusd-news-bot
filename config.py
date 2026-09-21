import os
from pathlib import Path
from dotenv import load_dotenv
import pytz

# Base Directory
BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Telegram Settings
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# Mode settings
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "false").lower() in ("true", "1", "yes")

# Gemini AI settings (used for natural-language Khmer market analysis)
# NOTE: Never commit your real key. Set GEMINI_API_KEY in the .env file only.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
# If true, use Gemini for analysis; otherwise fall back to the rule-based MacroAnalyzer.
USE_GEMINI = os.getenv("USE_GEMINI", "true").lower() in ("true", "1", "yes")

# Gemini throttling — protects the free-tier quota from HTTP 429 bursts.
# GEMINI_MIN_INTERVAL: minimum seconds between any two Gemini calls (spaces out
#   the many news items processed in one cycle so we stay under the RPM limit).
# GEMINI_COOLDOWN: when the quota is exhausted (HTTP 429), stop calling Gemini
#   for this many seconds and use the rule-based fallback instead of hammering
#   an already-exhausted quota with useless retries.
GEMINI_MIN_INTERVAL = float(os.getenv("GEMINI_MIN_INTERVAL", "20"))
GEMINI_COOLDOWN = float(os.getenv("GEMINI_COOLDOWN", "900"))

# Minimum seconds between two breaking-news alerts (user spec: 1 alert per 2 hours).
# Extra gold-relevant items arriving inside the window are held, not dropped.
BREAKING_ALERT_MIN_GAP = float(os.getenv("BREAKING_ALERT_MIN_GAP", "7200"))

# Timezone (Cambodia Time UTC+7)
CAMBODIA_TZ_NAME = os.getenv("TIMEZONE", "Asia/Phnom_Penh")
CAMBODIA_TZ = pytz.timezone(CAMBODIA_TZ_NAME)

# Daily Gold Price Alert Schedule (Cambodia Time)
DAILY_PRICE_ALERT_HOUR = int(os.getenv("DAILY_PRICE_ALERT_HOUR", "7"))
DAILY_PRICE_ALERT_MINUTE = int(os.getenv("DAILY_PRICE_ALERT_MINUTE", "0"))

# Database Path
DB_PATH = BASE_DIR / "data.db"

# -------------------------------------------------------------
# Cambodian Gold Weight Standard Conversion Constants
# -------------------------------------------------------------
# 1 Troy Ounce = 31.1034768 grams
# 1 តម្លឹង (Damlung / Tael) = 37.5 grams
# 1 ជី (Chi) = 3.75 grams (1/10 of Damlung)
# 1 ហ៊ុន (Hun) = 0.375 grams (1/10 of Chi)
#
# Formula:
# Price per gram = Price_per_oz / 31.1034768
# 1 Damlung = Price per gram * 37.5 = Price_per_oz * (37.5 / 31.1034768)
# Gram ratio: 37.5 / 31.1034768 ≈ 1.20565297
GRAMS_PER_TROY_OUNCE = 31.1034768
GRAMS_PER_DAMLUNG = 37.5
DAMLUNG_TO_OZ_RATIO = GRAMS_PER_DAMLUNG / GRAMS_PER_TROY_OUNCE

# Monitoring Interval timings (in seconds)
INTERVAL_NORMAL = 60 * 60     # Mode 1: 1 hour normal checks
INTERVAL_UPCOMING = 60 * 2     # Mode 2: 2 minutes when high-impact event is within 30m
INTERVAL_HIGH_IMPACT = 30      # Mode 3: 30 seconds when within 5 mins or waiting for actual data
