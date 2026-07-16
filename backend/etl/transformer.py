import io
import csv
from datetime import datetime


def build_csv_buffer(records, target_date):                 #Turns raw AGMARKNET records (for one date) into a CSV buffer ready for COPY into the temp table.
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    target_date_str = target_date.strftime("%d/%m/%Y")
    row_count = 0

    for r in records:
        if r.get("Arrival_Date") != target_date_str:
            continue

        try:
            arrival_date = datetime.strptime(
                r.get("Arrival_Date"), "%d/%m/%Y"
            ).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue

        try:
            min_price = float(r.get("Min_Price") or 0)
            max_price = float(r.get("Max_Price") or 0)
            modal_price = float(r.get("Modal_Price") or 0)
        except ValueError:
            continue

        writer.writerow([                           #make a buffer copy to restrict the same data
            r.get("State"),
            r.get("District"),
            r.get("Market"),
            r.get("Commodity"),
            r.get("Variety"),
            min_price,
            max_price,
            modal_price,
            arrival_date,
        ])
        row_count += 1

    buffer.seek(0)
    return buffer, row_count