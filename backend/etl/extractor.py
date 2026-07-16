from .utils import get_retry_session, to_agmarknet_date_str
from backend.config import AGMARKNET_API_KEY, AGMARKNET_BASE_URL


PAGE_LIMIT = 6000
REQUEST_TIMEOUT = (30, 60)  # TEMP: lowered read timeout from 300 to 60 for faster debugging, restore later
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_records_for_date(target_date):
    session = get_retry_session()
    date_str = to_agmarknet_date_str(target_date)

    all_records = []
    offset = 0

    while True:
        params = {
            "api-key": AGMARKNET_API_KEY,
            "format": "json",
            "limit": PAGE_LIMIT,
            "offset": offset,
            "filters[state.keyword]": "Tamil Nadu",
            "filters[Arrival_Date]": date_str,
        }

        print(f"  → requesting {date_str} (offset={offset}) ...", flush=True)

        try:
            response = session.get(
                AGMARKNET_BASE_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except Exception as e:
            print(f"❌ API fetch failed for {date_str} (offset={offset}):", e, flush=True)
            break

        data = response.json()
        page_records = data.get("records", [])

        if not page_records:
            break

        all_records.extend(page_records)

        if len(page_records) < PAGE_LIMIT:
            break

        offset += PAGE_LIMIT

    print(f"  {date_str}: {len(all_records)} records fetched", flush=True)
    return all_records