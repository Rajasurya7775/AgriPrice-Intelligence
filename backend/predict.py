# ============================================================
#   Daily Commodity Price Intelligence Tool
#   prediction_engine.py — Price Prediction Logic
#   reads from MySQL only — no live price API calls
# ============================================================

import mysql.connector
from datetime import datetime, timedelta
from backend.config import DB_CONFIG, TN_HARVEST, TN_FESTIVALS, WEATHER_IMPACT
import json, time, os

# #region agent log
_DEBUG_LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "debug-f45c6e.log"))
def _agent_log(hypothesis_id, location, message, data=None, run_id="pre-fix"):
    try:
        payload = {
            "sessionId": "f45c6e",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion

# ─────────────────────────────────────────
#  STEP 1 — GET PRICE HISTORY FROM MYSQL
# ─────────────────────────────────────────
def get_price_history(district, commodity):
    try:
        conn   = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Get last 7 available days
        # Uses whatever days exist — no strict 7 day requirement
        cursor.execute("""
            SELECT
                arrival_date,
                ROUND(AVG(modal_price), 2) as avg_price,
                ROUND(MIN(min_price),   2) as min_price,
                ROUND(MAX(max_price),   2) as max_price,
                COUNT(DISTINCT market)     as markets_count
            FROM mandi_prices
            WHERE district  LIKE %s
            AND   commodity LIKE %s
            AND   arrival_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            GROUP BY arrival_date
            ORDER BY arrival_date ASC
        """, (f"%{district}%", f"%{commodity}%"))

        rows = cursor.fetchall()

        # If no data in last 7 days → try last 14 days
        if not rows:
            cursor.execute("""
                SELECT
                    arrival_date,
                    ROUND(AVG(modal_price), 2) as avg_price,
                    ROUND(MIN(min_price),   2) as min_price,
                    ROUND(MAX(max_price),   2) as max_price,
                    COUNT(DISTINCT market)     as markets_count
                FROM mandi_prices
                WHERE district  LIKE %s
                AND   commodity LIKE %s
                AND   arrival_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
                GROUP BY arrival_date
                ORDER BY arrival_date ASC
                LIMIT 7
            """, (f"%{district}%", f"%{commodity}%"))
            rows = cursor.fetchall()

        # Get all markets for this district + commodity
        cursor.execute("""
            SELECT
                market,
                ROUND(AVG(modal_price), 2) as avg_price
            FROM commodity_prices
            WHERE district  LIKE %s
            AND   commodity LIKE %s
            AND   arrival_date = (
                SELECT MAX(arrival_date)
                FROM mandi_prices
                WHERE district  LIKE %s
                AND   commodity LIKE %s
            )
            GROUP BY market
            ORDER BY avg_price DESC
        """, (f"%{district}%", f"%{commodity}%",
              f"%{district}%", f"%{commodity}%"))
        markets = cursor.fetchall()

        cursor.close()
        conn.close()
        return rows, markets

    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
        return [], []


# ─────────────────────────────────────────
#  STEP 2 — DETECT CONFIDENCE LEVEL
# ─────────────────────────────────────────
def get_confidence(days_count):
    if days_count >= 7:
        return "High ✅", "Based on full 7 days data"
    elif days_count >= 4:
        return "Medium ⚠️", f"Based on {days_count} days data"
    elif days_count >= 1:
        return "Low ⚠️", f"Only {days_count} day(s) available"
    else:
        return "None ❌", "No data found"


# ─────────────────────────────────────────
#  STEP 3 — DETECT TREND
# ─────────────────────────────────────────
def detect_trend(prices):
    if len(prices) < 2:
        return "Insufficient Data", 0

    changes = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        changes.append(change)

    avg_change = round(sum(changes) / len(changes), 2)
    last_3     = changes[-3:] if len(changes) >= 3 else changes

    rising  = sum(1 for c in last_3 if c > 0)
    falling = sum(1 for c in last_3 if c < 0)

    if rising >= 2:
        trend = "Rising ↑"
    elif falling >= 2:
        trend = "Falling ↓"
    else:
        trend = "Stable →"

    return trend, avg_change


# ─────────────────────────────────────────
#  STEP 4 — PREDICT TOMORROW + DAY AFTER
# ─────────────────────────────────────────
def predict_prices(prices, avg_change):
    if not prices:
        return None, None

    today_price = prices[-1]
    tomorrow    = round(max(today_price + avg_change, 0), 2)
    day_after   = round(max(tomorrow   + avg_change, 0), 2)

    return tomorrow, day_after


# ─────────────────────────────────────────
#  STEP 5 — CHECK HARVEST SEASON
# ─────────────────────────────────────────
def check_harvest(commodity):
    current_month = datetime.today().month
    commodity_key = None

    # Find matching commodity in harvest calendar
    for key in TN_HARVEST.keys():
        if key.lower() in commodity.lower() or commodity.lower() in key.lower():
            commodity_key = key
            break

    if not commodity_key:
        # #region agent log
        _agent_log("A", "backend/predict.py:check_harvest", "No harvest mapping match", {
            "commodity": commodity,
            "tn_harvest_keys": list(TN_HARVEST.keys())[:20]
        })
        # #endregion
        return "Unknown", 0

    data = TN_HARVEST[commodity_key]
    # #region agent log
    _agent_log("A", "backend/predict.py:check_harvest", "Harvest mapping found", {
        "commodity": commodity,
        "commodity_key": commodity_key,
        "data_keys": list(data.keys()) if isinstance(data, dict) else None
    })
    # #endregion

    # Support both config schemas:
    # - legacy: {"peak":[...], "lean":[...], "impact": N}
    # - current: {"peak_months":[...], "lean_months":[...]} (no impact)
    peak = data.get("peak") or data.get("peak_months") or []
    lean = data.get("lean") or data.get("lean_months") or []
    impact = data.get("impact", 0)  # config currently has no impact → keep neutral

    if current_month in peak:
        return "Peak Season 🌾 (High Supply → Price likely LOW)", -impact
    elif current_month in lean:
        return "Lean Season 🏜️ (Low Supply → Price likely HIGH)", impact
    else:
        return "Normal Season", 0


# ─────────────────────────────────────────
#  STEP 6 — CHECK UPCOMING FESTIVALS
# ─────────────────────────────────────────
def check_festivals():
    today        = datetime.today()
    upcoming     = []

    for festival in TN_FESTIVALS:
        try:
            fest_date = datetime.strptime(
                f"2026-{festival['date']}", "%Y-%m-%d"
            )
            days_until = (fest_date - today).days

            if 0 <= days_until <= festival["days_impact"]:
                upcoming.append({
                    "name"      : festival["name"],
                    "days_until": days_until,
                    "demand"    : festival["demand"],
                    "closed"    : festival["mandi_closed"]
                })
        except:
            continue

    return upcoming


# ─────────────────────────────────────────
#  STEP 7 — GENERATE BUY/SELL/HOLD SIGNAL
# ─────────────────────────────────────────
def get_signal(user_type, today_price, tomorrow, day_after, weekly_avg, trend):

    price_vs_avg = round(((today_price - weekly_avg) / weekly_avg) * 100, 1)

    if user_type == "producer":
        # Farmer wants to SELL at highest price
        if trend == "Rising ↑" and day_after > tomorrow:
            signal  = "HOLD 📦"
            reason  = "Price rising — wait 2 days for better rate"
        elif trend == "Falling ↓":
            signal  = "SELL NOW 🚨"
            reason  = "Price falling — sell today before further drop"
        else:
            signal  = "SELL TOMORROW 📈"
            reason  = "Price stable — tomorrow slightly better"

    elif user_type == "distributor":
        # Trader wants to BUY low and SELL high
        if trend == "Falling ↓":
            signal  = "BUY NOW 🛒"
            reason  = "Price falling — good time to stock up"
        elif trend == "Rising ↑":
            signal  = "SELL STOCK 💰"
            reason  = "Price rising — sell existing stock now"
        else:
            signal  = "HOLD STOCK ⏳"
            reason  = "Price stable — monitor for 1-2 days"

    else:
        # Consumer wants to BUY at lowest price
        if trend == "Rising ↑":
            signal  = "BUY TODAY 🛒"
            reason  = "Price rising — buy now before it gets expensive"
        elif trend == "Falling ↓":
            signal  = "WAIT 1-2 DAYS ⏳"
            reason  = "Price falling — wait for lower price"
        else:
            signal  = "BUY ANYTIME ✅"
            reason  = "Price stable — no urgency"

    return signal, reason, price_vs_avg


# ─────────────────────────────────────────
#  MAIN ANALYSIS FUNCTION
# ─────────────────────────────────────────
def analyse(user_type, district, commodity):

    print("\n" + "=" * 60)
    print(f"  📊 Price Intelligence Report")
    print(f"  User      : {user_type.capitalize()}")
    print(f"  District  : {district}")
    print(f"  Commodity : {commodity}")
    print(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # Get price history
    rows, markets = get_price_history(district, commodity)

    if not rows:
        print(f"\n❌ No data found for {commodity} in {district}")
        print("💡 Try running fetch_prices.py first")
        return None

    # Extract data
    prices  = [float(row["avg_price"]) for row in rows]
    dates   = [str(row["arrival_date"]) for row in rows]

    # Confidence level
    confidence, conf_note = get_confidence(len(prices))

    # Weekly average
    weekly_avg  = round(sum(prices) / len(prices), 2)
    today_price = prices[-1]
    last_date   = dates[-1]

    # Trend
    trend, avg_change = detect_trend(prices)

    # Predictions
    tomorrow, day_after = predict_prices(prices, avg_change)

    # Harvest season
    harvest_status, harvest_impact = check_harvest(commodity)

    # Festivals
    upcoming_festivals = check_festivals()

    # Signal
    signal, reason, price_vs_avg = get_signal(
        user_type, today_price, tomorrow, day_after, weekly_avg, trend
    )

    # ── Print History ──
    print(f"\n📅 Price History (₹/Quintal)")
    print(f"  {'Date':<15} {'Avg Price':>10} {'Min':>8} {'Max':>8} {'Markets':>8}")
    print("  " + "-" * 55)
    for i, row in enumerate(rows):
        marker = " ◀ LATEST" if i == len(rows)-1 else ""
        print(f"  {str(row['arrival_date']):<15} ₹{str(row['avg_price']):>8} ₹{str(row['min_price']):>6} ₹{str(row['max_price']):>6} {str(row['markets_count']):>7}{marker}")

    # ── Print Markets ──
    if markets:
        print(f"\n🏪 Markets in {district} (latest date)")
        print(f"  {'Market':<35} {'Avg Price':>10}")
        print("  " + "-" * 47)
        for m in markets:
            print(f"  {str(m['market']):<35} ₹{str(m['avg_price']):>8}")

    # ── Print Analysis ──
    print(f"\n📊 Analysis")
    print(f"  Last Available Date : {last_date}")
    print(f"  Latest Price        : ₹{today_price}")
    print(f"  Weekly Average      : ₹{weekly_avg}")
    print(f"  vs Weekly Average   : {price_vs_avg:+}%")
    print(f"  Trend               : {trend}")
    print(f"  Avg Daily Change    : ₹{avg_change}")
    print(f"  Data Confidence     : {confidence} ({conf_note})")

    # ── Print Predictions ──
    print(f"\n🔮 Predictions")
    print(f"  Tomorrow            : ₹{tomorrow}")
    print(f"  Day After Tomorrow  : ₹{day_after}")

    # ── Print Harvest ──
    print(f"\n🌾 Harvest Season")
    print(f"  Status              : {harvest_status}")
    if harvest_impact != 0:
        direction = "drop" if harvest_impact < 0 else "rise"
        print(f"  Expected Impact     : Price may {direction} ~{abs(harvest_impact)}%")

    # ── Print Festivals ──
    if upcoming_festivals:
        print(f"\n🎉 Upcoming Festivals (next 3 days)")
        for f in upcoming_festivals:
            days_text = "Today!" if f["days_until"] == 0 else f"in {f['days_until']} day(s)"
            closed    = "🔴 Mandi may close" if f["closed"] else "🟢 Mandi open"
            print(f"  → {f['name']} {days_text} | Demand: {f['demand']} | {closed}")
    else:
        print(f"\n🎉 No festivals in next 3 days")

    # ── Print Signal ──
    print(f"\n{'='*60}")
    print(f"  {signal}")
    print(f"  {reason}")
    print(f"{'='*60}")

    # Return data for AI advisory
    return {
        "user_type"          : user_type,
        "district"           : district,
        "commodity"          : commodity,
        "dates"              : dates,
        "prices"             : prices,
        "weekly_avg"         : weekly_avg,
        "today_price"        : today_price,
        "last_date"          : last_date,
        "trend"              : trend,
        "avg_change"         : avg_change,
        "tomorrow"           : tomorrow,
        "day_after"          : day_after,
        "confidence"         : confidence,
        "harvest_status"     : harvest_status,
        "harvest_impact"     : harvest_impact,
        "upcoming_festivals" : upcoming_festivals,
        "signal"             : signal,
        "reason"             : reason,
        "price_vs_avg"       : price_vs_avg,
        "markets"            : markets
    }


# ─────────────────────────────────────────
#  INTERACTIVE MODE
# ─────────────────────────────────────────
def interactive_mode():
    print("\n" + "=" * 60)
    print("  🌾 Commodity Price Intelligence — Tamil Nadu")
    print("=" * 60)

    # User type selection
    print("\n👤 Who are you?")
    print("  1. Producer  (Farmer)")
    print("  2. Distributor (Trader)")
    print("  3. Consumer  (Buyer)")

    choice = input("\n👉 Enter 1, 2 or 3: ").strip()
    user_map = {"1": "producer", "2": "distributor", "3": "consumer"}
    user_type = user_map.get(choice, "consumer")

    # District
    district  = input("\n👉 Enter district name: ").strip()

    # Commodity
    commodity = input("👉 Enter commodity name: ").strip()

    # Run analysis
    result = analyse(user_type, district, commodity)
    return result


# ─────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────
if __name__ == "__main__":
    interactive_mode()