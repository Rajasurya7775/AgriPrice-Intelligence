# routes/seasonal.py
# /api/seasonal — returns seasonal profit-potential scoring for all active commodities.

import os
from flask import Blueprint, jsonify

from ..analytics import get_seasonal_data

seasonal_bp = Blueprint("seasonal", __name__)

DB_URL = os.environ.get("DATABASE_URL")


@seasonal_bp.route("/api/seasonal")
def get_seasonal():
    try:
        return jsonify(get_seasonal_data(DB_URL))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
