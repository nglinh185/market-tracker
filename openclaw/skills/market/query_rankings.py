"""
Skill: query_rankings
Current top-N products per category from category_rankings.
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
    "name": "query_rankings",
    "group": "market",
    "description": (
        "Return the top-N products in a category for a given snapshot. "
        "Fields: rank, asin, title, brand, price, stars, reviews_count, is_sponsored."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category":      {"type": "string"},
            "top_n":         {"type": "integer", "default": 20, "minimum": 1, "maximum": 50},
            "snapshot_date": {"type": "string"},
        },
        "required": ["category"],
    },
}


def run(category: str, top_n: int = 20, snapshot_date: str | None = None) -> list[dict]:
    snap = snapshot_date or date.today().isoformat()
    return (supabase.table("category_rankings")
            .select("rank,asin,title,brand,price,stars,reviews_count,is_sponsored,thumbnail_url")
            .eq("browse_node", category).eq("snapshot_date", snap)
            .order("rank").limit(top_n).execute()).data or []


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
