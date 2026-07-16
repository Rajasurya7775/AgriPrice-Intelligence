// js/prices.js
// Handles queries, target price alerts, volatility metrics, and transport estimation.

'use strict';

let districtCoords = {};
let commoditiesList = [];
let districtsList = [];
let trendChart = null;

function getDistance(c1, c2) {
  if (!c1 || !c2) return Infinity;
  const R = 6371;
  const dLat = (c2.lat - c1.lat) * Math.PI / 180;
  const dLon = (c2.lon - c1.lon) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(c1.lat * Math.PI / 180) * Math.cos(c2.lat * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function getClosestDistricts(target, count = 5) {
  const targetCoord = districtCoords[target];
  if (!targetCoord) return [];
  return Object.keys(districtCoords)
    .filter(name => name.toLowerCase() !== target.toLowerCase())
    .map(name => ({
      name,
      distance: getDistance(targetCoord, districtCoords[name])
    }))
    .sort((a, b) => a.distance - b.distance)
    .slice(0, count);
}

function checkPriceAlerts(commodity, district, currentPriceKg) {
  const alerts = JSON.parse(localStorage.getItem("price_alerts") || "[]");
  const matching = alerts.filter(a =>
    a.commodity.toLowerCase() === commodity.toLowerCase() &&
    a.district.toLowerCase() === district.toLowerCase()
  );

  const alertContainer = document.getElementById("triggeredAlertsContainer");
  alertContainer.innerHTML = "";

  matching.forEach(alert => {
    const target = parseFloat(alert.targetPrice);
    const direction = alert.direction;
    let triggered = false;

    if (direction === "above" && currentPriceKg > target) triggered = true;
    if (direction === "below" && currentPriceKg < target) triggered = true;

    if (triggered) {
      const alertDiv = document.createElement("div");
      alertDiv.className = "p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl text-red-800 text-sm font-semibold flex items-center justify-between";
      alertDiv.innerHTML = `
        <span>🔔 Alert Triggered: ${commodity} in ${district} went ${direction} your target of ₹${target}/kg (Current: ₹${currentPriceKg.toFixed(2)}/kg)</span>
        <button class="text-red-900 hover:underline text-xs" onclick="removeAlert(${alert.id})">Dismiss</button>
      `;
      alertContainer.appendChild(alertDiv);
    }
  });
}

function removeAlert(id) {
  let alerts = JSON.parse(localStorage.getItem("price_alerts") || "[]");
  alerts = alerts.filter(a => a.id !== id);
  localStorage.setItem("price_alerts", JSON.stringify(alerts));
  renderAlertsList();
  analyzeMarketPrices();
}

window.removeAlert = removeAlert;

function renderAlertsList() {
  const list = document.getElementById("activeAlertsList");
  const alerts = JSON.parse(localStorage.getItem("price_alerts") || "[]");
  if (alerts.length === 0) {
    list.innerHTML = `<p class="text-xs text-gray-400">No active alerts set.</p>`;
    return;
  }
  list.innerHTML = alerts.map(a => `
    <div class="flex items-center justify-between p-2.5 bg-slate-50 border rounded-xl text-xs mt-1.5 font-semibold">
      <span><strong>${a.commodity}</strong> in <strong>${a.district}</strong> (${a.direction} ₹${a.targetPrice}/kg)</span>
      <button class="text-red-600 hover:text-red-800 font-bold" onclick="removeAlert(${a.id})">✕</button>
    </div>
  `).join("");
}

document.getElementById("btnSaveAlert").addEventListener("click", () => {
  const commodity = document.getElementById("alertCommodity").value;
  const district = document.getElementById("alertDistrict").value;
  const targetPrice = parseFloat(document.getElementById("alertPrice").value);
  const direction = document.getElementById("alertDirection").value;

  if (!commodity || !district || isNaN(targetPrice)) {
    showToast("Please fill in all alert fields", "error");
    return;
  }

  const alerts = JSON.parse(localStorage.getItem("price_alerts") || "[]");
  alerts.push({
    id: Date.now(),
    commodity,
    district,
    targetPrice,
    direction
  });
  localStorage.setItem("price_alerts", JSON.stringify(alerts));
  renderAlertsList();
  showToast("Price Alert Set!", "success");
  analyzeMarketPrices();
});

async function analyzeMarketPrices() {
  const commodity = document.getElementById("pricesCommodity").value;
  const district = document.getElementById("pricesDistrict").value;

  if (!commodity || !district) return;

  // Sync with price alert card selectors
  const alertComm = document.getElementById("alertCommodity");
  const alertDist = document.getElementById("alertDistrict");
  if (alertComm) alertComm.value = commodity;
  if (alertDist) alertDist.value = district;

  document.getElementById("loadingIndicator").classList.remove("hidden");
  document.getElementById("pricesContent").classList.add("hidden");

  const chartTitle = document.getElementById("chartTitle");
  if (chartTitle) chartTitle.textContent = `7-Day Trend — ${commodity}`;

  try {
    const pricesResp = await fetchPrices(commodity, "farmer");
    const allPrices = pricesResp.prices || [];
    const localPrices = allPrices.filter(p => p.district && p.district.toLowerCase() === district.toLowerCase());

    const isMiss = localPrices.length === 0;

    if (isMiss) {
      document.getElementById("pricesLocalCard").innerHTML = `
        <div class="p-6 text-center text-gray-500">
          <p class="font-bold text-sm">No price data recorded in ${district} for ${commodity}.</p>
          <p class="text-xs mt-1">Check nearby districts or view Tamil Nadu average rates below.</p>
        </div>
      `;
      document.getElementById("volatilityBadge").className = "hidden";
    } else {
      const primary = localPrices[0];
      const modal = parseFloat(primary.modal_price);
      const min = parseFloat(primary.min_price);
      const max = parseFloat(primary.max_price);
      const modalKg = modal / 100;

      const spreadPct = ((max - min) / (modal || 1)) * 100;
      const volBadge = document.getElementById("volatilityBadge");
      volBadge.classList.remove("hidden");
      if (spreadPct > 12) {
        volBadge.textContent = "Volatile Prices";
        volBadge.className = "text-xs px-2.5 py-1 rounded-full font-bold bg-red-100 text-red-800";
      } else {
        volBadge.textContent = "Stable Prices";
        volBadge.className = "text-xs px-2.5 py-1 rounded-full font-bold bg-[#f3f7ed] text-green-800 border border-[#d4e2be]";
      }

      document.getElementById("pricesLocalCard").innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-semibold">
          <div class="bg-[#f3f7ed] border border-[#d4e2be] p-5 rounded-2xl flex justify-between items-center">
            <div>
              <span class="text-[9px] text-green-700 uppercase tracking-wider block">Price per Quintal</span>
              <h3 class="text-3xl md:text-4xl font-black text-green-950 mt-1">₹${modal.toLocaleString('en-IN')}</h3>
            </div>
            <span class="text-xs font-extrabold text-[#27500A]">${primary.market} Market</span>
          </div>
          <div class="bg-blue-50 border border-blue-100 p-6 rounded-2xl flex justify-between items-center shadow-sm">
            <div>
              <span class="text-[10px] text-blue-800 uppercase tracking-wider font-extrabold block">Price per Kilogram</span>
              <h3 class="text-3xl md:text-4xl font-black text-blue-950 mt-1">₹${modalKg.toFixed(2)}/kg</h3>
            </div>
            <span class="text-xs text-gray-500 font-extrabold bg-white border border-gray-200 px-3 py-1.5 rounded-full">Range: ₹${(min / 100).toFixed(2)} - ₹${(max / 100).toFixed(2)}/kg</span>
          </div>
        </div>
      `;

      checkPriceAlerts(commodity, district, modalKg);
    }

    const chartCanvas = document.getElementById("pricesTrendChart");
    const analytics = await fetchAnalytics(commodity).catch(() => null);

    if (trendChart) {
      trendChart.destroy();
      trendChart = null;
    }

    if (analytics && analytics.trend_labels && analytics.trend_prices && analytics.trend_labels.length > 0) {
      const labels = analytics.trend_labels.slice(-7);
      const prices = analytics.trend_prices.slice(-7).map(p => p / 100);

      trendChart = new Chart(chartCanvas, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: `${commodity} Price (₹/Kg)`,
            data: prices,
            borderColor: '#27500A',
            backgroundColor: 'rgba(39, 80, 10, 0.04)',
            borderWidth: 2.5,
            tension: 0.35,
            fill: true,
            pointBackgroundColor: '#27500A',
            pointBorderColor: '#27500A',
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: { 
              grid: { color: '#f1f5f9' }, 
              ticks: { 
                callback: function(v) { 
                  return '₹' + Number(v * 100).toLocaleString('en-IN') + ' (₹' + v + '/kg)';
                } 
              } 
            },
            x: { grid: { display: false } }
          }
        }
      });
    } else {
      chartCanvas.parentNode.innerHTML = `<div class="flex items-center justify-center h-48 text-gray-400 text-xs">7-Day trend chart unavailable.</div>`;
    }

    const neighbors = getClosestDistricts(district, 5);
    const neighborsContainer = document.getElementById("neighboringComparisons");
    neighborsContainer.innerHTML = "";

    neighbors.forEach(n => {
      const distPrices = allPrices.filter(p => p.district && p.district.toLowerCase() === n.name.toLowerCase());
      let priceInfo = "No Live Data";
      let priceVal = 0;
      if (distPrices.length > 0) {
        priceVal = parseFloat(distPrices[0].modal_price) / 100;
        priceInfo = `₹${parseFloat(distPrices[0].modal_price).toLocaleString('en-IN')} / Quintal`;
      }

      const card = document.createElement("div");
      card.className = "w-full bg-[#f3f7ed] border border-[#d4e2be] rounded-2xl p-4 flex items-center justify-between text-xs transition hover:shadow-sm";
      card.innerHTML = `
        <div>
          <span class="font-extrabold text-[#27500A] text-sm block">${n.name}</span>
          <span class="text-gray-400 font-semibold block mt-0.5">${Math.round(n.distance)} km away</span>
        </div>
        <div class="text-right space-y-0.5">
          <strong class="text-[#27500A] text-[11px] font-black block">${priceInfo}</strong>
          <strong class="text-[#27500A] text-sm font-black block">${priceVal ? '₹' + priceVal.toFixed(2) + ' / kg' : '—'}</strong>
          <span class="text-[9px] text-gray-400 font-bold block">Transport ~₹${(n.distance * 1.5).toFixed(0)}/quintal</span>
        </div>
      `;
      neighborsContainer.appendChild(card);
    });

    const tableBody = document.getElementById("comparisonTableBody");
    if (allPrices.length > 0) {
      tableBody.innerHTML = allPrices.map(item => {
        const trend = item.trend_analysis || "Stable";
        const icon = { Rising: "↑", Falling: "↓", Stable: "—" }[trend] || "—";
        const color = { Rising: "text-green-600 font-bold", Falling: "text-red-600 font-bold", Stable: "text-gray-400 font-bold" }[trend] || "text-gray-400";
        return `
          <tr class="border-b border-gray-100 text-base hover:bg-gray-50/50 transition-colors">
            <td class="py-3.5 px-4 font-bold text-gray-800">${item.market}</td>
            <td class="py-3.5 px-4 text-gray-400 font-semibold">${item.district}</td>
            <td class="py-3.5 px-4 text-right font-extrabold text-gray-850">₹${Number(item.modal_price).toLocaleString('en-IN')}</td>
            <td class="py-3.5 px-4 text-right font-black text-sm text-[#27500A]">₹${(item.modal_price / 100).toFixed(2)} / kg</td>
            <td class="py-3.5 px-4 text-center font-extrabold ${color}">${icon}</td>
          </tr>
        `;
      }).join("");
    } else {
      tableBody.innerHTML = `<tr><td colspan="5" class="py-4 text-center text-gray-400 text-xs">No Tamil Nadu records found.</td></tr>`;
    }

    document.getElementById("loadingIndicator").classList.add("hidden");
    document.getElementById("pricesContent").classList.remove("hidden");

  } catch (err) {
    console.error(err);
    document.getElementById("loadingIndicator").classList.add("hidden");
  }
}

window.analyzeMarketPrices = analyzeMarketPrices;

async function initConfig() {
  try {
    const cfg = await fetchConfig();
    districtCoords = cfg.district_coords || {};
    districtsList = cfg.districts || [];

    commoditiesList = [];
    (cfg.commodities || []).forEach(group => {
      group.items.forEach(i => commoditiesList.push(i.value));
    });

    const elements = {
      alertCommodity: commoditiesList,
      alertDistrict: districtsList,
      pricesCommodity: commoditiesList,
      pricesDistrict: districtsList
    };

    for (const [id, list] of Object.entries(elements)) {
      document.getElementById(id).innerHTML = list.map(item => `<option value="${item}">${item}</option>`).join("");
    }

    const urlParams = new URLSearchParams(window.location.search);
    const q = urlParams.get("q") || "Tomato";
    const d = urlParams.get("district") || "Madurai";

    document.getElementById("pricesCommodity").value = q;
    document.getElementById("pricesDistrict").value = d;

    if (q && d) {
      sessionStorage.setItem('selected_commodity_label', q);
      sessionStorage.setItem('selected_commodity_value', q);
      sessionStorage.setItem('selected_district_label', d);
      sessionStorage.setItem('selected_district_value', d);
    }

    renderAlertsList();
    analyzeMarketPrices();
  } catch (err) {
    console.error("Config failed:", err);
  }
}

document.addEventListener("DOMContentLoaded", initConfig);
