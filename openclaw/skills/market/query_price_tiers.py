"""
Skill: query_price_tiers
K-Means price-tier clusters (entry/mid/premium) per category.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase


SKILL = {
    "name": "query_price_tiers",
    "group": "market",
    "description": (
        "Return K-Means price-tier clusters (entry/mid/premium) for a category's top-50. "
        "Includes price ranges and ASIN count per tier. Source: price_tier_daily."
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


def run(category: str, snapshot_date: str | None = None) -> dict:
    snap = snapshot_date or date.today().isoformat()
    rows = (supabase.table("price_tier_daily").select("*")
            .eq("browse_node", category).eq("snapshot_date", snap).execute()).data or []
    tiers: dict[str, dict] = defaultdict(lambda: {"count": 0, "prices": [], "asins": []})
    for r in rows:
        t = tiers[r["cluster_name"]]
        t["count"] += 1
        t["prices"].append(float(r["price"]))
        t["asins"].append(r["asin"])
    summary = {}
    for name, t in tiers.items():
        prices = sorted(t["prices"])
        summary[name] = {
            "count":      t["count"],
            "price_min":  prices[0] if prices else None,
            "price_max":  prices[-1] if prices else None,
            "price_mean": round(sum(prices)/len(prices), 2) if prices else None,
            "asins":      t["asins"][:20],
        }
    return {"snapshot_date": snap, "category": category, "tiers": summary}


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
