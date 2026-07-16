# COPY + INSERT logic 
def load_buffer(db, buffer, row_count):
    if row_count == 0:
        print(" No valid rows to load for this date — skipping DB write.")
        return 0

    cursor = db.cursor()

    try:
        cursor.execute("""
            SELECT setval(
                'commodity_prices_id_seq',
                COALESCE((SELECT MAX(id) FROM commodity_prices), 1)
            )
        """)

        # STEP 1 — COPY into temp table (no constraints, never fails)
        cursor.execute("""
            CREATE TEMP TABLE temp_prices (
                state        VARCHAR(100),
                district     VARCHAR(100),
                market       VARCHAR(150),
                commodity    VARCHAR(150),
                variety      VARCHAR(150),
                min_price    NUMERIC(10,2),
                max_price    NUMERIC(10,2),
                modal_price  NUMERIC(10,2),
                arrival_date DATE
            ) ON COMMIT DROP
        """)

        cursor.copy_expert("""
            COPY temp_prices
            (state, district, market, commodity, variety,
             min_price, max_price, modal_price, arrival_date)
            FROM STDIN WITH CSV
        """, buffer)

        # STEP 2 — Insert from temp to real table, skip duplicates
        cursor.execute("""
            INSERT INTO commodity_prices
                (state, district, market, commodity, variety,
                 min_price, max_price, modal_price, arrival_date)
            SELECT
                state, district, market, commodity, variety,
                min_price, max_price, modal_price, arrival_date
            FROM temp_prices
            ON CONFLICT (market, commodity, variety, arrival_date)
            DO NOTHING
        """)

        inserted = cursor.rowcount
        db.commit()

        print(f"  ✅ {inserted} new rows added (out of {row_count} fetched)")
        return inserted

    except Exception as e:
        db.rollback()
        print("  ❌ Insert failed:", e)
        return 0

    finally:
        cursor.close()