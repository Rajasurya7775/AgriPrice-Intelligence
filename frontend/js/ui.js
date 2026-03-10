// ============================================================
//   AgriPrice Intelligence — Tamil Nadu
//   ui.js — UI helpers, animations, rendering
// ============================================================

// ─────────────────────────────────────────
//  PAGE NAVIGATION
// ─────────────────────────────────────────
function showPage(pageId) {
    document.querySelectorAll(".page").forEach(p => {
        p.classList.remove("active");
        p.style.opacity = "0";
    });

    const page = document.getElementById(pageId);
    page.classList.add("active");

    // Fade in
    setTimeout(() => { page.style.opacity = "1"; }, 10);

    // Update active nav link
    document.querySelectorAll(".nav-link").forEach(l => {
        l.classList.remove("nav-active");
        if (l.dataset.page === pageId) l.classList.add("nav-active");
    });

    // Scroll to top
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// ─────────────────────────────────────────
//  LOADING
// ─────────────────────────────────────────
function showLoading(msg = "Analysing market data...") {
    document.getElementById("loadingText").textContent = msg;
    document.getElementById("loadingOverlay").classList.add("active");
}

function hideLoading() {
    document.getElementById("loadingOverlay").classList.remove("active");
}

// ─────────────────────────────────────────
//  RENDER MARKET MOVERS TICKER
// ─────────────────────────────────────────
function renderMovers(movers) {
    const container = document.getElementById("moversTicker");
    if (!movers || movers.length === 0) {
        container.innerHTML = "<span class='ticker-item'>No movers data today</span>";
        return;
    }

    const items = movers.map(m => {
        const isUp    = m.change_pct > 0;
        const arrow   = isUp ? "↑" : "↓";
        const cls     = isUp ? "ticker-up" : "ticker-down";
        const sign    = isUp ? "+" : "";
        return `<span class="ticker-item ${cls}">
            ${m.commodity} (${m.district}) 
            ${arrow} ${sign}${m.change_pct}%
        </span>`;
    }).join('<span class="ticker-sep">•</span>');

    // Duplicate for infinite scroll effect
    container.innerHTML = items + items;
}

// ─────────────────────────────────────────
//  RENDER SEASONAL CALENDAR
// ─────────────────────────────────────────
function renderSeasonal(seasonal) {
    const container = document.getElementById("seasonalGrid");
    const months    = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"];

    if (!seasonal || seasonal.length === 0) {
        container.innerHTML = "<p>No seasonal data available</p>";
        return;
    }

    let html = `
        <div class="seasonal-header">
            <div class="seasonal-crop-col">Crop</div>
            ${months.map(m => `<div class="seasonal-month">${m}</div>`).join("")}
        </div>
    `;

    seasonal.forEach(item => {
        html += `<div class="seasonal-row">
            <div class="seasonal-crop-name">${item.commodity}</div>
            ${months.map((_, i) => {
                const month = i + 1;
                let cls = "season-normal";
                let tip = "Normal Season";
                if (item.peak.includes(month)) {
                    cls = "season-peak";
                    tip = "Peak Season 🌾";
                } else if (item.lean.includes(month)) {
                    cls = "season-lean";
                    tip = "Lean Season 🏜️";
                }
                return `<div class="seasonal-cell ${cls}" title="${tip}"></div>`;
            }).join("")}
        </div>`;
    });

    // Legend
    html += `
        <div class="seasonal-legend">
            <span class="legend-item">
                <span class="legend-dot season-peak"></span> Peak Season (High Supply)
            </span>
            <span class="legend-item">
                <span class="legend-dot season-lean"></span> Lean Season (Low Supply)
            </span>
            <span class="legend-item">
                <span class="legend-dot season-normal"></span> Normal Season
            </span>
        </div>
    `;

    container.innerHTML = html;
}

// ─────────────────────────────────────────
//  RENDER RESULTS PAGE
// ─────────────────────────────────────────
async function renderResults(data) {

    // Set commodity image
    const imgUrl = await fetchCommodityImage(data.commodity);
    const hero   = document.getElementById("resultHero");
    if (imgUrl) {
        hero.style.backgroundImage = `linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.7)), url(${imgUrl})`;
    } else {
        hero.style.background = "linear-gradient(135deg, #1a3a2a, #2d6a4f)";
    }

    // Title
    document.getElementById("resultTitle").textContent =
        `${data.commodity} — ${data.district}`;
    document.getElementById("resultSubtitle").textContent =
        `${data.user_type?.charAt(0).toUpperCase() + data.user_type?.slice(1)} Advisory`;

    // Data source badge
    const sourceBadge = document.getElementById("sourceBadge");
    if (data.data_source === "gemini_search") {
        sourceBadge.textContent  = "🔍 Live Web Search";
        sourceBadge.className    = "source-badge source-gemini";
    } else {
        sourceBadge.textContent  = "🗄️ Database";
        sourceBadge.className    = "source-badge source-mysql";
    }

    // Advisory
    document.getElementById("advisoryText").textContent = data.advisory;

    // Signal
    const badge = document.getElementById("signalBadge");
    badge.textContent = data.signal;
    badge.className   = "signal-badge ";
    if (data.signal?.includes("SELL"))  badge.className += "signal-sell";
    else if (data.signal?.includes("BUY")) badge.className += "signal-buy";
    else badge.className += "signal-hold";

    // Stats — handle null for Gemini fallback
    document.getElementById("latestPrice").textContent =
        data.latest_price ? `₹${data.latest_price}` : "—";
    document.getElementById("weeklyAvg").textContent =
        data.weekly_avg ? `₹${data.weekly_avg}` : "—";
    document.getElementById("trendText").textContent =
        data.trend || "—";
    document.getElementById("tomorrowPrice").textContent =
        data.tomorrow ? `₹${data.tomorrow}` : "—";
    document.getElementById("dayAfterPrice").textContent =
        data.day_after ? `₹${data.day_after}` : "—";
    document.getElementById("confidence").textContent =
        data.confidence?.split(" ")[0] || "—";
    document.getElementById("harvestStatus").textContent =
        data.harvest_status || "—";
    document.getElementById("lastDate").textContent =
        data.last_date ? `as of ${data.last_date}` : "Live search";

    // Trend color
    const trendEl = document.getElementById("trendText");
    if (data.trend?.includes("↑")) trendEl.style.color = "#e63946";
    else if (data.trend?.includes("↓")) trendEl.style.color = "#2d6a4f";
    else trendEl.style.color = "#f4a261";

    // Price chart
    if (data.price_history && data.price_history.length > 0) {
        buildPriceChart(data.price_history);
        document.getElementById("chartSection").style.display = "block";
    } else {
        document.getElementById("chartSection").style.display = "none";
    }

    // Markets
    const marketsList = document.getElementById("marketsList");
    if (data.markets && data.markets.length > 0) {
        marketsList.innerHTML = data.markets.slice(0, 6).map(m => `
            <div class="market-row">
                <span class="market-name">${m.market}</span>
                <span class="market-price">₹${m.price}</span>
            </div>
        `).join("");
    } else {
        marketsList.innerHTML = `<p class="no-data">No market breakdown available</p>`;
    }

    // Weather
    const weatherIcons = {
        "Clear":"☀️","Clouds":"⛅","Rain":"🌧️",
        "Drizzle":"🌦️","Thunderstorm":"⛈️","Mist":"🌫️"
    };
    const weatherRow = document.getElementById("weatherRow");
    const labels     = ["Today","Tomorrow","Day After"];

    if (data.weather_3day && data.weather_3day.length > 0) {
        weatherRow.innerHTML = data.weather_3day.slice(0, 3).map((w, i) => `
            <div class="weather-day">
                <div class="w-label">${labels[i]}</div>
                <div class="w-date">${w.date}</div>
                <div class="w-icon">${weatherIcons[w.condition] || "🌤️"}</div>
                <div class="w-temp">${w.avg_temp}°C</div>
                <div class="w-cond">${w.condition}</div>
                ${w.rainfall_mm > 0
                    ? `<div class="w-rain">🌧️ ${w.rainfall_mm}mm</div>`
                    : ""}
                ${w.alerts?.length > 0
                    ? `<div class="w-alert">⚠️ ${w.alerts[0]}</div>`
                    : ""}
            </div>
        `).join("");
    } else {
        weatherRow.innerHTML = `<p class="no-data">Weather unavailable</p>`;
    }

    // Festivals
    const festSection = document.getElementById("festSection");
    if (data.upcoming_festivals && data.upcoming_festivals.length > 0) {
        festSection.style.display = "block";
        document.getElementById("festList").innerHTML =
            data.upcoming_festivals.map(f => `
                <div class="fest-item">
                    🎉 <strong>${f.name}</strong>
                    in ${f.days_until} day(s) —
                    Demand: <span class="demand-${f.demand.toLowerCase()}">${f.demand}</span>
                </div>
            `).join("");
    } else {
        festSection.style.display = "none";
    }
}

// ─────────────────────────────────────────
//  PRICE CHART
// ─────────────────────────────────────────
let priceChart = null;

function buildPriceChart(history) {
    const labels = history.map(h => h.date);
    const prices = history.map(h => h.price);

    if (priceChart) priceChart.destroy();

    const ctx = document.getElementById("priceChart").getContext("2d");
    priceChart = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label          : "Modal Price (₹/quintal)",
                data           : prices,
                borderColor    : "#52b788",
                backgroundColor: "rgba(82,183,136,0.15)",
                borderWidth    : 2.5,
                pointBackgroundColor: "#52b788",
                pointRadius    : 5,
                tension        : 0.4,
                fill           : true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    ticks: {
                        callback: v => "₹" + v,
                        font    : { family: "DM Sans" }
                    },
                    grid: { color: "rgba(255,255,255,0.05)" }
                },
                x: {
                    ticks: { font: { family: "DM Sans", size: 11 } },
                    grid : { display: false }
                }
            }
        }
    });
}
