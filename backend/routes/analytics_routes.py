# routes/analytics_routes.py
# API routes for market analytics.

import os
from flask import Blueprint, request, jsonify

from ..analytics import get_price_trend

analytics_bp = Blueprint("analytics", __name__)

DB_URL = os.environ.get("DATABASE_URL")


def _require_commodity():
    commodity = request.args.get("commodity", "").strip()
    if not commodity:
        return None, (jsonify({"error": "commodity is required"}), 400)
    return commodity, None


@analytics_bp.route("/api/analytics")
def get_analytics():
    commodity, err = _require_commodity()
    if err:
        return err
    try:
        return jsonify(get_price_trend(DB_URL, commodity))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

