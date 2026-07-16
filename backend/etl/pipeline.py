from .extractor import fetch_records_for_date
from .transformer import build_csv_buffer
from .loader import load_buffer
from .cleanup import keep_latest_seven_dates
from backend.config import get_db



def get_last_arrival_date(db):           # Fetches the latest arrival_date in commodity_prices, or None if empty.
    cursor = db.cursor()
    try:
        cursor.execute("SELECT MAX(arrival_date) FROM commodity_prices")
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()


# Calculate missing dates (last_date+1 ... today)
# For each missing date: fetch (extractor) -> transform (transformer) -> load (loader)
# After all dates processed: cleanup (keep latest 7 distinct dates)

def run_pipeline():                             
    print("=" * 50)
    print("Starting AgriPrice ETL run")
    print("=" * 50)

    db = get_db()

    try:
        last_date = get_last_arrival_date(db)
        print(f"Latest date currently in DB: {last_date}")

        missing_dates = get_missing_dates(last_date)

        if not missing_dates:
            print("No missing dates — database already up to date.")
        else:
            print(f"Dates to process: {[d.isoformat() for d in missing_dates]}")

        total_inserted = 0

        for target_date in missing_dates:
            print(f"\nProcessing {target_date.isoformat()} ...")

            records = fetch_records_for_date(target_date)

            if not records:
                print(f"  No data published yet for {target_date.isoformat()} — skipping.")
                continue

            buffer, row_count = build_csv_buffer(records, target_date)
            inserted = load_buffer(db, buffer, row_count)
            total_inserted += inserted

        print(f"\nTotal new rows inserted this run: {total_inserted}")

        print("\nRunning cleanup (keep latest 7 distinct dates)...")
        keep_latest_seven_dates(db)

    finally:
        db.close()

    print("\nETL run complete.")


if __name__ == "__main__":
    run_pipeline()