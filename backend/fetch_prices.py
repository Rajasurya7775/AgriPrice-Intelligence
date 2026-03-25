import requests
import psycopg2
import io
import csv
from datetime import datetime

try:
    from backend.config import AGMARKNET_API_KEY, AGMARKNET_BASE_URL, get_db
except ImportError:
    from config import AGMARKNET_API_KEY, AGMARKNET_BASE_URL, get_db


# -----------------------
# API CONFIG
# -----------------------

API_KEY = AGMARKNET_API_KEY
URL = AGMARKNET_BASE_URL


params = {
    "api-key": API_KEY,
    "format": "json",
    "limit": 9999,
    "filters[state.keyword]": "Tamil Nadu"
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}
# -----------------------
# FETCH DATA
# -----------------------

print("Fetching mandi data...")

try:
    response = requests.get(URL, params=params,headers=headers,timeout=60)
    response.raise_for_status()

    data = response.json()
    records = data.get("records", [])

    print(f"Records received: {len(records)}")

except Exception as e:
    print("❌ API fetch failed:", e)
    exit()


# -----------------------
# CREATE CSV BUFFER
# -----------------------

buffer = io.StringIO()
writer = csv.writer(buffer)

for r in records:

    try:
        arrival_date = datetime.strptime(
            r.get("arrival_date"),
            "%d/%m/%Y"
        ).strftime("%Y-%m-%d")
    except:
        continue

    writer.writerow([
        r.get("state"),
        r.get("district"),
        r.get("market"),
        r.get("commodity"),
        r.get("variety"),
        r.get("min_price"),
        r.get("max_price"),
        r.get("modal_price"),
        arrival_date
    ])

buffer.seek(0)


# -----------------------
# INSERT INTO DATABASE
# -----------------------

print("Connecting to database...")

db = get_db()
cursor = db.cursor()

try:

    # Fix sequence mismatch
    cursor.execute("""
    SELECT setval(
        'commodity_prices_id_seq',
        COALESCE((SELECT MAX(id) FROM commodity_prices),1)
    )
    """)

    print("Inserting data...")

    cursor.copy_expert("""
    COPY commodity_prices
    (state,district,market,commodity,variety,
    min_price,max_price,modal_price,arrival_date)
    FROM STDIN WITH CSV
    """, buffer)

    db.commit()

    print("✅ Insert completed")

except Exception as e:

    db.rollback()
    print("❌ Insert failed:", e)

finally:
    cursor.close()
    db.close()


# -----------------------
# CLEAN OLD DATA
# -----------------------

print("Cleaning old records...")

try:

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
    DELETE FROM commodity_prices
    WHERE arrival_date < CURRENT_DATE - INTERVAL '7 days'
    """)

    deleted = cursor.rowcount
    db.commit()

    cursor.close()
    db.close()

    print(f"🗑 Deleted {deleted} old rows")

except Exception as e:

    print("⚠ Cleanup failed:", e)


print("✅ Pipeline completed")
