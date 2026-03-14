
from flask import Flask, request, jsonify
from flask_cors import CORS
from backend.predict import analyse
from backend.AI_advisory import generate_advisory, get_3day_weather, build_prompt, call_gemini , gemini_search_price
from backend.config import TN_DISTRICTS, TN_COMMODITIES, get_db
import psycopg2
import requests
import json, time, os

# Create Flask app
app = Flask(__name__)
CORS(app)

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

# #region agent log
_agent_log("E", "backend/app.py:module", "Backend module loaded", {"debug_log_path": _DEBUG_LOG_PATH})
# #endregion

# ─────────────────────────────────────────
#  ENDPOINT 0 — TEST
# ─────────────────────────────────────────
@app.route("/", methods=["GET"])
def home():
    # #region agent log
    _agent_log("E", "backend/app.py:/", "Home endpoint hit", {"debug_log_path": _DEBUG_LOG_PATH})
    # #endregion
    return jsonify({
        "status" : "running",
        "message": "Commodity Price Intelligence API is live!",
        "debug_log_path": _DEBUG_LOG_PATH
    })

# ─────────────────────────────────────────
#  ENDPOINT 1 — GET ALL 38 TN DISTRICTS
# ─────────────────────────────────────────
@app.route("/districts", methods=["GET"])
def get_districts():
    try:
        districts = sorted(list(TN_DISTRICTS.keys()))
        return jsonify({
            "status"   : "success",
            "count"    : len(districts),
            "districts": districts
        })
    except Exception as e:
        return jsonify({
            "status" : "error",
            "message": str(e)
        }), 500

# ─────────────────────────────────────────
#  ENDPOINT 2 — GET COMMODITIES BY DISTRICT
# ─────────────────────────────────────────
@app.route("/commodities", methods=["GET"])
def get_commodities():
    district = request.args.get("district", "")

    if not district:
        return jsonify({
            "status" : "error",
            "message": "District required"
        }), 400

    return jsonify({
        "status"     : "success",
        "district"   : district,
        "count"      : len(TN_COMMODITIES),
        "commodities": TN_COMMODITIES
    })

# ─────────────────────────────────────────
#  ENDPOINT 3 — FULL ANALYSIS
# ─────────────────────────────────────────

@app.route("/analyse", methods=["POST"])
def get_analysis():

    data      = request.get_json()
    user_type = data.get("user_type", "consumer")
    district  = data.get("district",  "")
    commodity = data.get("commodity", "")

    # #region agent log
    _agent_log("A", "backend/app.py:/analyse", "Analyse request", {
        "user_type": user_type,
        "district": district,
        "commodity": commodity,
        "has_json": data is not None
    })
    # #endregion

    if not district or not commodity:
        return jsonify({
            "status" : "error",
            "message": "district and commodity are required"
        }), 400

    try:
        # Step 1 — Run prediction engine
        result = analyse(user_type, district, commodity)
        print(f"DEBUG result = {result}")
        # #region agent log
        _agent_log("A", "backend/app.py:/analyse", "Analyse result summary", {
            "result_is_none": result is None,
            "result_keys": list(result.keys()) if isinstance(result, dict) else None
        })
        # #endregion

        # Step 2 — No data → Gemini fallback
        if not result:
            print("DEBUG — entering Gemini fallback")
            advisory = gemini_search_price(district, commodity)
            print(f"DEBUG — Gemini returned: {advisory}")
            # #region agent log
            _agent_log("D", "backend/app.py:/analyse", "Gemini fallback used", {
                "advisory_present": bool(advisory),
                "advisory_len": len(advisory or "")
            })
            # #endregion
            return jsonify({
                "status"            : "success",
                "district"          : district,
                "commodity"         : commodity,
                "user_type"         : user_type,
                "data_source"       : "gemini_search",
                "advisory"          : advisory or "Price data currently unavailable",
                "signal"            : "CHECK MARKET 🔍",
                "latest_price"      : None,
                "weekly_avg"        : None,
                "trend"             : "Unknown",
                "tomorrow"          : None,
                "day_after"         : None,
                "price_history"     : [],
                "markets"           : [],
                "weather_3day"      : None,
                "harvest_status"    : "Unknown",
                "upcoming_festivals": []
            })

        # Step 3 — Mdata available → normal flow
        weather  = get_3day_weather(district)
        prompt   = build_prompt(result, weather)
        advisory = call_gemini(prompt)
        # #region agent log
        _agent_log("C", "backend/app.py:/analyse", "Gemini advisory generated", {
            "advisory_present": bool(advisory),
            "advisory_len": len(advisory or ""),
            "weather_present": bool(weather),
            "weather_days": len(weather) if isinstance(weather, list) else None
        })
        # #endregion

        return jsonify({
            "status"   : "success",
            "district" : district,
            "commodity": commodity,
            "user_type": user_type,
            "data_source": "mysql",

            "price_history": [
                {"date": d, "price": p}
                for d, p in zip(result["dates"], result["prices"])
            ],

            "latest_price" : result["today_price"],
            "last_date"    : result["last_date"],
            "weekly_avg"   : result["weekly_avg"],
            "trend"        : result["trend"],
            "confidence"   : result["confidence"],

            "tomorrow" : result["tomorrow"],
            "day_after": result["day_after"],

            "weather_3day"      : weather,
            "harvest_status"    : result["harvest_status"],
            "upcoming_festivals": result["upcoming_festivals"],

            "signal"  : result["signal"],
            "reason"  : result["reason"],
            "advisory": advisory or result["reason"],

            "markets": [
                {"market": m["market"], "price": m["avg_price"]}
                for m in result["markets"]
            ]
        })

    except Exception as e:
        # #region agent log
        _agent_log("A", "backend/app.py:/analyse", "Analyse exception", {
            "error": str(e),
            "error_type": type(e).__name__
        })
        # #endregion
        return jsonify({
            "status" : "error",
            "message": str(e)
        }), 500
        
@app.route("/movers", methods=["GET"])
def get_movers():
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
                SELECT
                    today.commodity,
                    today.district,
                    ROUND(AVG(today.modal_price)::numeric, 2)     AS today_price,
                    ROUND(AVG(yesterday.modal_price)::numeric, 2) AS yesterday_price,
                    ROUND(
                        ((AVG(today.modal_price) - AVG(yesterday.modal_price))
                        / AVG(yesterday.modal_price)) * 100, 1
                    ) AS change_pct
                FROM commodity_prices today
                JOIN commodity_prices yesterday
                    ON  today.commodity = yesterday.commodity
                    AND today.district  = yesterday.district
                WHERE today.arrival_date     = (SELECT MAX(arrival_date) FROM commodity_prices)
                AND   yesterday.arrival_date = (SELECT MAX(arrival_date) FROM commodity_prices) - INTERVAL '1 day'
                AND   today.modal_price > 0
                AND   yesterday.modal_price > 0
                GROUP BY today.commodity, today.district
                HAVING ABS(
                    ROUND(
                        ((AVG(today.modal_price) - AVG(yesterday.modal_price))
                        / AVG(yesterday.modal_price)) * 100, 1
                    )
                ) > 1
                ORDER BY change_pct DESC
                LIMIT 20
            """)

        rows   = cursor.fetchall()
        cols   = [desc[0] for desc in cursor.description]
        movers = [dict(zip(cols, row)) for row in rows]

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "movers": movers
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────
#  ENDPOINT 5 — SEASONAL CALENDAR
# ─────────────────────────────────────────
@app.route("/seasonal", methods=["GET"])
def get_seasonal():
    try:
        from backend.config import TN_HARVEST
        seasonal = []

        for commodity, data in TN_HARVEST.items():
            seasonal.append({
                "commodity": commodity,
                "peak"     : data.get("peak_months", []),
                "lean"     : data.get("lean_months", []),
            })

        return jsonify({
            "status"  : "success",
            "seasonal": seasonal
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
# ─────────────────────────────────────────
#  ENDPOINT 6 — COMMODITY IMAGE
# ─────────────────────────────────────────
@app.route("/commodity-image", methods=["GET"])
def get_commodity_image():
    commodity = request.args.get("commodity", "")
    
    try:
        query    = commodity.split("(")[0].strip().split()[0].lower()
        url      = "https://api.unsplash.com/search/photos"
        headers  = {"Authorization": f"Client-ID {os.getenv('UNSPLASH_ACCESS_KEY')}"}
        params   = {
            "query"      : f"{query} vegetable food",
            "per_page"   : 1,
            "orientation": "landscape"
        }
        
        res  = requests.get(url, headers=headers, params=params)
        data = res.json()
        
        if data["results"]:
            img_url = data["results"][0]["urls"]["regular"]
            return jsonify({"status": "success", "url": img_url})
        else:
            return jsonify({"status": "error", "url": None})
            
    except Exception as e:
        return jsonify({"status": "error", "url": None})
# ─────────────────────────────────────────
#  RUN SERVER
# ─────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)