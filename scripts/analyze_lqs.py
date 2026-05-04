"""
Listing Quality Score (LQS) — 0-100 composite score.
Populate: listing_quality_score_daily
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import date
from dotenv import load_dotenv
load_dotenv()

from lib.db import supabase, upsert


def _score_title(title: str | None) -> float:
    if not title:
        return 0
    words = len(title.split())
    if words >= 10:
        return 10
    return round(words / 10 * 10, 1)


def _score_bullets(count: int | None) -> float:
    if not count:
        return 0
    return min(count / 5 * 15, 15)


def _score_image(image_url: str | None) -> float:
    return 15 if image_url else 0


def _score_aplus(ebc_hash: str | None) -> float:
    return 15 if ebc_hash else 0


def _score_rating(stars: float | None) -> float:
    if not stars:
        return 0
    return round((stars / 5) * 20, 1)


def _score_reviews(count: int | None) -> float:
    if not count:
        return 0
    if count >= 1000:
        return 15
    return round(count / 1000 * 15, 1)


def _score_sentiment(sentiment: float | None) -> float:
    if sentiment is None:
        return 0
    return round((sentiment + 1) / 2 * 10, 1)


def main() -> None:
    today = date.today().isoformat()

    snapshots = (
        supabase.table("daily_snapshots")
        .select("asin,snapshot_date,bullet_count,image_url,ebc_html_hash,stars,reviews_count,description")
        .eq("snapshot_date", today)
        .execute()
    ).data

    sentiments = {
        r["asin"]: r["avg_sentiment_score"]
        for r in (
            supabase.table("review_sentiment_daily")
            .select("asin,avg_sentiment_score")
            .eq("snapshot_date", today)
            .execute()
        ).data
    }

    asins_snap = (
        supabase.table("asins")
        .select("asin,product_name")
        .execute()
    ).data
    title_map = {r["asin"]: r["product_name"] for r in asins_snap}

    rows = []
    for s in snapshots:
        asin = s["asin"]
        t  = _score_title(title_map.get(asin))
        b  = _score_bullets(s.get("bullet_count"))
        im = _score_image(s.get("image_url"))
        ap = _score_aplus(s.get("ebc_html_hash"))
        ra = _score_rating(s.get("stars"))
        re = _score_reviews(s.get("reviews_count"))
        se = _score_sentiment(sentiments.get(asin))
        total = round(t + b + im + ap + ra + re + se, 1)

        rows.append({
            "snapshot_date":  today,
            "asin":           asin,
            "title_score":    t,
            "bullet_score":   b,
            "image_score":    im,
            "video_score":    0,
            "aplus_score":    ap,
            "rating_score":   ra,
            "review_score":   re,
            "sentiment_score": se,
            "freshness_score": 0,
            "lqs_total":      total,
        })

    n = upsert("listing_quality_score_daily", rows, "snapshot_date,asin")
    print(f"[LQS] {n} ASINs scored. Avg LQS = "
          f"{round(sum(r['lqs_total'] for r in rows)/len(rows), 1) if rows else 0}")


if __name__ == "__main__":
    main()
