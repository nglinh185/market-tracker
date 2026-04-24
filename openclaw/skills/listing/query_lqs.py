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
        "Return Listing Quality Score (0-100) for all ASINs in a category: "
        "title_score, bullet_score, image_score, aplus_score, rating_score, review_score, "
        "sentiment_score, lqs_total. Source: listing_quality_score_daily + asins."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category":      {"type": "string"},
            "snapshot_date": {"type": "string"},
        },
        "required": ["category"],
    },
}


def run(category: str, snapshot_date: str | None = None) -> list[dict]:
    snap = snapshot_date or date.today().isoformat()
    meta = {r["asin"]: r for r in (
        supabase.table("asins").select("asin,product_name,brand,category")
        .eq("category", category).execute()
    ).data or []}
    rows = (supabase.table("listing_quality_score_daily")
            .select("*").eq("snapshot_date", snap).execute()).data or []
    out = [{**r, "product_name": meta[r["asin"]]["product_name"], "brand": meta[r["asin"]]["brand"]}
           for r in rows if r["asin"] in meta]
    out.sort(key=lambda x: x.get("lqs_total") or 0, reverse=True)
    return out


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
