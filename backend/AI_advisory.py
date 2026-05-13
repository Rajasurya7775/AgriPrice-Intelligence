# ============================================================
#   Daily Commodity Price Intelligence Tool
#   ai_advisory.py — Gemini AI Advisory Generator
#   Weather: 3 day forecast from OpenWeatherMap
# ============================================================

import requests
from backend.config import (
    GEMINI_API_KEY, GEMINI_MODEL,
    OPENWEATHER_API_KEY, WEATHER_FORECAST_URL,
    WEATHER_IMPACT, TN_DISTRICTS
)

# ─────────────────────────────────────────
#  STEP 1 — GET 3 DAY WEATHER FORECAST
# ─────────────────────────────────────────
def get_3day_weather(district):
    try:
        coords = None
        for key in TN_DISTRICTS:
            if key.lower() in district.lower() or district.lower() in key.lower():
                coords = TN_DISTRICTS[key]
                break

        if not coords:
            return None

        params = {
            "lat"  : coords["lat"],
            "lon"  : coords["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
            "cnt"  : 24
        }

        response = requests.get(WEATHER_FORECAST_URL, params=params, timeout=10)

        if response.status_code != 200:
            return None

        data     = response.json()
        forecast = data.get("list", [])

        if not forecast:
            return None

        daily = {}

        for slot in forecast:
            date = slot["dt_txt"].split(" ")[0]

            if date not in daily:
                daily[date] = {
                    "date"       : date,
                    "temps"      : [],
                    "humidity"   : [],
                    "rainfall_mm": 0.0,
                    "conditions" : [],
                    "alerts"     : []
                }

            daily[date]["temps"].append(slot["main"]["temp"])
            daily[date]["humidity"].append(slot["main"]["humidity"])
            daily[date]["conditions"].append(slot["weather"][0]["main"])

            if "rain" in slot:
                daily[date]["rainfall_mm"] += slot["rain"].get("3h", 0.0)

        result = []
        for date, d in sorted(daily.items())[:3]:

            avg_temp     = round(sum(d["temps"])    / len(d["temps"]),    1)
            avg_humidity = round(sum(d["humidity"]) / len(d["humidity"]), 1)
            rainfall     = round(d["rainfall_mm"], 2)
            condition    = max(set(d["conditions"]), key=d["conditions"].count)

            alerts = []
            if rainfall > WEATHER_IMPACT["heavy_rain_mm"]:
                alerts.append(f"Heavy Rain ({rainfall}mm) → Supply disruption likely")
            if avg_temp > WEATHER_IMPACT["extreme_heat_c"]:
                alerts.append(f"Extreme Heat ({avg_temp}°C) → Crop damage risk")
            if avg_humidity > WEATHER_IMPACT["high_humidity_pct"]:
                alerts.append(f"High Humidity ({avg_humidity}%) → Storage issues")

            result.append({
                "date"        : date,
                "avg_temp"    : avg_temp,
                "avg_humidity": avg_humidity,
                "rainfall_mm" : rainfall,
                "condition"   : condition,
                "alerts"      : alerts
            })

        return result

    except Exception as e:
        print(f"  ⚠️  Weather fetch failed: {e}")
        return None


# ─────────────────────────────────────────
#  STEP 2 — BUILD GEMINI PROMPT
# ─────────────────────────────────────────
def build_prompt(prediction_data, weather_3day):

    user_type   = prediction_data["user_type"]
    district    = prediction_data["district"]
    commodity   = prediction_data["commodity"]
    prices      = prediction_data["prices"]
    dates       = prediction_data["dates"]
    weekly_avg  = prediction_data["weekly_avg"]
    today_price = prediction_data["today_price"]
    last_date   = prediction_data["last_date"]
    trend       = prediction_data["trend"]
    tomorrow    = prediction_data["tomorrow"]
    day_after   = prediction_data["day_after"]
    confidence  = prediction_data["confidence"]
    harvest     = prediction_data["harvest_status"]
    festivals   = prediction_data["upcoming_festivals"]
    signal      = prediction_data["signal"]
    markets     = prediction_data["markets"]

    # ── Price history string ──
    price_history = ""
    for date, price in zip(dates, prices):
        price_history += f"  {date}: ₹{price}/quintal\n"

    # ── Market string ──
    market_info = ""
    if markets:
        for m in markets[:3]:
            market_info += f"  {m['market']}: ₹{m['avg_price']}\n"

    # ── 3 Day weather string ──
    weather_info = "Weather data unavailable"
    if weather_3day:
        weather_info = ""
        labels = ["Today", "Tomorrow", "Day After"]
        for i, day in enumerate(weather_3day):
            label     = labels[i] if i < len(labels) else day["date"]
            rain_str  = f" | 🌧️ Rain: {day['rainfall_mm']}mm" if day["rainfall_mm"] > 0 else ""
            alert_str = f" ⚠️ {', '.join(day['alerts'])}" if day["alerts"] else ""
            weather_info += f"  {label} ({day['date']}): {day['condition']} | {day['avg_temp']}°C | Humidity: {day['avg_humidity']}%{rain_str}{alert_str}\n"

    # ── Festival string ──
    festival_info = "No upcoming festivals in next 3 days"
    if festivals:
        festival_info = ""
        for f in festivals:
            festival_info += f"  {f['name']} in {f['days_until']} day(s) — Demand: {f['demand']}\n"

    # ── User context ──
    user_context = {
        "producer"    : "a farmer who grows this commodity and wants to decide when to SELL for maximum profit",
        "distributor" : "a trader who buys from farmers and sells to markets — looking for best BUY and SELL timing",
        "consumer"    : "a buyer who wants to purchase this commodity at the lowest possible price"
    }

    # ── FIXED PROMPT — no contradiction ──
    prompt = f"""
You are an agricultural commodity price advisor in Tamil Nadu.

Commodity: {commodity}
District: {district}
User: {user_type} — {user_context.get(user_type, "")}

Today Price: ₹{today_price}/quintal
Weekly Avg:  ₹{weekly_avg}/quintal
Trend: {trend}

Price Prediction:
  Tomorrow:  ₹{tomorrow}/quintal
  Day After: ₹{day_after}/quintal

Weather Forecast (3 days):
{weather_info}

Harvest Status: {harvest}
Festival Demand:
{festival_info}

System Signal: {signal}

Give exactly 4 lines of advisory. No numbering. No bullet points.

Line 1 → Market summary: current price, trend, and tomorrow prediction
Line 2 → Specific action the {user_type} should take TODAY and why
Line 3 → One key risk or opportunity from weather or festival demand
Line 4 → How harvest season and festival together affect this commodity now

Rules:
- Simple English only
- Each line must be a complete meaningful sentence
- Do not combine lines
- Do not add any extra lines or headings
"""
    return prompt


# ─────────────────────────────────────────
#  STEP 3 — CALL GEMINI API
# ─────────────────────────────────────────
def call_gemini(prompt):
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature"    : 0.4,
                "maxOutputTokens": 500   # ← increased from 300
                # thinkingConfig removed — was causing empty output
            }
        }

        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 200:
            data  = response.json()
            parts = (data.get("candidates", [{}])[0].get("content", {}) or {}).get("parts", []) or []
            text  = "".join([p.get("text", "") for p in parts]).strip()
            return text
        else:
            print(f"  ⚠️  Gemini error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"  ⚠️  Gemini failed: {e}")
        return None


# ─────────────────────────────────────────
#  GEMINI FALLBACK — When no DB data
#  Searches web for current price
# ─────────────────────────────────────────
def gemini_search_price(district, commodity):
    try:
        prompt = f"""
Search the web and find the current mandi market price
of {commodity} in {district}, Tamil Nadu, India.

Provide exactly 4 lines:
Line 1 → Current approximate price in ₹ per quintal
Line 2 → Price trend (rising / falling / stable) with reason
Line 3 → One line market summary
Line 4 → Advice for a farmer — should they sell now or wait?

Rules:
- English only
- Use ₹ and quintal units
- No bullet points or numbering
- If price not found, say "Price data currently unavailable"
"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "tools": [{
                "google_search": {}
            }],
            "generationConfig": {
                "temperature"    : 0.5,
                "maxOutputTokens": 500
            }
        }

        response = requests.post(url, json=payload, timeout=15)

        if response.status_code == 200:
            data  = response.json()
            parts = (data.get("candidates", [{}])[0].get("content", {}) or {}).get("parts", []) or []
            text  = "".join([p.get("text", "") for p in parts]).strip()
            return text
        else:
            print(f"  ⚠️  Gemini search error {response.status_code}: {response.text}")
            return None

    except Exception as e:
        print(f"  ⚠️  Gemini search failed: {e}")
        return None


# ─────────────────────────────────────────
#  MAIN — GENERATE COMPLETE ADVISORY
# ─────────────────────────────────────────
def generate_advisory(prediction_data):

    if not prediction_data:
        return None

    # ── No price history → use Gemini web search fallback ──
    if not prediction_data.get("prices"):
        print("\n⚠️  No DB data — using Gemini web search...")
        district  = prediction_data.get("district", "")
        commodity = prediction_data.get("commodity", "")
        result    = gemini_search_price(district, commodity)

        if result:
            print(f"\n{'='*60}")
            print(result)
            print(f"{'='*60}")
        else:
            print("❌ Could not fetch price from web either")

        return result

    # ── Normal flow — DB data available ──
    print("\n" + "=" * 60)
    print("  🤖 AI Advisory (Powered by Gemini)")
    print("=" * 60)

    district = prediction_data["district"]

    # Step 1 — Get 3 day weather
    print(f"\n🌦️  Fetching 3 day weather forecast for {district}...")
    weather_3day = get_3day_weather(district)

    if weather_3day:
        labels = ["Today    ", "Tomorrow ", "Day After"]
        for i, day in enumerate(weather_3day):
            label    = labels[i] if i < len(labels) else "        "
            rain_str = f" 🌧️ {day['rainfall_mm']}mm" if day["rainfall_mm"] > 0 else ""
            print(f"  {label} → {day['condition']:<10} {day['avg_temp']}°C {rain_str}")
            for alert in day["alerts"]:
                print(f"             ⚠️  {alert}")
    else:
        print("  ⚠️  Weather unavailable")

    # Step 2 — Build prompt
    print(f"\n🧠 Generating AI advisory...")
    prompt = build_prompt(prediction_data, weather_3day)

    # Step 3 — Call Gemini
    advisory = call_gemini(prompt)

    if advisory:
        print(f"\n{'='*60}")
        print(advisory)
        print(f"{'='*60}")
    else:
        # Fallback — show system signal
        print(f"\n{'='*60}")
        print(f"  {prediction_data['signal']}")
        print(f"  {prediction_data['reason']}")
        print(f"  Tomorrow: ₹{prediction_data['tomorrow']}/quintal")
        print(f"{'='*60}")

    return advisory


# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    from backend.predict import analyse

    print("=" * 60)
    print("  Daily Commodity Price Intelligence Tool")
    print("  ai_advisory.py — Full AI Advisory")
    print("=" * 60)

    print("\n👤 Who are you?")
    print("  1. Producer  (Farmer)")
    print("  2. Distributor (Trader)")
    print("  3. Consumer  (Buyer)")

    choice    = input("\n👉 Enter 1, 2 or 3: ").strip()
    user_map  = {"1": "producer", "2": "distributor", "3": "consumer"}
    user_type = user_map.get(choice, "consumer")
    district  = input("👉 Enter district name : ").strip()
    commodity = input("👉 Enter commodity name: ").strip()

    result = analyse(user_type, district, commodity)

    if result:
        generate_advisory(result)