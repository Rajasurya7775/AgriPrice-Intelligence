import os
import requests
from datetime import datetime
from flask import Blueprint, jsonify, request

weather_bp = Blueprint("weather", __name__)

_API_KEY      = os.environ.get("OPENWEATHER_API_KEY")
_BASE_CURRENT = "https://api.openweathermap.org/data/2.5/weather"
_BASE_FORECAST= "https://api.openweathermap.org/data/2.5/forecast"
_TIMEOUT      = 5

_FALLBACK_DISTRICTS = ["Chennai", "Coimbatore", "Tiruchirappalli", "Madurai"]


def _rain_prob_from_condition(condition: str) -> int:
    if condition in ("Rain", "Drizzle", "Thunderstorm"):
        return 90
    if condition == "Clouds":
        return 30
    return 10


def _fetch_current(district: str) -> dict | None:
    if not _API_KEY:
        return None
    try:
        res  = requests.get(
            _BASE_CURRENT,
            params={"q": f"{district},IN", "appid": _API_KEY, "units": "metric"},
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
        cond = data["weather"][0]["main"]
        return {
            "district" : district,
            "temp"     : round(data["main"]["temp"]),
            "humidity" : data["main"]["humidity"],
            "wind"     : round(data["wind"]["speed"] * 3.6),  # m/s → km/h
            "condition": cond,
            "rain_prob": _rain_prob_from_condition(cond),
        }
    except Exception:
        return None


def _fetch_forecast(district: str) -> list | None:
    if not _API_KEY:
        return None
    try:
        res  = requests.get(
            _BASE_FORECAST,
            params={"q": f"{district},IN", "appid": _API_KEY, "units": "metric"},
            timeout=_TIMEOUT,
        )
        res.raise_for_status()
        data      = res.json()
        today_str = datetime.today().strftime("%Y-%m-%d")
        forecasts_by_day = {}

        for item in data.get("list", []):
            dt_txt = item.get("dt_txt", "")
            if not dt_txt:
                continue
            date_part, time_part = dt_txt.split(" ")
            if date_part == today_str:
                continue
            if date_part not in forecasts_by_day:
                forecasts_by_day[date_part] = []
            forecasts_by_day[date_part].append(item)

        forecast  = []
        for date_part in sorted(forecasts_by_day.keys())[:3]:
            slots = forecasts_by_day[date_part]
            # Prefer noon slot; accept first-of-day as fallback
            selected_slot = next((s for s in slots if "12:00:00" in s.get("dt_txt", "")), slots[0])
            dt_obj = datetime.strptime(date_part, "%Y-%m-%d")
            forecast.append({
                "date"     : dt_obj.strftime("%a (%d %b)"),
                "temp"     : round(selected_slot["main"]["temp"]),
                "humidity" : selected_slot["main"]["humidity"],
                "wind"     : round(selected_slot["wind"]["speed"] * 3.6),
                "condition": selected_slot["weather"][0]["main"],
                "rain_prob": round(selected_slot.get("pop", 0) * 100),
            })

        return forecast
    except Exception:
        return None


@weather_bp.route("/api/weather")
def get_weather():
    district = request.args.get("district", "").strip()

    if district:
        current = _fetch_current(district)
        if not current:
            return jsonify({"error": f"Weather data unavailable for {district}."}), 404
        return jsonify({
            "current" : current,
            "forecast": _fetch_forecast(district) or [],
        })

    results = [w for d in _FALLBACK_DISTRICTS if (w := _fetch_current(d))]
    return jsonify({"weather": results})
