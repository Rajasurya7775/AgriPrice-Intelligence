import requests
import mysql.connector
from backend.config import AGMARKNET_API_KEY,AGMARKNET_BASE_URL
from datetime import datetime

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
# MYSQL CONNECTION
# -----------------------

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Surya@2005",
    database="commodity_intelligence"
)

cursor = db.cursor()

# -----------------------
# FETCH DATA
# -----------------------

response = requests.get(url, params=params)

data = response.json()


records = data["records"]


print("Total records:", len(records))
print("Data inserted successfully")
print(data)

# -----------------------
# INSERT INTO MYSQL
# -----------------------

for record in records:

    state = record.get("state")
    district = record.get("district")
    market = record.get("market")
    commodity = record.get("commodity")
    grade = record.get("grade")
    min_price = record.get("min_price")
    max_price = record.get("max_price")
    modal_price = record.get("modal_price")
    arrival_date_raw = record.get("arrival_date")
    arrival_date = datetime.strptime(arrival_date_raw, "%d/%m/%Y").strftime("%Y-%m-%d")


    sql = """
    INSERT IGNORE INTO mandi_prices
    (state, district, market, commodity, grade, min_price, max_price, modal_price,arrival_date)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (state, district, market, commodity, grade, min_price, max_price, modal_price,arrival_date)

    cursor.execute(sql, values)

db.commit()
cursor.close()
db.close()