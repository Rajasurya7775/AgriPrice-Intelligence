# routes/prices.py
# API routes for market prices and stats.

import os
from psycopg2.extras import RealDictCursor
from flask import Blueprint, request, jsonify
from backend.config import get_db

prices_bp = Blueprint("prices", __name__)

# Sort by user role preferences
_ROLE_SORT = {
    "farmer"  : lambda x: -x["modal_price"],
    "trader"  : lambda x: -(x["max_price"] - x["min_price"]),
    "consumer": lambda x:  x["modal_price"],
}


def _load_sql(filename: str) -> str:
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql", filename)
    with open(sql_path, "r", encoding="utf-8") as f:
        return f.read()


def _get_conn():
    return get_db(cursor_factory=RealDictCursor)


@prices_bp.route("/api/prices")
def get_prices():
    commodity = request.args.get("commodity", "").strip()
    role      = request.args.get("role", "farmer").lower()

    if not commodity:
        return jsonify({"error": "commodity is required"}), 400

    conn = None
    try:
        conn = _get_conn()
        sql = _load_sql("prices.sql")
        with conn.cursor() as cur:
            cur.execute(sql, (commodity, commodity, commodity))
            rows = cur.fetchall()

        results = []
        for r in rows:
            item = dict(r)
            item["fetched_at"] = str(item["fetched_at"])
            results.append(item)

        sort_key = _ROLE_SORT.get(role, _ROLE_SORT["farmer"])
        results.sort(key=sort_key)

        return jsonify({"prices": results})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()


@prices_bp.route("/api/stats")
def get_stats():
    conn = None
    try:
        conn = _get_conn()
        with conn.cursor() as cur:
            cur.execute(_load_sql("stats_commodities.sql"))
            commodities = cur.fetchone()["c"]

            cur.execute(_load_sql("stats_markets.sql"))
            markets = cur.fetchone()["m"]

            cur.execute(_load_sql("stats_last_updated.sql"))
            last = cur.fetchone()["t"]

        return jsonify({
            "commodities" : commodities,
            "markets"     : markets,
            "last_updated": last.strftime("%d %b %I:%M %p") if last else "N/A",
            "accuracy"    : "96%",
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        if conn:
            conn.close()

 
 
@prices_bp.route("/api/config")
def get_config():
    from backend.config import TN_DISTRICTS, TN_COMMODITIES, TN_COMMODITY_CATEGORIES, TN_COMMODITY_READABLE_NAMES, TN_FESTIVALS
    commodities_list = []
    for cat, list_items in TN_COMMODITY_CATEGORIES.items():
        items = []
        for val in list_items:
            if val in TN_COMMODITIES:
                name = TN_COMMODITY_READABLE_NAMES.get(val, val)
                items.append({"name": name, "value": val})
        if items:
            commodities_list.append({"category": cat, "items": items})
                
    # Add any remaining uncategorized commodities under "Others"
    categorized_set = set()
    for list_items in TN_COMMODITY_CATEGORIES.values():
        categorized_set.update(list_items)
        
    others = []
    for val in TN_COMMODITIES:
        if val not in categorized_set:
            name = TN_COMMODITY_READABLE_NAMES.get(val, val)
            others.append({"name": name, "value": val})
            
    if others:
        commodities_list.append({"category": "Others", "items": others})

    return jsonify({
        "districts": sorted(list(TN_DISTRICTS.keys())),
        "district_coords": TN_DISTRICTS,
        "commodities": commodities_list,
        "festivals": TN_FESTIVALS
    })