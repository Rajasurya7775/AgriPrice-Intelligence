import os
import psycopg2
from psycopg2.extras import RealDictCursor

_SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")


def _load_sql(filename: str) -> str:
    with open(os.path.join(_SQL_DIR, filename)) as fh:
        return fh.read()


def _connect(db_url: str = None):
    try:
        from backend.config import get_db
    except ImportError:
        from config import get_db
    return get_db(cursor_factory=RealDictCursor)

def get_price_trend(db_url: str, commodity: str) -> dict:
    sql = _load_sql("price_trend.sql")
    conn = _connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(sql, {"commodity": commodity})
            rows = cur.fetchall()
        return {
            "trend_labels" : [r["label"]       for r in rows],
            "trend_prices" : [float(r["price"]) for r in rows],
            "rolling_avg"  : [float(r["rolling_avg"]) for r in rows],
        }
    finally:
        conn.close()


def get_seasonal_data(db_url: str) -> list:
    
    sql = _load_sql("seasonal_scoring.sql")
    conn = _connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()

