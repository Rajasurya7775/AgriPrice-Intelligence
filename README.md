## AgriPrice Intelligence — Tamil Nadu Mandi Advisory

AgriPrice Intelligence is an end‑to‑end price intelligence tool for Tamil Nadu agricultural markets.  
It combines **historical mandi prices (MySQL)**, **OpenWeather 3‑day forecast**, **festival demand**, and **Google Gemini AI** to generate clear **BUY / SELL / HOLD** advisories for farmers, traders, and consumers.

### Features

- **Multi‑role advisory**: Separate views for **Farmer (Producer)**, **Trader (Distributor)**, and **Consumer (Buyer)**.
- **District + commodity selection**: 38 Tamil Nadu districts and 80+ commodities from Agmarknet.
- **Price intelligence backend**:
  - 7‑day sliding window price history from MySQL.
  - Trend detection (rising / falling / stable) and confidence score.
  - Predictions for **tomorrow** and **day after tomorrow**.
  - Harvest season and nearby festival impact.
- **AI advisory layer (Gemini)**:
  - Enriched, human‑friendly 3–4 line advisory based on price signal, weather, harvest, and festivals.
  - Web‑search fallback when DB has no data for a district–commodity pair.
- **Modern frontend UI**:
  - Single‑page layout with **Home**, **Seasonal Calendar**, and **About** pages.
  - Animated ticker for daily “market movers”.
  - Visual cards for stats, price chart, 3‑day weather, and festivals.

---

## Tech Stack

- **Backend**: Python, Flask, Flask‑CORS
- **Database**: MySQL (schema: `mandi_prices`, `commodity_prices`)
- **Data sources**:
  - Agmarknet API (historical mandi prices)
  - OpenWeatherMap (3‑day forecast)
  - Google Gemini (AI advisory + price search fallback)
  - Unsplash API (commodity images)
- **Frontend**: HTML, CSS, vanilla JS, Chart.js

---

## Project Structure

```text
AgriPrice_Intelligence/
  backend/
    app.py             # Flask API entrypoint
    predict.py         # MySQL price analysis and signals
    AI_advisory.py     # Gemini prompts and fallback search
    fetch_prices.py    # Agmarknet → MySQL ingestion
    config.py          # API keys, DB config, static config

  frontend/
    index.html         # Single‑page app shell
    css/style.css      # Modern UI styling
    js/api.js          # Fetch wrappers to backend + Unsplash
    js/app.js          # Main app logic and interactions
    js/ui.js           # Rendering helpers and Chart.js

  requirements.txt     # Python backend dependencies
  .env                 # Local secrets (NOT committed)
```

---

## Prerequisites

- **Python**: 3.10+ (project tested with 3.13)
- **MySQL**: running instance accessible from your machine
- **Node / npm**: *optional*, only if you later add tooling; current frontend is plain HTML/JS
- **API keys**:
  - `AGMARKNET_API_KEY` (data.gov.in)
  - `OPENWEATHER_API_KEY`
  - `GEMINI_API_KEY`

> **Important**: keep all API keys in `.env` (never commit them).

---

## 1. Environment Setup

### 1.1 Clone the repository

```bash
git clone https://github.com/<your-username>/AgriPrice_Intelligence.git
cd AgriPrice_Intelligence
```

### 1.2 Create and activate virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows PowerShell
# source .venv/bin/activate  # Linux / macOS
```

### 1.3 Install Python dependencies

```bash
pip install -r requirements.txt
```

### 1.4 Configure `.env`

Create a `.env` file in the project root:

```text
AGMARKNET_API_KEY=your_api_key_here
OPENWEATHER_API_KEY=your_api_key_here
GEMINI_API_KEY=your_api_key_here

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_db_password
DB_NAME=commodity_intelligence
```

> For GitHub, add a safe `.env.example` (same keys, placeholder values) and keep **`.env` in `.gitignore`**.

---

## 2. Database Setup

You need a MySQL schema that matches the queries in `backend/predict.py` and `backend/fetch_prices.py`.

Tables used (high‑level):

- `mandi_prices`  
  - fields used: `arrival_date`, `district`, `commodity`, `modal_price`, `min_price`, `max_price`, `market`
- `commodity_prices`  
  - used for market‑level averages

Recommended flow:

1. Create database:

```sql
CREATE DATABASE commodity_intelligence;
```

2. Create the required tables (aligning with your Agmarknet ingestion).
3. Run `backend/fetch_prices.py` periodically (e.g., daily) to pull data from Agmarknet into MySQL.

---

## 3. Running the Backend

From the project root with the virtualenv activated:

```bash
(.venv) python backend/app.py
```

By default, Flask starts on `http://127.0.0.1:5000`.

Key endpoints:

- `GET /` — health check (`status: running`)
- `GET /districts` — list of 38 Tamil Nadu districts
- `GET /commodities?district=<name>` — list of commodities
- `POST /analyse` — main analysis endpoint
- `GET /movers` — daily price movers for ticker
- `GET /seasonal` — seasonal calendar data

---

## 4. Running the Frontend

The frontend is a static single‑page app.

### 4.1 Simplest: open directly

1. Ensure the backend is running on `http://127.0.0.1:5000`.
2. Open `frontend/index.html` in your browser (double‑click or `File → Open`).

### 4.2 Using a simple static server (recommended)

This avoids CORS / file URL issues:

```bash
cd frontend
python -m http.server 8000
```

Then open:

- `http://127.0.0.1:8000/index.html`

---

## 5. How the Analysis Flow Works

1. User selects **user type**, **district**, and **commodity**, then clicks **“Analyse Market →”**.
2. Frontend calls `POST /analyse` with:
   - `user_type` (`producer` / `distributor` / `consumer`)
   - `district`
   - `commodity`
3. Backend:
   - `predict.py`:
     - Reads last 7–14 days from `mandi_prices`.
     - Computes weekly average, trend, tomorrow / day‑after predictions.
     - Evaluates harvest season and upcoming festivals.
     - Generates BUY/SELL/HOLD signal + reason.
   - `AI_advisory.py`:
     - Fetches 3‑day weather from OpenWeather.
     - Builds a Gemini prompt with all signals.
     - Calls Gemini to generate a concise advisory.
   - If **no DB data** is found:
     - Falls back to `gemini_search_price(...)`, which uses Gemini web search to estimate price + trend.
4. Frontend renders:
   - Advisory, signal badge.
   - Latest price, weekly average, confidence.
   - Price chart (7‑day history) using Chart.js.
   - Markets, 3‑day weather, and upcoming festivals.

---

## 6. Proof & Screenshots (replace with your images)

Create a `docs/` folder and add real screenshots, then update paths below.

```markdown
### Home — District & Commodity Selection
![Home selection](docs/home-selection.png)

### Analysis — AI Advisory & Price Chart
![Analysis page](docs/analysis-page.png)

### Seasonal Calendar
![Seasonal calendar](docs/seasonal-calendar.png)
```

Suggested screenshots:

- **Home selection**: district + commodity dropdowns, user type buttons, and ticker.
- **Analysis page**: full advisory card, stats, chart, markets, and weather.
- **Seasonal calendar**: grid of crops vs months with peak/lean coloring.

---

## 7. Deployment Notes

- **Backend**:
  - Use a production WSGI server (e.g., `gunicorn` or `uwsgi`) behind Nginx or similar.
  - Configure environment variables on the server instead of `.env` when possible.
  - Restrict access to API keys and database credentials.
- **Frontend**:
  - Can be served by any static hosting (GitHub Pages, Netlify, S3 + CloudFront, etc.).
  - Make sure `API_BASE` in `frontend/js/api.js` points to your deployed backend URL.

---

## 8. Contributing / Future Work

- Add user authentication and saved watchlists.
- Extend harvest calendar and festival data.
- Support additional states beyond Tamil Nadu.
- Add automated tests for prediction logic and advisory generation.

