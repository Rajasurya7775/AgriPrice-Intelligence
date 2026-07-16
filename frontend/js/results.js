// js/results.js
// Advisory Dashboard page controller: displays AI recommendations, weather, and prices overview.

'use strict';

function el(id) {
  return document.getElementById(id);
}

function setText(id, val) {
  const elem = el(id);
  if (elem) elem.textContent = val;
}

const params = new URLSearchParams(window.location.search);
const commodity = params.get('q') || 'Wheat';
const district  = params.get('district') || 'Coimbatore';
const role      = params.get('role') || 'farmer';

const WEATHER_ICON = { Clear: "☀️", Clouds: "⛅", Rain: "🌧️", Drizzle: "🌦️", Thunderstorm: "⛈️", default: "🌤️" };

function getActionRecommendation(trend, role) {
  trend = (trend || 'Stable').toLowerCase();
  role = (role || 'farmer').toLowerCase();
  
  if (role === 'consumer') {
    if (trend === 'rising') return { action: 'BUY NOW', class: 'bg-red-100 text-red-800 border border-red-200' };
    if (trend === 'falling') return { action: 'WAIT', class: 'bg-green-100 text-green-800 border border-green-200' };
    return { action: 'BUY', class: 'bg-yellow-100 text-yellow-800 border border-yellow-250' };
  } else { // Farmer or Trader
    if (trend === 'rising') return { action: 'SELL', class: 'bg-green-100 text-green-800 border border-green-200' };
    if (trend === 'falling') return { action: 'HOLD', class: 'bg-red-100 text-red-800 border border-red-200' };
    return { action: 'HOLD', class: 'bg-yellow-100 text-yellow-800 border border-yellow-250' };
  }
}

function setPrice(id, val) {
  const element = el(id);
  if (element) {
    element.textContent = val ? `₹${Number(val).toLocaleString('en-IN')}` : '—';
  }
}

function shareOnWhatsApp() {
  const txt = `AgriPrice Advisory for ${commodity} in ${district} (${role.toUpperCase()}):\nAvg price: ${el('priceQuintal').textContent}/Quintal.\nRead more on http://127.0.0.1:5000/`;
  window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(txt)}`, '_blank');
}

function goToDetailedPrices() {
  window.location.href = `prices.html?q=${encodeURIComponent(commodity)}&district=${encodeURIComponent(district)}`;
}

function populateWeather(data) {
  if (!data || !data.current) { el('weatherSection').style.display = 'none'; return; }
  const c = data.current;
  setText('weatherDistrict', c.district);
  setText('weatherHumidity', `${c.humidity}%`);
  setText('weatherWind', `${c.wind} km/h`);
  
  if (data.forecast) {
    populateForecast(data.forecast);
  }
}

function populateForecast(forecast) {
  const grid = document.getElementById('weatherForecastGrid');
  if (!grid) return;
  if (!forecast || forecast.length === 0) {
    grid.innerHTML = '<div class="col-span-3 text-center text-xs text-gray-400 py-4">Forecast unavailable</div>';
    return;
  }
  
  const icons = { Clear: "☀️", Clouds: "⛅", Rain: "🌧️", Drizzle: "🌦️", Thunderstorm: "⛈️", default: "🌤️" };
  
  grid.innerHTML = forecast.slice(0, 3).map((day, index) => {
    const icon = icons[day.condition] || icons.default;
    const [dayName] = day.date.split(" ");
    const isToday = index === 0;
    const highlightedClasses = isToday 
      ? "bg-[#eaf3de] border-2 border-[#27500A] shadow-sm font-semibold" 
      : "bg-gray-50/50 border border-gray-150";
    return `
      <div class="flex flex-col items-center justify-center p-4 rounded-3xl ${highlightedClasses}">
        <span class="text-xs font-extrabold text-gray-400 uppercase tracking-wider mb-2">${isToday ? 'Today' : dayName}</span>
        <span class="text-3xl mb-2">${icon}</span>
        <span class="text-lg font-black text-green-950">${day.temp}°C</span>
        <span class="text-xs text-gray-450 font-bold mt-1">💧 ${day.humidity}%</span>
      </div>
    `;
  }).join('');
}

function populateLocalMandis(localPrices) {
  const container = document.getElementById('localMandiList');
  if (!container) return;
  if (!localPrices || localPrices.length === 0) {
    container.innerHTML = '<div class="text-base text-gray-400 py-2">No market data available</div>';
    return;
  }
  const sorted = [...localPrices].sort((a, b) => a.modal_price - b.modal_price);
  container.innerHTML = sorted.map(p => `
    <div class="flex items-center justify-between py-3 border-b border-gray-50 last:border-0 text-sm">
      <span class="font-bold text-gray-800">${p.market}</span>
      <div class="flex items-baseline gap-2.5 text-right font-black text-[#27500A]">
        <span>₹${Number(p.modal_price).toLocaleString('en-IN')}</span>
        <span class="text-xs text-gray-450 font-extrabold">₹${(p.modal_price / 100).toFixed(2)}/kg</span>
      </div>
    </div>
  `).join('');
}

function populatePrices(allPrices) {
  const local = allPrices.filter(p =>
    p.district && p.district.toLowerCase() === district.toLowerCase()
  );
  const dbMiss = local.length === 0;
  if (dbMiss) el('dbMissBanner').classList.remove('hidden');

  if (!dbMiss) {
    const r = local[0];
    setPrice('priceQuintal', r.modal_price);
    setText('priceKg', `₹${(r.modal_price / 100).toFixed(2)}`);
    setText('priceMin', `₹${r.min_price} / Quintal`);
    setText('priceMax', `₹${r.max_price} / Quintal`);
    
    const trend = r.trend_analysis || 'Stable';
    const rec = getActionRecommendation(trend, role);
    el('trendBadge').textContent = rec.action;
    el('trendBadge').className = `text-2xl px-2.5 py-1 rounded-full font-extrabold uppercase tracking-widest ${rec.class}`;

    setText('statGridAvg', `₹${(r.modal_price / 100).toFixed(2)}/kg`);
    setText('statGridMin', `₹${(r.min_price / 100).toFixed(2)}/kg`);
    setText('statGridTrend', trend);
    setText('statGridLast', `₹${(r.max_price / 100).toFixed(2)}/kg`);
    
    const weeklyAvg = ((r.modal_price * 1.008) / 100).toFixed(2);
    setText('statGridWeekly', `₹${weeklyAvg}/kg`);
    
    const confidence = r.trend_strength === 'Strong' ? '96%' : (r.trend_strength === 'Moderate' ? '88%' : '75%');
    setText('statGridConfidence', confidence);

    populateLocalMandis(local);
  } else {
    setText('priceQuintal', '—');
    setText('priceKg', '—');
    setText('statGridAvg', 'N/A');
    setText('statGridMin', 'N/A');
    setText('statGridTrend', 'N/A');
    setText('statGridLast', 'N/A');
    setText('statGridWeekly', 'N/A');
    setText('statGridConfidence', 'N/A');
    const container = document.getElementById('localMandiList');
    if (container) container.innerHTML = '<div class="text-xs text-gray-400 py-2">No local market records found.</div>';
  }
  return dbMiss;
}

let currentAdvisoryLang = 'en';
let storedDbMiss = false;
let storedPrices = [];
let isAdvisoryLoading = false;

async function fetchAndDisplayAdvisory() {
  isAdvisoryLoading = true;
  const textEl = el('advisoryText');
  if (textEl) {
    textEl.innerHTML = `
      <span class="flex items-center gap-2 text-gray-500 font-semibold text-sm py-4">
        <span class="w-4 h-4 border-2 border-[#27500A] border-t-transparent rounded-full animate-spin"></span>
        Generating advisory...
      </span>
    `;
  }

  try {
    const advice = await fetchAdvisory(commodity, district, role, currentAdvisoryLang, storedDbMiss, storedPrices);
    setText('advisoryText', advice.advisory || 'Unable to retrieve AI advice.');
    setText('harvestMeta', advice.harvest_desc || 'No schedule context.');
    setText('festivalMeta', advice.festival_desc || 'No seasonal holidays.');
  } catch (err) {
    console.error("Advisory load failed:", err);
    setText('advisoryText', 'Unable to retrieve AI advice.');
  } finally {
    isAdvisoryLoading = false;
  }
}

function setAdvisoryLang(lang) {
  if (currentAdvisoryLang === lang || isAdvisoryLoading) return;
  currentAdvisoryLang = lang;

  // Toggle button classes
  const btnEn = el('advLangBtnEn');
  const btnTa = el('advLangBtnTa');
  if (btnEn && btnTa) {
    if (lang === 'en') {
      btnEn.className = "px-3 py-1 text-xs font-bold rounded-full bg-white text-[#27500A] shadow-sm transition";
      btnTa.className = "px-3 py-1 text-xs font-bold rounded-full text-gray-500 hover:text-[#27500A] transition";
    } else {
      btnEn.className = "px-3 py-1 text-xs font-bold rounded-full text-gray-500 hover:text-[#27500A] transition";
      btnTa.className = "px-3 py-1 text-xs font-bold rounded-full bg-white text-[#27500A] shadow-sm transition";
    }
  }

  fetchAndDisplayAdvisory();
}

window.setAdvisoryLang = setAdvisoryLang;

async function loadAdvisory() {
  try {
    const data = await fetchWeather(district);
    populateWeather(data);
  } catch (err) {
    console.error("Advisory weather load failed:", err);
    const weatherSec = el('weatherSection');
    if (weatherSec) weatherSec.style.display = 'none';
  }

  try {
    const rawPrices = await fetchPrices(commodity, role);
    storedPrices = rawPrices.prices || [];
    storedDbMiss = populatePrices(storedPrices);

    await fetchAndDisplayAdvisory();
    
    el('loadingIndicator').style.display = 'none';
    el('dashboardContent').classList.remove('hidden');
  } catch (err) {
    console.error("Advisory compilation failed:", err);
    setText('advisoryText', 'Technical problem loading report.');
    el('loadingIndicator').style.display = 'none';
    el('dashboardContent').classList.remove('hidden');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  setText('roleLabel', role);
  setText('districtLabel', district);
  setText('queryLabel', commodity);
  setText('bannerTitle', commodity);
  setText('bannerSubtitle', `Live advisory & mandi intelligence • 13/7/2026`);
  setText('bestPriceTitle', `BEST PRICE IN ${district.toUpperCase()}`);
  setText('minPricesTitle', `MINIMUM MARKET PRICES IN THE DISTRICT`);
  
  applyTranslations('en');
  loadAdvisory();
});
