"""
Chay 1 lan duy nhat - backfill BSR + price history tu Keepa
Lay 90 ngay lich su cho target ASINs, insert vao daily_snapshots
"""
import keepa
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from db import supabase

load_dotenv()

# Keepa token: dang ky tai keepa.com, free tier 250 tokens/ngay
KEEPA_KEY   = os.getenv("KEEPA_KEY")
LOOKBACK    = 90  # so ngay muon lay lich su


def keepa_time_to_date(kt):
    """Keepa dung unix minutes ke tu 2011-01-08. Chuyen ve date string."""
    unix_seconds = (kt + 21564000) * 60
    return datetime.fromtimestamp(unix_seconds, tz=timezone.utc).date().isoformat()


def get_target_asins():
    result = supabase.table("asins").select("asin").eq("is_active", True).execute()
    return [row["asin"] for row in result.data]


def run():
    api          = keepa.Keepa(KEEPA_KEY)
    target_asins = get_target_asins()

    print(f"[Keepa] Backfill {len(target_asins)} ASINs, {LOOKBACK} ngay lich su...")

    # Keepa tinh tokens: ~10 tokens/ASIN khi lay history
    # Free tier: 250 tokens/ngay -> query 25 ASINs/ngay
    products = api.query(
        target_asins,
        history=True,
        days=LOOKBACK,
        offers=0,
    )

    rows = []
    for product in products:
        asin = product.get("asin")
        if not asin:
            continue

        # BSR history: array xen ke [keepa_time, bsr, keepa_time, bsr, ...]
        bsr_data   = product.get("data", {}).get("SALES", [])
        price_data = product.get("data", {}).get("NEW", [])  # new condition price

        # Build dict: date -> bsr
        bsr_by_date = {}
        for i in range(0, len(bsr_data) - 1, 2):
            if bsr_data[i] != -1 and bsr_data[i+1] != -1:
                d = keepa_time_to_date(bsr_data[i])
                bsr_by_date[d] = bsr_data[i+1]

        # Build dict: date -> price (Keepa luu gia theo cents)
        price_by_date = {}
        for i in range(0, len(price_data) - 1, 2):
            if price_data[i] != -1 and price_data[i+1] != -1:
                d = keepa_time_to_date(price_data[i])
                price_by_date[d] = round(price_data[i+1] / 100, 2)

        # Merge theo ngay
        all_dates = set(bsr_by_date.keys()) | set(price_by_date.keys())
        for d in all_dates:
            rows.append({
                "asin":          asin,
                "snapshot_date": d,
                "bsr":           bsr_by_date.get(d),
                "price":         price_by_date.get(d),
                "in_stock":      True,  # Keepa khong co stock info chi tiet
            })

        print(f"  {asin}: {len(all_dates)} ngay lich su")

    # Insert theo batch 500 rows
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        supabase.table("daily_snapshots").upsert(
            batch,
            on_conflict="asin,snapshot_date"
        ).execute()
        print(f"[Keepa] Inserted batch {i//batch_size + 1}: {len(batch)} rows")

    print(f"[Keepa] Xong. Tong {len(rows)} rows historical data")


if __name__ == "__main__":
    run()
