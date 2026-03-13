import requests
from backend.config import AGMARKNET_API_KEY,AGMARKNET_BASE_URL,PG_CONFIG
from datetime import datetime
import psycopg2

# -----------------------
# API CONFIG
# -----------------------

API_KEY =AGMARKNET_API_KEY

url = AGMARKNET_BASE_URL

params = {
    "api-key": API_KEY,
    "format": "json",
    "limit": 9999,
    "filters[State]": "Tamil Nadu",
    "filters[Arrival_Date]": "07/03/2026"
    
}

# -----------------------
# POSTGRESQL CONNECTION
# -----------------------
db     = psycopg2.connect(**PG_CONFIG)
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
print("Data inserted successfully")


# -----------------------
# INSERT INTO MYSQL
# -----------------------

for record in records:

    state = record.get("State")
    district = record.get("District")
    market = record.get("Market")
    commodity = record.get("Commodity")
    variety = record.get("Variety")
    min_price = record.get("Min_Price")
    max_price = record.get("Max_Price")
    modal_price = record.get("Modal_Price")
    arrival_date_raw = record.get("Arrival_Date")
    arrival_date = datetime.strptime(arrival_date_raw, "%d/%m/%Y").strftime("%Y-%m-%d")


    sql ="""
        INSERT INTO commodity_prices
        (state, district, market, commodity, variety,
        min_price, max_price, modal_price, arrival_date)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (market, commodity, variety, arrival_date)
        DO NOTHING
        """

    values = (state, district, market, commodity, variety, min_price, max_price, modal_price,arrival_date)

    cursor.execute(sql, values)

db.commit()
cursor.close()
db.close()