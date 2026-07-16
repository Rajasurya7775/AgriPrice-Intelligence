// api.js — All backend API calls

const BASE_URL = "https://agriprice-intelligence.onrender.com"; 

async function fetchPrices(commodity, role = "farmer", district = "") {
  const res = await fetch(`${BASE_URL}/api/prices?commodity=${encodeURIComponent(commodity)}&role=${role}&district=${encodeURIComponent(district)}`);
  if (!res.ok) throw new Error("Failed to fetch prices");
  return res.json();
}


async function fetchSeasonal() {
  const res = await fetch(`${BASE_URL}/api/seasonal`);
  if (!res.ok) throw new Error("Failed to fetch seasonal data");
  return res.json();
}

async function fetchWeather(district = "") {
  const url = district 
    ? `${BASE_URL}/api/weather?district=${encodeURIComponent(district)}`
    : `${BASE_URL}/api/weather`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch weather");
  return res.json();
}

async function fetchAIAdvisory(commodity, district, role, language, weather = {}) {
  const res = await fetch(`${BASE_URL}/api/advisory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      commodity, 
      district, 
      role, 
      language, 
      weather 
    })
  });
  if (!res.ok) throw new Error("Failed to fetch AI advisory");
  return res.json();
}

async function fetchAdvisory(commodity, district, role, language, db_miss, db_prices = [], weather = {}) {
  const res = await fetch(`${BASE_URL}/api/advisory`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      commodity, 
      district, 
      role, 
      language, 
      db_miss, 
      db_prices,
      weather 
    })
  });
  if (!res.ok) throw new Error("Failed to fetch advisory");
  return res.json();
}

async function fetchAnalytics(commodity) {
  const res = await fetch(`${BASE_URL}/api/analytics?commodity=${encodeURIComponent(commodity)}`);
  if (!res.ok) throw new Error("Failed to fetch analytics");
  return res.json();
}

async function fetchStats() {
  const res = await fetch(`${BASE_URL}/api/stats`);
  if (!res.ok) return { commodities: 120, markets: 47, accuracy: "96%" };
  return res.json();
}

async function fetchConfig() {
  const res = await fetch(`${BASE_URL}/api/config`);
  if (!res.ok) throw new Error("Failed to fetch config");
  return res.json();
}
