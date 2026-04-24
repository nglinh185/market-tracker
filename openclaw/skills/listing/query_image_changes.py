"""
Skill: query_image_changes
pHash-detected image change events.
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
    "name": "query_image_changes",
    "group": "listing",
    "description": (
        "Return pHash image-change events (hash_distance, change_flag) for a list of ASINs "
        "in the last N days. High distance = listing redesign."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "asin_list": {"type": "array", "items": {"type": "string"}},
            "days":      {"type": "integer", "default": 7, "minimum": 1, "maximum": 30},
        },
        "required": [],
    },
}


def run(asin_list: list[str] | None = None, days: int = 7) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    q = (supabase.table("image_change_events")
         .select("snapshot_date,asin,hash_before,hash_after,hash_distance,change_flag")
         .gte("snapshot_date", since).order("snapshot_date", desc=True))
    if asin_list:
        q = q.in_("asin", asin_list)
    return q.execute().data or []


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
