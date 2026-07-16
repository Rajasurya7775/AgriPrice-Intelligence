// ui.js — UI rendering helpers


function renderWeatherCard(w) {
  const icons = { Clear: "☀️", Clouds: "⛅", Rain: "🌧️", Drizzle: "🌦️", Thunderstorm: "⛈️", default: "🌤️" };
  const icon = icons[w.condition] || icons.default;
  return `
    <div class="weather-card bg-white rounded-xl p-4 border border-gray-100 shadow-sm">
      <div class="flex justify-between items-center">
        <div>
          <p class="font-semibold text-gray-800">${w.district}</p>
          <p class="text-xs text-gray-400">${w.condition}</p>
        </div>
        <div class="text-right">
          <span class="text-3xl">${icon}</span>
          <p class="text-lg font-bold text-green-800">${w.temp}°C</p>
        </div>
      </div>
      <div class="flex gap-3 mt-2 text-xs text-gray-500">
        <span>💧 ${w.humidity}%</span>
        <span>🌬️ ${w.wind} km/h</span>
      </div>
    </div>
  `;
}

function showToast(msg, type = "info") {
  const colors = { info: "bg-blue-600", success: "bg-green-600", error: "bg-red-600" };
  const toast = document.createElement("div");
  toast.className = `fixed bottom-4 right-4 ${colors[type]} text-white px-4 py-2 rounded-xl shadow-lg z-50 text-sm transition-all`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

