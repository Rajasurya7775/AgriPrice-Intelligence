// js/seasonal.js
// Handles loading and rendering seasonal crop suggestions.

'use strict';

function profitBadge(level) {
  const map = {
    High: "bg-green-100 text-green-800",
    Medium: "bg-yellow-100 text-yellow-800",
    Low: "bg-gray-100 text-gray-800"
  };
  const labelKey = { High: "seasonal_high", Medium: "seasonal_medium", Low: "seasonal_low" };
  return `<span class="text-xs px-2.5 py-1 rounded-full font-bold ${map[level] || map.Low}" data-i18n="${labelKey[level]}">${level}</span>`;
}

function trendBadge(trend, strength) {
  const icon = { Rising: "↑", Falling: "↓", Stable: "→" }[trend] || "→";
  const col = { Rising: "bg-green-100 text-green-800", Falling: "bg-red-100 text-red-800", Stable: "bg-yellow-100 text-yellow-800" }[trend] || "bg-gray-100 text-gray-600";
  return `<span class="text-[10px] px-2 py-0.5 rounded-full ${col} font-medium">${icon} ${trend} · ${strength}</span>`;
}

function renderSeasonalCard(item) {
  // Convert price from per-quintal average to per-kg average for presentation
  const priceKg = (parseFloat(item.avg_price || 0) / 100).toFixed(2);
  return `
    <div class="bg-white border rounded-xl p-4 flex justify-between items-center mb-2.5 shadow-sm">
      <div>
        <p class="font-bold text-sm text-gray-900">${item.commodity}</p>
        <div class="flex gap-2 mt-1 flex-wrap">
          ${trendBadge(item.trend_analysis || "Stable", item.trend_strength || "Moderate")}
        </div>
      </div>
      <div class="text-right flex flex-col items-end gap-1">
        ${profitBadge(item.profit_potential)}
        <span class="text-xs text-gray-400">₹${priceKg}/kg</span>
      </div>
    </div>
  `;
}

async function loadSeasonal() {
  try {
    const data = await fetchSeasonal();
    const inSeason = data.filter(d => d.status === "in_season");
    const upcoming = data.filter(d => d.status === "upcoming");
    const avoid = data.filter(d => d.status === "avoid");

    document.getElementById("inSeasonList").innerHTML =
      inSeason.length ? inSeason.map(renderSeasonalCard).join("") : '<p class="text-gray-400 text-xs py-2">No crops in season.</p>';
    document.getElementById("upcomingList").innerHTML =
      upcoming.length ? upcoming.map(renderSeasonalCard).join("") : '<p class="text-gray-400 text-xs py-2">No upcoming crops.</p>';
    document.getElementById("avoidList").innerHTML =
      avoid.length ? avoid.map(renderSeasonalCard).join("") : '<p class="text-gray-400 text-xs py-2">No crops to avoid.</p>';

    applyTranslations(currentLang);
  } catch (e) {
    console.error(e);
    ["inSeasonList", "upcomingList", "avoidList"].forEach(id => {
      document.getElementById(id).innerHTML = '<p class="text-gray-400 text-xs py-2">Could not load seasonal data.</p>';
    });
  }
}

document.addEventListener("DOMContentLoaded", loadSeasonal);
