"""
Skill: query_lqs
Listing Quality Score (0-100) per ASIN in a category.
"""
from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase


SKILL = {
    "name": "query_lqs",
    "group": "listing",
    "description": (
        "Return Listing Quality Score (0-100) for ASINs. "
        "Two modes: (1) pass 'category' to get all ASINs in that category; "
        "(2) pass 'asin_list' to look up specific ASINs regardless of category — "
        "use this to look up LQS for BMS candidates that span multiple categories. "
        "Fields: title_score, bullet_score, image_score, aplus_score, rating_score, "
        "review_score, sentiment_score, lqs_total."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category":      {"type": "string", "description": "Filter by category (optional if asin_list given)"},
            "asin_list":     {"type": "array", "items": {"type": "string"}, "description": "Look up specific ASINs across any category"},
            "snapshot_date": {"type": "string"},
        },
    },
}


def run(category: str | None = None, asin_list: list[str] | None = None, snapshot_date: str | None = None) -> list[dict]:
    snap = snapshot_date or date.today().isoformat()

    # Fetch LQS rows
    lqs_query = supabase.table("listing_quality_score_daily").select("*").eq("snapshot_date", snap)
    if asin_list:
        lqs_query = lqs_query.in_("asin", asin_list)
    rows = lqs_query.execute().data or []

    # Fetch metadata for matched ASINs
    asins_in_rows = list({r["asin"] for r in rows})
    if not asins_in_rows:
        return []
    meta_query = supabase.table("asins").select("asin,product_name,brand,category")
    if category and not asin_list:
        meta_query = meta_query.eq("category", category)
    meta = {r["asin"]: r for r in meta_query.execute().data or []}

    out = [
        {**r, "product_name": meta[r["asin"]]["product_name"], "brand": meta[r["asin"]]["brand"], "category": meta[r["asin"]]["category"]}
        for r in rows if r["asin"] in meta
    ]

    # If category filter requested, apply post-hoc (covers both modes)
    if category and not asin_list:
        out = [r for r in out if r.get("category") == category]

    out.sort(key=lambda x: x.get("lqs_total") or 0, reverse=True)
    return out


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
