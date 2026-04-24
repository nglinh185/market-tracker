"""
Skill: query_sentiment
Daily sentiment aggregates by ASIN from review_sentiment_daily.
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
    "name": "query_sentiment",
    "group": "sentiment",
    "description": (
        "Return daily sentiment aggregates (avg_sentiment_score, positive_ratio, "
        "negative_ratio, review_count_new) for a list of ASINs over the last N days. "
        "Source: review_sentiment_daily. Use to detect sentiment swings or trajectory."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "asin_list": {"type": "array", "items": {"type": "string"},
                          "description": "List of ASINs. Empty = all ASINs."},
            "days":      {"type": "integer", "default": 7, "minimum": 1, "maximum": 90},
        },
        "required": [],
    },
}


def run(asin_list: list[str] | None = None, days: int = 7) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    q = (supabase.table("review_sentiment_daily")
         .select("snapshot_date,asin,review_count_new,avg_sentiment_score,positive_ratio,negative_ratio")
         .gte("snapshot_date", since)
         .order("snapshot_date", desc=True))
    if asin_list:
        q = q.in_("asin", asin_list)
    return q.execute().data or []


def main() -> None:
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1] not in ("--schema",) else {}
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
