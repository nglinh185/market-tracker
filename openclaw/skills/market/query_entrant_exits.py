"""
Skill: query_entrant_exits
Top-50 market entry/exit events per category.
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
    "name": "query_entrant_exits",
    "group": "market",
    "description": (
        "Return top-50 entry/exit events (type=entrant|exit) for a category in the last N days. "
        "is_top10 flag marks high-impact moves. Source: entrant_exit_events."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string"},
            "days":     {"type": "integer", "default": 7, "minimum": 1, "maximum": 30},
        },
        "required": ["category"],
    },
}


def run(category: str, days: int = 7) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    return (supabase.table("entrant_exit_events")
            .select("snapshot_date,asin,event_type,rank_today,rank_yesterday,is_top10")
            .eq("browse_node", category).gte("snapshot_date", since)
            .order("snapshot_date", desc=True).execute()).data or []


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
