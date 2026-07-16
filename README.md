# AgriPrice Intelligence 🌾
> An Enterprise-Grade Agricultural Analytics & Market Intelligence Platform for Tamil Nadu, India.

AgriPrice Intelligence is a real-time price monitoring, predictive analysis, and advisory system designed to optimize supply chain decisions for **Farmers**, **Traders**, and **Consumers**. The platform utilizes a robust Flask backend, a PostgreSQL relational database, real-time OpenWeather services, and generative Gemini AI to deliver actionable market intelligence.

---

## 🏗️ System Architecture & Workflow

The platform separates presentation and business logic using a decoupled **Frontend-Backend Client-Server Model**. 

### High-Level Workflow Diagram
```mermaid
graph TD
    Client[Web Frontend Client] <-->|HTTP REST / JSON| API[Flask API Gatekeeper]
    API <-->|SQL Queries| DB[(PostgreSQL Database)]
    API --->|JSON Config| MD[backend/metadata.json]
    API -->|Prompt Context| LLM[Google Gemini LLM]
    API -->|Live Conditions| W[OpenWeather API]
    ETL[ETL pipeline.py] -->|API Fetch| Agmarknet[Govt Agmarknet API]
    ETL -->|Parse & Clean| DB
```

---

## 📂 Project Structure

```bash
├── backend/
│   ├── app.py                  # Flask Application Factory & Server Entrypoint
│   ├── config.py               # Database connections and centralized Metadata configuration
│   ├── analytics.py            # Data access layer for analytics calculations
│   ├── metadata.json           # Single source of truth for districts, harvest cycles, & festivals
│   ├── etl/                    # Automated ETL Data Pipeline
│   │   ├── extractor.py        # Agmarknet Government API interface
│   │   ├── transformer.py      # Cleans, normalizes, and filters raw arrivals
│   │   ├── loader.py           # Loads records to database with conflict handling
│   │   ├── cleanup.py          # Enforces the 7-day rolling data retention policy
│   │   └── pipeline.py         # Orchestrates the ETL pipeline execution sequence
│   ├── routes/                 # Blueprint Endpoint Route Definitions
│   │   ├── advisory.py         # AI Advisory compilation & Gemini integration
│   │   ├── prices.py           # Exposes /api/config and market price feeds
│   │   ├── seasonal.py         # Seasonal profit-potential endpoint
│   │   └── weather.py          # Weather retrieval & mapping integration
│   └── sql/                    # Modularized Queries
│       ├── schema.sql          # Core DDL tables & database schema definitions
│       ├── prices.sql          # Filters and sorts active market listings
│       ├── seasonal_scoring.sql# Computes crop margins within rolling windows
│       └── price_trend_30day.sql# Aggregates price trends for the chart
├── frontend/                   # Static Frontend Files
│   ├── index.html              # Main Landing page & Dashboard
│   ├── prices.html             # Detailed Market Prices & Transport calculator
│   ├── seasonal.html           # Seasonal Crop Planner
│   ├── results.html            # AI Advisory Results page
│   ├── css/style.css           # Custom layout and component UI styles
│   └── js/
│       ├── api.js              # Centralized JavaScript client library for API calls
│       ├── index.js            # Controller script for index.html (loads config & weather)
│       ├── prices.js           # Chart generation, alert management, and distance calculations
│       └── seasonal.js         # Renders profit potentials and seasonal badges
```

---

## 🔄 Core Workflows

### 1. Application Initialization & Dynamic Configuration
To prevent code duplication, the frontend maintains no hardcoded config. Everything is driven dynamically:
```mermaid
sequenceDiagram
    participant Browser as Web Browser
    participant API as Flask backend
    participant Config as config.py
    participant Meta as metadata.json

    Browser->>API: GET /api/config
    API->>Config: Read loaded configuration
    Config->>Meta: Load JSON schema (Districts, Commodities, Festivals)
    API-->>Browser: JSON payload with sorted lists
    Browser->>Browser: Render custom dropdowns & upcoming festival calendars
```

### 2. Market Search & Personalised AI Advisory
When a user requests a market analysis:
1. **Weather Pull**: The backend calls the **OpenWeather API** to fetch live temperature, condition, and humidity for the selected district.
2. **Context Matching**: The backend pulls:
   * **Harvest Cycle**: Checks if the target crop is in its peak or lean harvest period (from `metadata.json`).
   * **Holiday Calendar**: Checks if any high-demand festivals are occurring within the next 3 days.
   * **State Comparison**: SQL pulls the highest, lowest, and average prices for the crop across all Tamil Nadu markets.
3. **Gemini Execution**: All gathered parameters (prices, state comparisons, weather, harvest phase, and festival demand) are compiled into a strict structured prompt. Gemini generates a 4-to-5 sentence actionable strategy (BUY/SELL/HOLD/STORE) tailored to the user's role (Farmer, Trader, or Consumer).

---

## 🚜 Automated ETL Pipeline Workflow

The ETL pipeline runs periodically (via cron triggers hitting `/run-fetch`) to sync local storage with government reports.

```mermaid
flowchart LR
    Start([Trigger Webhook]) --> Extract[Extractor: Fetch raw data from Agmarknet API]
    Extract --> Transform[Transformer: Filter only TN records, clean price text, format schemas]
    Transform --> Load[Loader: Upsert into commodity_prices table]
    Load --> Cleanup[Cleanup: Purge records older than 7 days]
    Cleanup --> End([ETL Complete])
```

* **Extractor**: Connects to the Government of India's Open Data API (`api.data.gov.in`) and extracts raw commodity arrivals.
* **Transformer**: Standardizes formatting, filters out non-Tamil Nadu listings, maps human-readable names, and casts numeric prices.
* **Loader**: Writes records into PostgreSQL using upsert syntax (`ON CONFLICT`) to prevent duplicate listings.
* **Cleanup**: Deletes historical data older than 7 days to maintain a lightweight, highly responsive, and storage-optimized database footprint.

---

## ⚡ System Design Decisions

### Optimized 7-Day Rolling Analytics
Because the database strictly retains only the **last 7 days** of data, traditional 30-day or 60-day historical baseline algorithms would fail or yield empty sets. 
To ensure the analytics engines remain highly functional under this storage footprint, the SQL calculations are optimized as follows:

* **Daily Trend Aggregation**: The line chart queries are constrained to a maximum window of `7 days`.
* **Seasonal Profit Potential**: Instead of comparing current prices to a month-old baseline, the seasonal scoring engine calculates margins by contrasting:
  * **Recent average**: The last **2 days** of commodity prices.
  * **Historical baseline**: The preceding **5 days** (days 3 through 7) of available data in the table.
  This allows the platform to correctly classify crops as **High (in_season)**, **Medium (upcoming)**, or **Low (avoid)** based on short-term price movements.

---

## 🚀 Local Setup & Running

### Prerequisites
* Python 3.10+
* PostgreSQL DB Instance

### Step 1: Clone & Configure Variables
Create a `.env` file in the root directory based on `.env.example`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/commodity_intelligence
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

### Step 2: Initialize Database Schema
Run the schema setup query from:
* `backend/sql/schema.sql`

### Step 3: Run the Application
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the Flask application:
   ```bash
   python -m backend.app
   ```
3. Open `http://127.0.0.1:5000` in your web browser.
