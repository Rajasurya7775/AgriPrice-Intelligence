import os
from dotenv import load_dotenv

load_dotenv()

AGMARKNET_API_KEY   = os.getenv("AGMARKNET_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")

DB_CONFIG = {
    "host"    : os.getenv("DB_HOST",     "localhost"),
    "user"    : os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "commodity_intelligence")
}

# ─────────────────────────────────────────
#  AGMARKNET API
# ─────────────────────────────────────────
AGMARKNET_BASE_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
AGMARKNET_STATE    = "Tamil Nadu"
AGMARKNET_LIMIT    = "2000"

# ─────────────────────────────────────────
#  OPENWEATHERMAP API
# ─────────────────────────────────────────
WEATHER_BASE_URL     = "https://api.openweathermap.org/data/2.5/weather"
WEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# ─────────────────────────────────────────
#  ALL 38 TAMIL NADU DISTRICTS + COORDINATES
# ─────────────────────────────────────────
TN_DISTRICTS = {
    "Ariyalur"       : {"lat": 11.14, "lon": 79.08},
    "Chennai"        : {"lat": 13.08, "lon": 80.27},
    "Chengalpattu"   : {"lat": 12.69, "lon": 79.97},
    "Coimbatore"     : {"lat": 11.00, "lon": 76.96},
    "Cuddalore"      : {"lat": 11.75, "lon": 79.76},
    "Dharmapuri"     : {"lat": 12.12, "lon": 78.15},
    "Dindigul"       : {"lat": 10.36, "lon": 77.97},
    "Erode"          : {"lat": 11.34, "lon": 77.72},
    "Kallakurichi"   : {"lat": 11.73, "lon": 78.96},
    "Kancheepuram"   : {"lat": 12.83, "lon": 79.70},
    "Karur"          : {"lat": 10.96, "lon": 78.08},
    "Kanyakumari"    : {"lat": 8.08,  "lon": 77.55},
    "Krishnagiri"    : {"lat": 12.52, "lon": 78.21},
    "Madurai"        : {"lat": 9.93,  "lon": 78.12},
    "Nagapattinam"   : {"lat": 10.76, "lon": 79.84},
    "Namakkal"       : {"lat": 11.22, "lon": 78.16},
    "Perambalur"     : {"lat": 11.23, "lon": 78.88},
    "Pudukkottai"    : {"lat": 10.38, "lon": 78.82},
    "Ramanathapuram" : {"lat": 9.37,  "lon": 78.83},
    "Ranipet"        : {"lat": 12.92, "lon": 79.33},
    "Salem"          : {"lat": 11.65, "lon": 78.15},
    "Sivaganga"      : {"lat": 9.84,  "lon": 78.48},
    "Thanjavur"      : {"lat": 10.78, "lon": 79.13},
    "Theni"          : {"lat": 10.01, "lon": 77.47},
    "Thoothukudi"    : {"lat": 8.76,  "lon": 78.13},
    "Tiruchirappalli": {"lat": 10.79, "lon": 78.70},
    "Tirunelveli"    : {"lat": 8.73,  "lon": 77.69},
    "Tirupathur"     : {"lat": 12.49, "lon": 78.57},
    "Tiruppur"       : {"lat": 11.10, "lon": 77.34},
    "Tiruvallur"     : {"lat": 13.14, "lon": 79.90},
    "Tiruvannamalai" : {"lat": 12.22, "lon": 79.07},
    "Tiruvarur"      : {"lat": 10.77, "lon": 79.64},
    "Vellore"        : {"lat": 12.92, "lon": 79.13},
    "Viluppuram"     : {"lat": 11.93, "lon": 79.49},
    "Virudhunagar"   : {"lat": 9.58,  "lon": 77.96}
}

TN_COMMODITIES = [
    "Amaranthus", "Amla(Nelli Kai)", "Apple",
    "Arhar(Tur/Red Gram)(Whole)", "Ashgourd",
    "Bajra(Pearl Millet/Cumbu)", "Banana",
    "Banana - Green", "Beans", "Beetroot",
    "Betal Leaves", "Bhindi(Ladies Finger)",
    "Bitter gourd", "Bottle gourd", "Brinjal",
    "Cabbage", "Capsicum", "Carrot",
    "Cauliflower", "Chikoos(Sapota)",
    "Chili Red", "Chow Chow", "Cluster beans",
    "Coconut", "Colacasia", "Coriander(Leaves)",
    "Cowpea(Veg)", "Cucumbar(Kheera)",
    "Custard Apple(Sharifa)", "Drumstick",
    "Elephant Yam(Suran)/Amorphophallus",
    "Fig(Anjura/Anjeer)", "Garlic",
    "Ginger(Green)", "Grapes", "Green Avare(W)",
    "Green Chilli", "Green Peas", "Groundnut",
    "Guava", "Indian Beans(Seam)",
    "Jack Fruit(Ripe)", "Jasmine",
    "Jowar(Sorghum)", "Kakada",
    "Karbuja(Musk Melon)", "Knool Khol",
    "Lemon", "Lime", "Mango", "Mango(Raw-Ripe)",
    "Marigold(Calcutta)", "Mashrooms",
    "Mint(Pudina)", "Mousambi(Sweet Lime)",
    "Onion", "Onion Green", "Orange",
    "Paddy(Common)", "Papaya", "Pear(Marasebu)",
    "Pineapple", "Pomegranate", "Potato",
    "Pumpkin", "Raddish", "Ragi(Finger Millet)",
    "Ridgeguard(Tori)", "Rose(Local)",
    "Snakeguard", "Soyabean", "Sweet Potato",
    "Tamarind Fruit", "Tapioca",
    "Tender Coconut", "Thondekkai", "Tomato",
    "Tube Flower", "Tube Rose(Loose)", "Turnip",
    "Water Melon", "Yam(Ratalu)"
]

TN_FESTIVALS = [
    {"name": "New Year's Day",       "date": "01-01", "days_impact": 3, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Thai Pongal",          "date": "01-15", "days_impact": 5, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Thiruvalluvar Day",    "date": "01-16", "days_impact": 2, "demand": "MEDIUM", "mandi_closed": True},
    {"name": "Uzhavar Thirunal",     "date": "01-17", "days_impact": 2, "demand": "MEDIUM", "mandi_closed": True},
    {"name": "Republic Day",         "date": "01-26", "days_impact": 1, "demand": "LOW",    "mandi_closed": True},
    {"name": "Thai Poosam",          "date": "02-01", "days_impact": 2, "demand": "MEDIUM", "mandi_closed": True},
    {"name": "Ramzan (Eid ul-Fitr)", "date": "03-21", "days_impact": 4, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Mahaveer Jayanthi",    "date": "03-31", "days_impact": 1, "demand": "LOW",    "mandi_closed": True},
    {"name": "Good Friday",          "date": "04-03", "days_impact": 2, "demand": "MEDIUM", "mandi_closed": True},
    {"name": "Tamil New Year",       "date": "04-14", "days_impact": 4, "demand": "HIGH",   "mandi_closed": True},
    {"name": "May Day",              "date": "05-01", "days_impact": 2, "demand": "MEDIUM", "mandi_closed": True},
    {"name": "Independence Day",     "date": "08-15", "days_impact": 2, "demand": "MEDIUM", "mandi_closed": True},
    {"name": "Vinayagar Chathurthi", "date": "09-14", "days_impact": 3, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Ayudha Poojai",        "date": "10-19", "days_impact": 3, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Vijayadasami",         "date": "10-20", "days_impact": 2, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Deepavali",            "date": "11-08", "days_impact": 5, "demand": "HIGH",   "mandi_closed": True},
    {"name": "Christmas",            "date": "12-25", "days_impact": 3, "demand": "MEDIUM", "mandi_closed": True},
]

# ─────────────────────────────────────────
#  TAMIL NADU HARVEST CALENDAR
# ─────────────────────────────────────────
TN_HARVEST = {
    "Tomato": {
        "peak_months": [11, 12, 1],
        "lean_months": [5, 6, 7]
    },
    "Onion": {
        "peak_months": [12, 1, 2],
        "lean_months": [6, 7, 8]
    },
    "Potato": {
        "peak_months": [1, 2, 3],
        "lean_months": [7, 8, 9]
    },
    "Brinjal": {
        "peak_months": [10, 11, 12],
        "lean_months": [4, 5, 6]
    },
    "Carrot": {
        "peak_months": [11, 12, 1],
        "lean_months": [5, 6, 7]
    },
    "Beans": {
        "peak_months": [11, 12, 1],
        "lean_months": [5, 6, 7]
    },
    "Cabbage": {
        "peak_months": [11, 12, 1],
        "lean_months": [6, 7, 8]
    },
    "Cauliflower": {
        "peak_months": [11, 12, 1],
        "lean_months": [5, 6, 7]
    },
    "Drumstick": {
        "peak_months": [2, 3, 4],
        "lean_months": [8, 9, 10]
    },
    "Banana": {
        "peak_months": [3, 4, 5],
        "lean_months": [9, 10, 11]
    }
}


# ─────────────────────────────────────────
#  WEATHER IMPACT RULES
# ─────────────────────────────────────────
WEATHER_IMPACT = {
    "heavy_rain_mm"    : 20,
    "extreme_heat_c"   : 38,
    "high_humidity_pct": 85,
    "price_impact_pct" : 15,
}



# ─────────────────────────────────────────
#  GEMINI AI
# ─────────────────────────────────────────
GEMINI_MODEL    = "gemini-2.5-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

# ─────────────────────────────────────────
#  SCHEDULER
# ─────────────────────────────────────────
FETCH_TIME = "06:00"