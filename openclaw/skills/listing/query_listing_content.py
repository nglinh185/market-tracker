"""
Skill: query_listing_content
Returns static listing content for one ASIN: title, description,
bullet_count, image_url, stars, reviews_count (latest snapshot).

NOTE: actual bullet text is NOT stored in the DB (only bullet_count is
persisted). Use bullet_count to flag thin listings (< 5 bullets).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase

SKILL = {
    "name": "query_listing_content",
    "group": "listing",
    "description": (
        "Return static listing content for one ASIN: product title, "
        "description, bullet_count, image_url, stars, reviews_count "
        "from the latest available snapshot. Use before recommending "
        "listing edits so recommendations are grounded in real data. "
        "NOTE: individual bullet text is not stored — only bullet_count."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "asin": {"type": "string", "description": "Amazon ASIN"},
        },
        "required": ["asin"],
    },
}


def run(asin: str) -> dict:
    # Title from asins table
    asin_row = (
        supabase.table("asins")
        .select("asin,product_name,brand,category")
        .eq("asin", asin)
        .limit(1)
        .execute()
    ).data
    title = asin_row[0].get("product_name") if asin_row else None
    brand = asin_row[0].get("brand") if asin_row else None
    category = asin_row[0].get("category") if asin_row else None

    # Latest snapshot for description, bullet_count, image_url
    snap = (
        supabase.table("daily_snapshots")
        .select("snapshot_date,description,bullet_count,image_url,stars,reviews_count,ebc_html_hash")
        .eq("asin", asin)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    ).data

    if not snap:
        return {
            "asin": asin,
            "found": False,
            "note": "No snapshot data found for this ASIN.",
        }

    s = snap[0]
    has_aplus = bool(s.get("ebc_html_hash"))
    title_words = len(title.split()) if title else 0

    # Listing health flags (same thresholds as LQS)
    flags: list[str] = []
    if title_words < 10:
        flags.append(f"title too short ({title_words} words, target ≥10)")
    if (s.get("bullet_count") or 0) < 5:
        flags.append(f"thin bullets ({s.get('bullet_count') or 0} bullets, target ≥5)")
    if not s.get("description"):
        flags.append("no description stored")
    if not has_aplus:
        flags.append("no A+ content detected")

    return {
        "asin":          asin,
        "found":         True,
        "brand":         brand,
        "category":      category,
        "title":         title,
        "title_words":   title_words,
        "bullet_count":  s.get("bullet_count"),
        "description":   s.get("description"),
        "has_aplus":     has_aplus,
        "image_url":     s.get("image_url"),
        "stars":         s.get("stars"),
        "reviews_count": s.get("reviews_count"),
        "as_of":         s.get("snapshot_date"),
        "listing_flags": flags,
        "note": (
            "bullet_count is a count only — individual bullet text is not "
            "stored in the database. Flag thin listings (< 5 bullets) "
            "but do not quote or invent specific bullet content."
        ),
    }


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2))
        return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
