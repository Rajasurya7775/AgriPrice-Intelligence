// ============================================================
//   AgriPrice Intelligence — Tamil Nadu
//   api.js — All API calls in one place
// ============================================================

const API_BASE      = "http://127.0.0.1:5000";
const UNSPLASH_KEY  = "############################"; // ← replace with your key

// #region agent log
function __agentLog(hypothesisId, location, message, data = {}) {
    try {
        fetch('http://127.0.0.1:7349/ingest/38915ad1-dcdd-4ec6-b887-f7e2d6198276', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Debug-Session-Id': 'f45c6e' },
            body: JSON.stringify({
                sessionId: 'f45c6e',
                runId: window.__AGENT_RUN_ID__ || 'pre-fix',
                hypothesisId,
                location,
                message,
                data,
                timestamp: Date.now()
            })
        }).catch(() => {});
    } catch (_) {}
}
// #endregion

// ─────────────────────────────────────────
//  BACKEND API CALLS
// ─────────────────────────────────────────

// Get all 38 TN districts
async function fetchDistricts() {
    const res  = await fetch(`${API_BASE}/districts`);
    const data = await res.json();
    return data.districts || [];
}

// Get commodities for district
async function fetchCommodities(district) {
    // #region agent log
    __agentLog('B', 'frontend/js/api.js:fetchCommodities', 'Requesting commodities', { district });
    // #endregion
    const res = await fetch(`${API_BASE}/commodities?district=${encodeURIComponent(district)}`);
    let data = null;
    try { data = await res.json(); } catch (e) {
        // #region agent log
        __agentLog('B', 'frontend/js/api.js:fetchCommodities', 'Failed to parse JSON', { district, status: res.status, error: String(e) });
        // #endregion
        throw e;
    }
    // #region agent log
    __agentLog('B', 'frontend/js/api.js:fetchCommodities', 'Commodities response', { district, status: res.status, ok: res.ok, keys: data ? Object.keys(data) : null, count: (data?.commodities || []).length });
    // #endregion
    return data.commodities || [];
}

// Get full analysis
async function fetchAnalysis(userType, district, commodity) {
    // #region agent log
    __agentLog('A', 'frontend/js/api.js:fetchAnalysis', 'Requesting analysis', { userType, district, commodity });
    // #endregion
    const res = await fetch(`${API_BASE}/analyse`, {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({
            user_type : userType,
            district  : district,
            commodity : commodity
        })
    });
    return await res.json();
}

// Get today's top movers
async function fetchMovers() {
    const res  = await fetch(`${API_BASE}/movers`);
    const data = await res.json();
    return data.movers || [];
}

// Get seasonal calendar data
async function fetchSeasonal() {
    const res  = await fetch(`${API_BASE}/seasonal`);
    const data = await res.json();
    return data.seasonal || [];
}

// ─────────────────────────────────────────
//  UNSPLASH IMAGE API
// ─────────────────────────────────────────
async function fetchCommodityImage(commodity) {
    try {
        // Clean commodity name for search
        const query = commodity
            .replace(/\(.*?\)/g, "")  // remove brackets
            .trim()
            .split(" ")[0]            // first word only
            .toLowerCase();

        const res  = await fetch(
            `https://api.unsplash.com/search/photos?query=${query}+vegetable+food&per_page=1&orientation=landscape`,
            { headers: { Authorization: `Client-ID ${UNSPLASH_KEY}` } }
        );
        const data = await res.json();

        if (data.results && data.results.length > 0) {
            return data.results[0].urls.regular;
        }
        return null;
    } catch(e) {
        return null;
    }
}
