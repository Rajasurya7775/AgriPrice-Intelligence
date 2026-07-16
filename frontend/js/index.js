// js/index.js
// Home page controller: manages dropdown options and parameters configuration.

'use strict';

let selectedRole = 'farmer';
let commoditiesData = {};
let districtsData = [];

function selectRole(el) {
  document.querySelectorAll('.role-card').forEach(c => c.classList.remove('border-[#27500A]', 'bg-[#eaf3de]'));
  document.querySelectorAll('.role-card').forEach(c => c.classList.add('border-gray-200'));
  
  el.classList.add('border-[#27500A]', 'bg-[#eaf3de]');
  el.classList.remove('border-gray-200');
  selectedRole = el.dataset.role;
  sessionStorage.setItem('selected_role', selectedRole);
}

function _buildSearchInput(dropdownId) {
  return `<div class="p-2 border-b border-gray-150 sticky top-0 bg-white z-20">
    <input type="text"
           class="w-full p-2 border rounded-md text-xs outline-none"
           placeholder="Type to search..."
           oninput="filterDropdown('${dropdownId}', this.value)"/>
  </div>`;
}

function populateCommodities() {
  const dropdown = document.getElementById('commodityDropdown');
  let html = _buildSearchInput('commodityDropdown');
  commoditiesData.forEach(group => {
    const category = group.category;
    const items = group.items;
    if (items.length === 0) return;
    html += `<div class="custom-select-group-header">${category}</div>`;
    items.forEach(item => {
      html += `<div class="custom-select-option"
                    data-val="${item.value}"
                    onclick="selectItem('commodity', '${item.name}', '${item.value}')">
                 ${item.name}
               </div>`;
    });
  });
  dropdown.innerHTML = html;
}

function populateDistricts() {
  const dropdown = document.getElementById('districtDropdown');
  let html = _buildSearchInput('districtDropdown');
  districtsData.forEach(dist => {
    html += `<div class="custom-select-option"
                  data-val="${dist}"
                  onclick="selectItem('district', '${dist}', '${dist}')">
               ${dist}
             </div>`;
  });
  dropdown.innerHTML = html;
}

function toggleDropdown(containerId) {
  const container = document.getElementById(containerId);
  const isOpen = container.classList.contains('open');
  document.querySelectorAll('.relative').forEach(c => c.classList.remove('open'));
  if (!isOpen) {
    container.classList.add('open');
    const searchBox = container.querySelector('input[type="text"]:not(#commoditySelectInput):not(#districtSelectInput)');
    if (searchBox) {
      searchBox.value = '';
      searchBox.focus();
      filterDropdown(container.querySelector('.dropdown-box').id, '');
    }
  }
}

function filterDropdown(dropdownId, query) {
  const dropdown = document.getElementById(dropdownId);
  const q = query.toLowerCase();
  dropdown.querySelectorAll('.custom-select-option').forEach(opt => {
    opt.style.display = opt.textContent.toLowerCase().includes(q) ? 'block' : 'none';
  });
  dropdown.querySelectorAll('.custom-select-group-header').forEach(header => {
    let sibling = header.nextElementSibling;
    let hasVisible = false;
    while (sibling && sibling.classList.contains('custom-select-option')) {
      if (sibling.style.display !== 'none') { hasVisible = true; break; }
      sibling = sibling.nextElementSibling;
    }
    header.style.display = hasVisible ? 'block' : 'none';
  });
}

function selectItem(type, label, value) {
  document.getElementById(`${type}SelectInput`).value = label;
  document.getElementById(`${type}HiddenVal`).value   = value;
  document.getElementById(`${type}Container`).classList.remove('open');
  sessionStorage.setItem('selected_' + type + '_label', label);
  sessionStorage.setItem('selected_' + type + '_value', value);
  if (type === 'district') {
    loadWeather();
  }
}

document.addEventListener('click', e => {
  if (!e.target.closest('.relative')) {
    document.querySelectorAll('.relative').forEach(c => c.classList.remove('open'));
  }
});

window.addEventListener('languageChanged', () => {
  populateCommodities();
  populateDistricts();
});

function triggerAnalysis() {
  const commodity = document.getElementById('commodityHiddenVal').value;
  const district  = document.getElementById('districtHiddenVal').value;

  if (!commodity) { showToast(t('error_no_commodity'), 'error'); return; }
  if (!district)  { showToast(t('error_no_district'),  'error'); return; }

  window.location.href =
    `results.html?q=${encodeURIComponent(commodity)}&district=${encodeURIComponent(district)}&role=${selectedRole}&lang=${currentLang}`;
}

async function loadWeather() {
  try {
    const data = await fetchWeather();
    if (!data.weather || data.weather.length === 0) {
      document.getElementById('weatherSection').style.display = 'none';
      return;
    }
    document.getElementById('weatherSection').style.display = 'block';

    const activeDistrict = document.getElementById('districtHiddenVal').value || sessionStorage.getItem('selected_district_value') || 'Coimbatore';
    const active = data.weather.find(w => w.district.toLowerCase() === activeDistrict.toLowerCase()) || data.weather[0];
    
    if (active) {
      document.getElementById('selectedWeatherDistrict').textContent = active.district;
      document.getElementById('selectedWeatherTemp').textContent = `${active.temp}°C`;
      document.getElementById('selectedWeatherHumidity').textContent = `${active.humidity}%`;
      document.getElementById('selectedWeatherWind').textContent = `${active.wind} km/h`;
      
      const icons = { Clear: "☀️", Clouds: "⛅", Rain: "🌧️", Drizzle: "🌦️", Thunderstorm: "⛈️", default: "🌤️" };
      document.getElementById('selectedWeatherIcon').textContent = icons[active.condition] || icons.default;
    }

    const others = data.weather.filter(w => w.district.toLowerCase() !== active.district.toLowerCase());
    const otherGrid = document.getElementById('otherWeatherGrid');
    const icons = { Clear: "☀️", Clouds: "⛅", Rain: "🌧️", Drizzle: "🌦️", Thunderstorm: "⛈️", default: "🌤️" };
    
    otherGrid.innerHTML = others.map(w => {
      const icon = icons[w.condition] || icons.default;
      return `
        <div class="flex-shrink-0 w-32 bg-[#fafaf7] border border-gray-150 rounded-2xl p-3 shadow-sm text-center">
          <span class="text-[9px] font-bold text-gray-400 uppercase tracking-wider block mb-1">${w.district}</span>
          <span class="text-2xl block my-1">${icon}</span>
          <span class="text-xs font-black text-[#27500A] block">${w.temp}°C</span>
          <span class="text-[8px] font-bold text-gray-400 mt-1 block">💧 ${w.humidity}% · ${w.wind}k</span>
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error("Weather load failed:", err);
    document.getElementById('weatherSection').style.display = 'none';
  }
}

function formatFestivalDate(dateStr) {
  if (!dateStr || dateStr === "VARIES") return "Upcoming";
  const [m, d] = dateStr.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[m-1]} ${d}`;
}

function populateFestivals(festivals) {
  const container = document.getElementById('festivalsContainer');
  if (!festivals || festivals.length === 0) {
    container.innerHTML = '<p class="text-xs text-gray-400">No upcoming festivals.</p>';
    return;
  }
  
  const defaultHighlights = {
    VERY_HIGH: "+15% vegetables & spices demand",
    HIGH: "+10% cereals & fruits demand",
    MEDIUM: "+5% demand increase",
    LOW: "+2% demand increase"
  };

  const today = new Date("2026-07-13");
  
  const parsed = festivals.map(f => {
    let dateObj = null;
    if (f.date && f.date !== "VARIES") {
      const [m, d] = f.date.split("-").map(Number);
      dateObj = new Date(2026, m - 1, d);
    } else {
      if (f.name === "Deepavali") dateObj = new Date(2026, 10, 8);
      else if (f.name === "Ramzan (Eid ul-Fitr)") dateObj = new Date(2027, 2, 20);
      else dateObj = new Date(2026, 8, 1);
    }
    return { ...f, dateObj };
  });

  let upcoming = parsed.filter(f => f.dateObj >= today);
  upcoming.sort((a, b) => a.dateObj - b.dateObj);
  const list = upcoming.slice(0, 4);
  
  container.innerHTML = list.map(f => {
    const displayDate = f.date === "VARIES" ? "Varies" : formatFestivalDate(f.date);
    const demandBadge = f.demand_highlight || defaultHighlights[f.demand] || "+5% demand increase";
    return `
      <div class="bg-white border border-gray-150 rounded-2xl p-4 shadow-sm flex items-center justify-between">
        <div>
          <span class="font-bold text-base text-gray-900 block">${f.name}</span>
          <span class="inline-block mt-2 text-[12px] font-bold text-green-700 bg-green-50 px-2.5 py-0.5 rounded-full">
            ${demandBadge}
          </span>
        </div>
        <div class="text-right">
          <span class="text-[15px] font-extrabold text-gray-400 block uppercase tracking-wider">${displayDate}</span>
        </div>
      </div>
    `;
  }).join('');
}

async function loadStats() {
  try {
    const s = await fetchStats();
    document.getElementById('statCommodities').textContent = s.commodities  || '120+';
    document.getElementById('statMarkets').textContent     = s.markets      || '47';
    document.getElementById('statUpdated').textContent     = s.last_updated || 'Today';
  } catch {}
}

async function loadConfig() {
  try {
    const cfg = await fetchConfig();
    commoditiesData = cfg.commodities || [];
    districtsData = cfg.districts || [];
    populateCommodities();
    populateDistricts();
    if (cfg.festivals) {
      populateFestivals(cfg.festivals);
    }

    const storedCommLabel = sessionStorage.getItem('selected_commodity_label');
    const storedCommValue = sessionStorage.getItem('selected_commodity_value');
    if (storedCommLabel && storedCommValue) {
      document.getElementById('commoditySelectInput').value = storedCommLabel;
      document.getElementById('commodityHiddenVal').value   = storedCommValue;
    }

    const storedDistLabel = sessionStorage.getItem('selected_district_label');
    const storedDistValue = sessionStorage.getItem('selected_district_value');
    if (storedDistLabel && storedDistValue) {
      document.getElementById('districtSelectInput').value = storedDistLabel;
      document.getElementById('districtHiddenVal').value   = storedDistValue;
    }

    const storedRole = sessionStorage.getItem('selected_role');
    if (storedRole) {
      const card = document.querySelector(`.role-card[data-role="${storedRole}"]`);
      if (card) selectRole(card);
    }
  } catch (err) {
    console.error("Config fetch failed:", err);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadConfig().then(() => {
    loadWeather();
  });
  loadStats();
  // Forcing UI to English by default
  applyTranslations('en');
});
