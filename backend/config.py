# config.py
# Central configuration: database connection, API keys, and Tamil Nadu domain data.

import os
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db(cursor_factory=None):
    import psycopg2

    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=cursor_factory)

    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=os.getenv("PG_PORT", "5432"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", ""),
        dbname=os.getenv("PG_DATABASE", "commodity_intelligence"),
        cursor_factory=cursor_factory,
    )


# ---------------------------------------------------------------------------
# External API keys and base URLs
# ---------------------------------------------------------------------------

AGMARKNET_API_KEY  = os.getenv("AGMARKNET_API_KEY")
AGMARKNET_BASE_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"

GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL    = "gemini-2.5-flash"

OPENWEATHER_API_KEY  = os.getenv("OPENWEATHER_API_KEY")
WEATHER_BASE_URL     = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


# ---------------------------------------------------------------------------
# Load Tamil Nadu master domain data from metadata.json
# ---------------------------------------------------------------------------

import json

_metadata_path = os.path.join(os.path.dirname(__file__), "metadata.json")
with open(_metadata_path, "r", encoding="utf-8") as _f:
    _metadata = json.load(_f)

TN_DISTRICTS   = _metadata["districts"]
TN_COMMODITIES = _metadata["commodities"]
TN_FESTIVALS   = _metadata["festivals"]
TN_HARVEST     = _metadata["harvest"]
WEATHER_IMPACT = _metadata["weather_impact"]
TN_COMMODITY_CATEGORIES = _metadata.get("commodity_categories", {})
TN_COMMODITY_READABLE_NAMES = _metadata.get("commodity_readable_names", {})

