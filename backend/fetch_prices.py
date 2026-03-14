import requests
from datetime import datetime
import psycopg2
import io
try:
    from backend.config import AGMARKNET_API_KEY, AGMARKNET_BASE_URL, get_db
except ImportError:
    from config import AGMARKNET_API_KEY, AGMARKNET_BASE_URL, get_db


# -----------------------
# API CONFIG
# -----------------------

API_KEY =AGMARKNET_API_KEY

url = AGMARKNET_BASE_URL

params = {
    "api-key": API_KEY,
    "format": "json",
    "limit": 9999,
    "filters[state.keyword]": "Tamil Nadu"
    
}

# -----------------------
# POSTGRESQL CONNECTION
# -----------------------
db = get_db()
cursor = db.cursor()

# -----------------------
# FETCH DATA
# -----------------------

try:
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    print(f"API Response Status: {response.status_code}")
    print(f"Records found: {len(data.get('records', []))}")
except requests.exceptions.RequestException as e:
    print(f"❌ API Request failed: {e}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    exit(1)
except ValueError as e:
    print(f"❌ JSON parsing failed: {e}")
    print(f"Response text: {response.text[:500]}")
    exit(1)


records = data["records"]


print("Total records:", len(records))


buffer = io.StringIO()

for r in records:

    arrival_date_raw = r.get("arrival_date")

    try:
        arrival_date = datetime.strptime(
            arrival_date_raw, "%d/%m/%Y"
        ).strftime("%Y-%m-%d")
    except:
        continue

    buffer.write(
        f"{r.get('state')},{r.get('district')},{r.get('market')},{r.get('commodity')},{r.get('variety')},{r.get('min_price')},{r.get('max_price')},{r.get('modal_price')},{arrival_date}\n"
    )

buffer.seek(0)

print(records[0])

# -----------------------
# FAST INSERT (COPY)
# -----------------------

print("Inserting data...")

cursor.copy_expert("""
COPY commodity_prices
(state,district,market,commodity,variety,
min_price,max_price,modal_price,arrival_date)
FROM STDIN WITH CSV
""", buffer)

db.commit()

print("Insert completed")

cursor.close()
db.close()
# -----------------------
# SLIDING WINDOW CLEANUP
# Only runs if fetch successful
# ----------------------- 
try:
    from backend.config import get_db
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM commodity_prices
        WHERE arrival_date < CURRENT_DATE - INTERVAL '6 days'
    """)

    deleted = cursor.rowcount
    db.commit()
    cursor.close()
    db.close()

    print(f"🗑️  Deleted {deleted} old records")
    print(f"✅  DB now has last 7 days only")

except Exception as e:
    print(f"⚠️  Cleanup failed: {e}")

print("✅ Done!")


