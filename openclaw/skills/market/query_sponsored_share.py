"""
Skill: query_sponsored_share
Brand share-of-voice in sponsored slots.
"""
from __future__ import annotations
import json
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase


SKILL = {
    "name": "query_sponsored_share",
    "group": "market",
    "description": (
        "Return sponsored share-of-voice leaders (brand, sponsored_slot_count, share_of_voice, "
        "organic_overlap_count) for a category keyword over the last N days."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "Used as keyword filter."},
            "days":     {"type": "integer", "default": 7, "minimum": 1, "maximum": 30},
            "top_n":    {"type": "integer", "default": 10},
        },
        "required": ["category"],
    },
}


def run(category: str, days: int = 7, top_n: int = 10) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    rows = (supabase.table("sponsored_ad_share_daily").select("*")
            .gte("snapshot_date", since)
            .ilike("keyword", f"%{category.replace('_', ' ')}%")
            .order("snapshot_date", desc=True).execute()).data or []
    rows.sort(key=lambda x: x.get("share_of_voice") or 0, reverse=True)
    return rows[:top_n]


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
