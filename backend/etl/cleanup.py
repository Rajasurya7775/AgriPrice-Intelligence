# Keeps only the latest 7 DISTINCT arrival_dates in commodity_prices.
# (CURRENT_DATE - INTERVAL '7 days')

def keep_latest_seven_dates(db):
    cursor = db.cursor()

    try:
        cursor.execute("""
            DELETE FROM commodity_prices
            WHERE arrival_date NOT IN (
                SELECT arrival_date
                FROM commodity_prices
                GROUP BY arrival_date
                ORDER BY arrival_date DESC
                LIMIT 7
            )
        """)

        deleted = cursor.rowcount
        db.commit()

        print(f"🗑 Cleanup: {deleted} old rows removed (kept latest 7 distinct dates)")
        return deleted

    except Exception as e:
        db.rollback()
        print("❌ Cleanup failed:", e)
        return 0

    finally:
        cursor.close()