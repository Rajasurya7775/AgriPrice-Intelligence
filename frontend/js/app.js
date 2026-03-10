// ============================================================
//   AgriPrice Intelligence — Tamil Nadu
//   app.js — Main application logic
// ============================================================

let selectedUserType = "producer";

// ─────────────────────────────────────────
//  INIT — runs when page loads
// ─────────────────────────────────────────
window.onload = async () => {
    // #region agent log
    window.__AGENT_RUN_ID__ = window.__AGENT_RUN_ID__ || ('run_' + Date.now());
    try { __agentLog('E', 'frontend/js/app.js:window.onload', 'App init', { apiBase: (typeof API_BASE !== 'undefined') ? API_BASE : null }); } catch (_) {}
    // #endregion

    // Load districts
    try {
        const districts = await fetchDistricts();
        const select    = document.getElementById("districtSelect");
        select.innerHTML = '<option value="">Select district...</option>';
        districts.forEach(d => {
            select.innerHTML += `<option value="${d}">${d}</option>`;
        });
    } catch(e) {
        console.error("Districts load failed:", e);
    }

    // Load market movers
    try {
        const movers = await fetchMovers();
        renderMovers(movers);
    } catch(e) {
        document.getElementById("moversTicker").innerHTML =
            "<span class='ticker-item'>Market data loading...</span>";
    }

    // Show page 1
    showPage("page1");
};

// ─────────────────────────────────────────
//  USER TYPE SELECTION
// ─────────────────────────────────────────
function selectUser(btn) {
    document.querySelectorAll(".user-btn").forEach(b =>
        b.classList.remove("selected"));
    btn.classList.add("selected");
    selectedUserType = btn.dataset.type;
}

// ─────────────────────────────────────────
//  LOAD COMMODITIES
// ─────────────────────────────────────────
async function loadCommodities() {
    const district = document.getElementById("districtSelect").value;
    const select   = document.getElementById("commoditySelect");

    if (!district) {
        select.innerHTML = '<option value="">Select district first</option>';
        select.disabled  = true;
        return;
    }

    select.innerHTML = '<option value="">Loading...</option>';
    select.disabled  = true;

    try {
        // #region agent log
        try { __agentLog('B', 'frontend/js/app.js:loadCommodities', 'Loading commodities', { district }); } catch (_) {}
        // #endregion
        const commodities = await fetchCommodities(district);
        select.innerHTML  = '<option value="">Select commodity...</option>';
        commodities.forEach(c => {
            select.innerHTML += `<option value="${c}">${c}</option>`;
        });
        select.disabled = false;
    } catch(e) {
        // #region agent log
        try { __agentLog('B', 'frontend/js/app.js:loadCommodities', 'Load commodities failed', { district, error: String(e?.message || e) }); } catch (_) {}
        // #endregion
        select.innerHTML = '<option value="">Could not load</option>';
    }
}

// ─────────────────────────────────────────
//  RUN ANALYSIS
// ─────────────────────────────────────────
async function runAnalysis() {
    const district  = document.getElementById("districtSelect").value;
    const commodity = document.getElementById("commoditySelect").value;

    if (!district || !commodity) {
        alert("Please select both district and commodity");
        return;
    }

    showLoading("Analysing market data...");

    try {
        const data = await fetchAnalysis(selectedUserType, district, commodity);

        if (data.status !== "success") {
            throw new Error(data.message);
        }

        hideLoading();
        // #region agent log
        try { __agentLog('C', 'frontend/js/app.js:runAnalysis', 'Rendering results', { data_source: data?.data_source, hasAdvisory: Boolean(data?.advisory), advisoryLen: (data?.advisory || '').length }); } catch (_) {}
        // #endregion
        await renderResults(data);
        // #region agent log
        try { __agentLog('E', 'frontend/js/app.js:runAnalysis', 'Navigating to page2', { ok: true }); } catch (_) {}
        // #endregion
        showPage("page2");

    } catch(e) {
        hideLoading();
        // #region agent log
        try { __agentLog('E', 'frontend/js/app.js:runAnalysis', 'Run analysis failed', { district, commodity, userType: selectedUserType, error: String(e?.message || e) }); } catch (_) {}
        // #endregion
        alert("Error: " + e.message);
    }
}

// ─────────────────────────────────────────
//  LOAD SEASONAL PAGE
// ─────────────────────────────────────────
async function loadSeasonal() {
    showPage("page3");

    try {
        const seasonal = await fetchSeasonal();
        renderSeasonal(seasonal);
    } catch(e) {
        document.getElementById("seasonalGrid").innerHTML =
            "<p>Could not load seasonal data</p>";
    }
}
