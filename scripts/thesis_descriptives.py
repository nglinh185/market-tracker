"""
Pull descriptive statistics for the thesis Results chapter.

Reads the most recent snapshot from Supabase and produces a single JSON file
under ``data/eval/descriptives.json`` that the LaTeX chapters can quote
verbatim. Read-only; safe to re-run.

Usage:
    python scripts/thesis_descriptives.py
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

from lib.db import supabase


CATEGORIES = ["gaming_keyboard", "true_wireless_earbuds", "portable_charger"]
PRETTY_CATEGORY = {
    "gaming_keyboard": "Gaming Keyboards",
    "true_wireless_earbuds": "True Wireless Earbuds",
    "portable_charger": "Portable Chargers",
}


def _safe(value, default=None):
    return default if value is None else value


def _round(value, n=2):
    if value is None:
        return None
    return round(float(value), n)


def _latest_snapshot_date(table: str, date_col: str = "snapshot_date") -> str | None:
    res = (
        supabase.table(table)
        .select(date_col)
        .order(date_col, desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    return res.data[0][date_col]


def _fetch_all(table: str, columns: str, **eq_filters) -> list[dict]:
    """Paginate over a Supabase table to bypass the 1000-row default cap."""
    rows: list[dict] = []
    page_size = 1000
    start = 0
    while True:
        q = supabase.table(table).select(columns)
        for k, v in eq_filters.items():
            q = q.eq(k, v)
        res = q.range(start, start + page_size - 1).execute()
        chunk = res.data or []
        rows.extend(chunk)
        if len(chunk) < page_size:
            break
        start += page_size
    return rows


def collection_summary() -> dict:
    rankings = _fetch_all("category_rankings", "snapshot_date")
    snapshots = _fetch_all("daily_snapshots", "snapshot_date")
    asin_reviews = _fetch_all("reviews_raw", "asin")
    image_events = _fetch_all("image_change_events", "id,change_flag")

    rank_set = sorted({r["snapshot_date"] for r in rankings})
    snap_set = sorted({r["snapshot_date"] for r in snapshots})
    unique_review_asins = len({r["asin"] for r in asin_reviews})
    image_change_actual = sum(1 for r in image_events if r.get("change_flag"))

    total_reviews = (
        supabase.table("reviews_raw")
        .select("review_id", count="exact")
        .limit(1)
        .execute()
    )
    alert_count = (
        supabase.table("alerts")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )
    entrant_exit_count = (
        supabase.table("entrant_exit_events")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )

    return {
        "rankings_days": len(rank_set),
        "rankings_date_range": [rank_set[0], rank_set[-1]] if rank_set else None,
        "snapshots_days": len(snap_set),
        "snapshots_date_range": [snap_set[0], snap_set[-1]] if snap_set else None,
        "total_category_ranking_rows": len(rankings),
        "total_daily_snapshot_rows": len(snapshots),
        "total_reviews": total_reviews.count or 0,
        "asins_with_reviews": unique_review_asins,
        "total_image_change_rows": len(image_events),
        "total_image_change_actual": image_change_actual,
        "total_alerts": alert_count.count or 0,
        "total_entrant_exit_events": entrant_exit_count.count or 0,
    }


def per_category_descriptives(rank_date: str, snap_date: str | None) -> list[dict]:
    """Summarise each category from the latest ranking snapshot.

    BSR comes from ``daily_snapshots`` (watchlist only) since
    ``category_rankings`` does not store BSR per row.
    """
    rankings = (
        supabase.table("category_rankings")
        .select("asin,browse_node,rank,price,is_sponsored,stars,reviews_count")
        .eq("snapshot_date", rank_date)
        .execute()
    ).data

    asin_to_cat = {
        r["asin"]: r.get("category")
        for r in (
            supabase.table("asins")
            .select("asin,category")
            .execute()
        ).data
    }

    snap_rows = []
    if snap_date:
        snap_rows = (
            supabase.table("daily_snapshots")
            .select("asin,bsr")
            .eq("snapshot_date", snap_date)
            .execute()
        ).data

    bsr_by_cat = defaultdict(list)
    for r in snap_rows:
        cat = asin_to_cat.get(r["asin"])
        if cat and r.get("bsr") is not None:
            bsr_by_cat[cat].append(int(r["bsr"]))

    by_cat = defaultdict(list)
    for r in rankings:
        by_cat[r["browse_node"]].append(r)

    out = []
    for cat in CATEGORIES:
        items = by_cat.get(cat, [])
        if not items:
            continue
        prices = [float(r["price"]) for r in items if r.get("price") is not None]
        reviews = [int(r["reviews_count"]) for r in items if r.get("reviews_count") is not None]
        stars = [float(r["stars"]) for r in items if r.get("stars") is not None]
        sponsored = sum(1 for r in items if r.get("is_sponsored"))
        bsrs = bsr_by_cat.get(cat, [])

        out.append({
            "category": cat,
            "category_label": PRETTY_CATEGORY[cat],
            "asins_ranked": len(items),
            "price_min": _round(min(prices), 2) if prices else None,
            "price_max": _round(max(prices), 2) if prices else None,
            "price_mean": _round(mean(prices), 2) if prices else None,
            "price_median": _round(median(prices), 2) if prices else None,
            "stars_mean": _round(mean(stars), 2) if stars else None,
            "reviews_mean": _round(mean(reviews), 0) if reviews else None,
            "reviews_median": _round(median(reviews), 0) if reviews else None,
            "sponsored_share_pct": _round(100 * sponsored / len(items), 1),
            "watchlist_bsr_mean": _round(mean(bsrs), 0) if bsrs else None,
            "watchlist_bsr_median": _round(median(bsrs), 0) if bsrs else None,
            "watchlist_bsr_n": len(bsrs),
        })
    return out


def watchlist_count() -> dict:
    """Count active watchlist ASINs (`asins.is_active = true`)."""
    rows = (
        supabase.table("asins")
        .select("asin,category")
        .eq("is_active", True)
        .execute()
    ).data
    by_cat = Counter(r["category"] for r in rows)
    return {
        "total_watchlist": len(rows),
        "by_category": {k: by_cat.get(k, 0) for k in CATEGORIES},
    }


def price_tier_summary(latest_date: str) -> list[dict]:
    rows = (
        supabase.table("price_tier_daily")
        .select("browse_node,asin,price,cluster_name")
        .eq("snapshot_date", latest_date)
        .execute()
    ).data

    out = []
    for cat in CATEGORIES:
        items = [r for r in rows if r["browse_node"] == cat]
        if not items:
            continue
        by_tier = defaultdict(list)
        for r in items:
            by_tier[r["cluster_name"]].append(float(r["price"]))
        for tier in ["entry", "mid", "premium"]:
            prices = by_tier.get(tier, [])
            if not prices:
                continue
            out.append({
                "category": cat,
                "category_label": PRETTY_CATEGORY[cat],
                "tier": tier,
                "n_asins": len(prices),
                "price_min": _round(min(prices), 2),
                "price_max": _round(max(prices), 2),
                "price_mean": _round(mean(prices), 2),
            })
    return out


def bms_top(latest_date: str, n: int = 10) -> list[dict]:
    rows = (
        supabase.table("brand_momentum_daily")
        .select("asin,bms_score,bsr_velocity,review_velocity,sentiment_score")
        .eq("snapshot_date", latest_date)
        .order("bms_score", desc=True)
        .limit(n)
        .execute()
    ).data
    asin_to_cat = {
        r["asin"]: r.get("category")
        for r in (
            supabase.table("asins")
            .select("asin,category")
            .execute()
        ).data
    }
    return [
        {
            "asin": r["asin"],
            "category": asin_to_cat.get(r["asin"]),
            "bms_score": _round(r.get("bms_score"), 3),
            "bsr_velocity": _round(r.get("bsr_velocity"), 3),
            "review_velocity": _round(r.get("review_velocity"), 3),
            "sentiment_score": _round(r.get("sentiment_score"), 3),
        }
        for r in rows
    ]


def lqs_summary(latest_date: str) -> dict:
    rows = (
        supabase.table("listing_quality_score_daily")
        .select("asin,lqs_total")
        .eq("snapshot_date", latest_date)
        .execute()
    ).data

    if not rows:
        return {"as_of": latest_date, "total": 0}

    asin_to_cat = {
        r["asin"]: r.get("category")
        for r in (
            supabase.table("asins")
            .select("asin,category")
            .execute()
        ).data
    }
    for r in rows:
        r["category"] = asin_to_cat.get(r["asin"])

    scores = [r["lqs_total"] for r in rows if r.get("lqs_total") is not None]
    by_cat = defaultdict(list)
    for r in rows:
        if r.get("lqs_total") is not None and r.get("category"):
            by_cat[r["category"]].append(r["lqs_total"])

    sorted_rows = sorted(
        [r for r in rows if r.get("lqs_total") is not None],
        key=lambda x: x["lqs_total"],
        reverse=True,
    )

    return {
        "as_of": latest_date,
        "n_asins": len(scores),
        "overall_mean": _round(mean(scores), 1) if scores else None,
        "overall_median": _round(median(scores), 1) if scores else None,
        "overall_min": _round(min(scores), 1) if scores else None,
        "overall_max": _round(max(scores), 1) if scores else None,
        "by_category": {
            cat: {
                "n": len(by_cat.get(cat, [])),
                "mean": _round(mean(by_cat[cat]), 1) if by_cat.get(cat) else None,
            }
            for cat in CATEGORIES
        },
        "top5": [
            {"asin": r["asin"], "category": r.get("category"), "lqs": _round(r["lqs_total"], 1)}
            for r in sorted_rows[:5]
        ],
        "bottom5": [
            {"asin": r["asin"], "category": r.get("category"), "lqs": _round(r["lqs_total"], 1)}
            for r in sorted_rows[-5:]
        ],
    }


def sentiment_per_category(latest_date: str) -> list[dict]:
    """Aggregate avg sentiment per category from review_sentiment_daily ∩ asins."""
    sentiments = (
        supabase.table("review_sentiment_daily")
        .select("asin,avg_sentiment_score,positive_ratio,negative_ratio,review_count_new")
        .eq("snapshot_date", latest_date)
        .execute()
    ).data

    if not sentiments:
        return []

    asin_to_cat = {
        r["asin"]: r["category"]
        for r in (
            supabase.table("asins")
            .select("asin,category")
            .execute()
        ).data
    }

    by_cat = defaultdict(list)
    for s in sentiments:
        cat = asin_to_cat.get(s["asin"])
        if cat:
            by_cat[cat].append(s)

    out = []
    for cat in CATEGORIES:
        items = by_cat.get(cat, [])
        if not items:
            continue
        avg = [i["avg_sentiment_score"] for i in items if i.get("avg_sentiment_score") is not None]
        pos = [i["positive_ratio"] for i in items if i.get("positive_ratio") is not None]
        neg = [i["negative_ratio"] for i in items if i.get("negative_ratio") is not None]
        out.append({
            "category": cat,
            "category_label": PRETTY_CATEGORY[cat],
            "n_asins": len(items),
            "avg_sentiment_score": _round(mean(avg), 3) if avg else None,
            "avg_positive_ratio": _round(mean(pos), 3) if pos else None,
            "avg_negative_ratio": _round(mean(neg), 3) if neg else None,
        })
    return out


def alerts_breakdown() -> dict:
    rows = _fetch_all("alerts", "alert_type,severity")

    by_type = Counter(r["alert_type"] for r in rows if r.get("alert_type"))
    by_severity = Counter(r["severity"] for r in rows if r.get("severity"))
    by_type_severity = defaultdict(Counter)
    for r in rows:
        if r.get("alert_type") and r.get("severity"):
            by_type_severity[r["alert_type"]][r["severity"]] += 1

    return {
        "total": len(rows),
        "by_type": dict(by_type),
        "by_severity": dict(by_severity),
        "by_type_severity": {k: dict(v) for k, v in by_type_severity.items()},
    }


def entrant_exit_summary() -> dict:
    rows = _fetch_all("entrant_exit_events", "event_type,is_top10,browse_node")

    total = len(rows)
    by_type = Counter(r["event_type"] for r in rows)
    top10 = sum(1 for r in rows if r.get("is_top10"))
    by_cat_type = defaultdict(Counter)
    for r in rows:
        if r.get("browse_node") and r.get("event_type"):
            by_cat_type[r["browse_node"]][r["event_type"]] += 1

    return {
        "total_events": total,
        "by_type": dict(by_type),
        "top10_events": top10,
        "by_category": {k: dict(v) for k, v in by_cat_type.items()},
    }


def main() -> None:
    print("[Descriptives] Pulling Supabase data...")

    latest_rank_date = _latest_snapshot_date("category_rankings")
    latest_snap_date = _latest_snapshot_date("daily_snapshots")
    latest_lqs_date = _latest_snapshot_date("listing_quality_score_daily")
    latest_bms_date = _latest_snapshot_date("brand_momentum_daily")
    latest_tier_date = _latest_snapshot_date("price_tier_daily")
    latest_sent_date = _latest_snapshot_date("review_sentiment_daily")

    print(f"  latest_rank_date  = {latest_rank_date}")
    print(f"  latest_snap_date  = {latest_snap_date}")
    print(f"  latest_lqs_date   = {latest_lqs_date}")
    print(f"  latest_bms_date   = {latest_bms_date}")
    print(f"  latest_tier_date  = {latest_tier_date}")
    print(f"  latest_sent_date  = {latest_sent_date}")

    out = {
        "as_of": date.today().isoformat(),
        "snapshot_dates": {
            "rankings": latest_rank_date,
            "snapshots": latest_snap_date,
            "lqs": latest_lqs_date,
            "bms": latest_bms_date,
            "price_tier": latest_tier_date,
            "sentiment": latest_sent_date,
        },
        "collection": collection_summary(),
        "watchlist": watchlist_count(),
        "per_category": per_category_descriptives(latest_rank_date, latest_snap_date) if latest_rank_date else [],
        "price_tiers": price_tier_summary(latest_tier_date) if latest_tier_date else [],
        "bms_top10": bms_top(latest_bms_date, n=10) if latest_bms_date else [],
        "lqs": lqs_summary(latest_lqs_date) if latest_lqs_date else {},
        "sentiment_per_category": sentiment_per_category(latest_sent_date) if latest_sent_date else [],
        "alerts": alerts_breakdown(),
        "entrant_exit": entrant_exit_summary(),
    }

    out_path = Path("data/eval/descriptives.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"[Descriptives] Wrote {out_path}")
    print(f"  collection.snapshots_days        = {out['collection']['snapshots_days']}")
    print(f"  collection.total_reviews         = {out['collection']['total_reviews']}")
    print(f"  collection.total_alerts          = {out['collection']['total_alerts']}")
    print(f"  collection.total_entrant_exit    = {out['collection']['total_entrant_exit_events']}")


if __name__ == "__main__":
    main()
