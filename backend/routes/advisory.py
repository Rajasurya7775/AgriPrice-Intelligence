import os
import requests
from psycopg2.extras import RealDictCursor
from datetime import datetime
from flask import Blueprint, request, jsonify

try:
    from backend.config import GEMINI_API_KEY, GEMINI_MODEL, TN_HARVEST, TN_FESTIVALS, get_db
except ImportError:
    from config import GEMINI_API_KEY, GEMINI_MODEL, TN_HARVEST, TN_FESTIVALS, get_db

advisory_bp = Blueprint("advisory", __name__)

_GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models"
    f"/{GEMINI_MODEL}:generateContent"
)


def _load_sql(filename: str) -> str:
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", filename)
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def _get_conn():
    return get_db(cursor_factory=RealDictCursor)


def _normalise(s: str) -> str:
    return s.lower().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")


def _harvest_description(commodity: str) -> str:
    c_key = _normalise(commodity)
    for crop_name, schedule in TN_HARVEST.items():
        if _normalise(crop_name) in c_key or c_key in _normalise(crop_name):
            month = datetime.today().month
            if month in schedule.get("peak_months", []):
                return (
                    f"Peak harvest season for {commodity} in Tamil Nadu. "
                    "Mandi arrivals are high, which may exert downward pressure on prices."
                )
            if month in schedule.get("lean_months", []):
                return (
                    f"Lean harvest season for {commodity} in Tamil Nadu. "
                    "Arrivals are low, which typically drives prices upward."
                )
            return f"Off-peak/normal harvest season for {commodity}."
    return f"Regular cropping season for {commodity}."


def _festival_description() -> str:
    today = datetime.today().date()
    upcoming = []

    for fest in TN_FESTIVALS:
        date_val = fest.get("date", "")
        if not date_val or date_val == "VARIES":
            continue

        try:
            m_str, d_str = date_val.split("-")
            m, d = int(m_str), int(d_str)
            # Parse festival date for current year
            fest_date = datetime(year=datetime.today().year, month=m, day=d).date()
            
            # Check within next 3 days
            diff = (fest_date - today).days
            if diff < -180:
                fest_date = datetime(year=datetime.today().year + 1, month=m, day=d).date()
                diff = (fest_date - today).days
            
            if 0 <= diff <= 3:
                upcoming.append(fest)
        except Exception:
            continue

    if not upcoming:
        return "No major upcoming festivals or holidays in Tamil Nadu within the next 3 days."

    names = [f["name"] for f in upcoming]
    desc = f"Upcoming festivals/holidays in the next 3 days: {', '.join(names)}."
    if any(f.get("demand") in ("VERY_HIGH", "HIGH") for f in upcoming):
        desc += " This will significantly increase market demand and cause price volatility."
    return desc


_ROLE_FOCUS = {
    "farmer"  : "Focus on: whether to sell now or wait, harvest timing, storage advice, weather impact, and expected price direction.",
    "trader"  : "Focus on: buying opportunity, selling window, best markets for arbitrage, and profit margin outlook.",
    "consumer": "Focus on: best time to buy, expected price direction, and nearby lower-price markets.",
}

_LANG_INSTRUCTION = {
    "ta": (
        "IMPORTANT: Write the entire advisory in natural, grammatically correct Tamil (தமிழ்). "
        "Use actual Tamil terminology — do NOT transliterate English into Tamil script."
    ),
    "en": "IMPORTANT: Write the advisory in clear, natural English.",
}


def _build_prompt(
    commodity:    str,
    district:     str,
    role:         str,
    language:     str,
    db_miss:      bool,
    db_prices:    list,
    tn_stats:     dict,
    weather:      dict,
    harvest_desc: str,
    festival_desc: str,
) -> str:
    role_instruction = _ROLE_FOCUS.get(role, "Provide a practical agricultural price advisory.")
    lang_instruction = _LANG_INSTRUCTION.get(language, _LANG_INSTRUCTION["en"])

    weather_desc = "Not available."
    if weather and weather.get("current"):
        c = weather["current"]
        weather_desc = (
            f"Temperature {c.get('temp', 'N/A')}°C, "
            f"Condition: {c.get('condition', 'N/A')}, "
            f"Humidity: {c.get('humidity', 'N/A')}%, "
            f"Rain probability: {c.get('rain_prob', 'N/A')}%."
        )

    if db_miss:
        return f"""You are an expert Agricultural Market Advisor for Tamil Nadu, India.
Our database has no live price records for {commodity} in {district} district.

TASK:
1. Search the web for the latest mandi price and trend of {commodity} in {district}, Tamil Nadu.
2. Write a personalised advisory for a {role}.
3. Incorporate: Weather: {weather_desc} | Harvest: {harvest_desc} | Calendar: {festival_desc}
4. {role_instruction}

{lang_instruction}
Write exactly 4 to 5 short, simple, and easily understandable sentences in English. Do not use complex jargon. Keep it direct and practical for a farmer, trader, or consumer. No bullet points, headings, or markdown. Return plain text only."""

    latest        = db_prices[0] if db_prices else {}
    modal_q       = latest.get("modal_price", 0)
    modal_kg      = round(float(modal_q) / 100, 2) if modal_q else 0
    high_price    = tn_stats.get("highest_price", 0)
    low_price     = tn_stats.get("lowest_price", 0)
    avg_price     = tn_stats.get("avg_price", 0)

    return f"""You are an expert Agricultural Market Advisor for Tamil Nadu, India.
Here is verified market data for {commodity} in {district} district:

Price Data:
  Market      : {latest.get("market", "N/A")}
  Modal Price  : ₹{modal_q}/Quintal  (₹{modal_kg}/Kg)
  Range        : ₹{latest.get("min_price", 0)} – ₹{latest.get("max_price", 0)} per Quintal
  Trend        : {latest.get("trend_analysis", "Stable")} ({latest.get("trend_strength", "Moderate")} strength)

Tamil Nadu State Comparison:
  Highest : {tn_stats.get("highest_market", "N/A")} at ₹{high_price}/Quintal (₹{round(float(high_price)/100,2)}/Kg)
  Lowest  : {tn_stats.get("lowest_market",  "N/A")} at ₹{low_price}/Quintal  (₹{round(float(low_price)/100,2)}/Kg)
  Average : ₹{avg_price}/Quintal (₹{round(float(avg_price)/100,2)}/Kg)

Local Context:
  Weather  : {weather_desc}
  Harvest  : {harvest_desc}
  Calendar : {festival_desc}

TASK:
1. Write a personalised advisory for a {role}.
2. Integrate price trend, state-wide comparison, weather, harvest season, and upcoming festivals.
3. {role_instruction}

{lang_instruction}
Write exactly 4 to 5 short, simple, and easily understandable sentences in English. Do not use complex jargon. Keep it direct and practical for a farmer, trader, or consumer. No bullet points, headings, or markdown. Return plain text only.
The main highlight thing is suggestion for the {role} based on the above data and context.
Avoid generic statements; provide actionable advice. BUY/SELL/WAIT/STORE recommendation should be clear and specific.
Avoid vague statements like prices may rise or consider selling."""


@advisory_bp.route("/api/advisory", methods=["POST"])
def get_advisory():
    if not GEMINI_API_KEY:
        return jsonify({"advisory": "Advisory unavailable."}), 200

    body      = request.get_json(silent=True) or {}
    commodity = body.get("commodity", "").strip()
    district  = body.get("district",  "").strip()
    role      = body.get("role",      "farmer").lower()
    language  = body.get("language",  "en").lower()
    weather   = body.get("weather",   {})

    if not commodity or not district:
        return jsonify({"error": "commodity and district are required"}), 400

    db_prices     = []
    all_tn_prices = []
    db_miss       = True

    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(_load_sql("advisory_local_prices.sql"), (commodity, district))
            db_prices = [dict(r) for r in cur.fetchall()]
            db_miss   = len(db_prices) == 0

            cur.execute(_load_sql("advisory_state_prices.sql"), (commodity,))
            all_tn_prices = [dict(r) for r in cur.fetchall()]

    except Exception as exc:
        print(f"Database error: {exc}")
    finally:
        if conn:
            conn.close()

    tn_stats = {}
    if all_tn_prices:
        hi  = max(all_tn_prices, key=lambda x: float(x["modal_price"] or 0))
        lo  = min(all_tn_prices, key=lambda x: float(x["modal_price"] or 0))
        avg = sum(float(x["modal_price"] or 0) for x in all_tn_prices) / len(all_tn_prices)
        tn_stats = {
            "highest_price"  : hi["modal_price"],
            "highest_market" : f"{hi['market']} ({hi['district']})",
            "lowest_price"   : lo["modal_price"],
            "lowest_market"  : f"{lo['market']} ({lo['district']})",
            "avg_price"      : round(avg, 2),
        }

    harvest_desc  = _harvest_description(commodity)
    festival_desc = _festival_description()

    try:
        prompt  = _build_prompt(
            commodity, district, role, language,
            db_miss, db_prices, tn_stats, weather,
            harvest_desc, festival_desc,
        )
        payload = {
            "contents"       : [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": 3000, "temperature": 0.4},
        }
        if db_miss:
            payload["tools"] = [{"google_search": {}}]

        res = requests.post(
            _GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        res.raise_for_status()
        advisory_text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        return jsonify({
            "advisory"     : advisory_text,
            "db_miss"      : db_miss,
            "harvest_desc" : harvest_desc,
            "festival_desc": festival_desc,
        })

    except Exception as exc:
        fallback = (
            "Could not generate advisory. Please verify prices in nearby mandis."
            if language == "en"
            else "ஆலோசனை உருவாக்க முடியவில்லை. அருகிலுள்ள சந்தை விலைகளை சரிபார்க்கவும்."
        )
        return jsonify({
            "advisory"     : f"{fallback} (Error: {exc})",
            "db_miss"      : db_miss,
            "harvest_desc" : harvest_desc,
            "festival_desc": festival_desc,
        }), 200
