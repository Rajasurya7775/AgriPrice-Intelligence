from datetime import date, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests


def get_retry_session(
    total_retries=2,  # TEMP: lowered from 5 for faster debugging, restore later
    backoff_factor=2,
    status_forcelist=(429, 500, 502, 503, 504),
):                                
 #Returns a requests.Session() configured with retry + backoff.
    session = requests.Session()

    retry = Retry(
        total=total_retries,
        read=total_retries,
        connect=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


def get_missing_dates(last_db_date):
    today = date.today()

    if last_db_date is None:
        return [today]

    if last_db_date >= today:
        return []

    missing = []
    current = last_db_date + timedelta(days=1)

    while current <= today:
        missing.append(current)
        current += timedelta(days=1)

    return missing

def to_agmarknet_date_str(d):
    return d.strftime("%d/%m/%Y")