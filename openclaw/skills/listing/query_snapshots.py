"""
Skill: query_snapshots
Daily price/BSR/stock time series for an ASIN.
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
    "name": "query_snapshots",
    "group": "listing",
    "description": (
        "Return daily_snapshots rows for an ASIN over the last N days: "
        "price, list_price, discount_pct, bsr, in_stock, stars, reviews_count."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "asin": {"type": "string"},
            "days": {"type": "integer", "default": 14, "minimum": 1, "maximum": 90},
        },
        "required": ["asin"],
    },
}


def run(asin: str, days: int = 14) -> list[dict]:
    since = (date.today() - timedelta(days=days)).isoformat()
    return (supabase.table("daily_snapshots")
            .select("snapshot_date,price,list_price,discount_pct,bsr,in_stock,stars,reviews_count,bullet_count")
            .eq("asin", asin).gte("snapshot_date", since)
            .order("snapshot_date").execute()).data or []


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
