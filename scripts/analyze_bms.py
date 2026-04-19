"""
Brand Momentum Score (BMS) — composite velocity metric.
bms = 0.5 * bsr_velocity + 0.3 * review_velocity_norm + 0.2 * sentiment_score_norm
Populate: brand_momentum_daily
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase, upsert


def main() -> None:
    today     = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()

    today_snaps = {
        r["asin"]: r for r in (
            supabase.table("daily_snapshots")
            .select("asin,bsr,reviews_count")
            .eq("snapshot_date", today)
            .execute()
        ).data
    }
    yesterday_snaps = {
        r["asin"]: r for r in (
            supabase.table("daily_snapshots")
            .select("asin,bsr,reviews_count")
            .eq("snapshot_date", yesterday)
            .execute()
        ).data
    }
    sentiments = {
        r["asin"]: r["avg_sentiment_score"] for r in (
            supabase.table("review_sentiment_daily")
            .select("asin,avg_sentiment_score")
            .eq("snapshot_date", today)
            .execute()
        ).data
    }

    rows = []
    for asin, t in today_snaps.items():
        y = yesterday_snaps.get(asin, {})

        bsr_t = t.get("bsr")
        bsr_y = y.get("bsr")
        bsr_velocity = None
        if bsr_t and bsr_y and bsr_y > 0:
            bsr_velocity = round((bsr_y - bsr_t) / bsr_y, 4)

        rev_t = t.get("reviews_count") or 0
        rev_y = y.get("reviews_count") or 0
        review_velocity = round(float(rev_t - rev_y), 4)

        sentiment = sentiments.get(asin)

        # Normalize to 0-1 then compute BMS
        bsr_norm  = max(0, min(1, (bsr_velocity + 1) / 2)) if bsr_velocity is not None else 0.5
        rev_norm  = min(1, max(0, review_velocity / 50))
        sent_norm = (sentiment + 1) / 2 if sentiment is not None else 0.5

        bms = round(0.5 * bsr_norm + 0.3 * rev_norm + 0.2 * sent_norm, 4)

        rows.append({
            "snapshot_date":   today,
            "asin":            asin,
            "bsr_velocity":    bsr_velocity,
            "review_velocity": review_velocity,
            "sentiment_score": sentiment,
            "bms_score":       bms,
        })

    n = upsert("brand_momentum_daily", rows, "snapshot_date,asin")
    print(f"[BMS] {n} ASINs. Top mover: "
          f"{max(rows, key=lambda r: r['bms_score'])['asin'] if rows else 'N/A'}")


if __name__ == "__main__":
    main()
