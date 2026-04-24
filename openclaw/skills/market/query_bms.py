"""
Skill: query_bms
Brand Momentum Score (BMS) ranked per category.
BMS = 0.5·bsr_velocity + 0.3·review_velocity + 0.2·sentiment.
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
    "name": "query_bms",
    "group": "market",
    "description": (
        "Return BMS rows for the given category, joined with product_name/brand, sorted "
        "desc by bms_score. Source: brand_momentum_daily + asins."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "category":      {"type": "string", "description": "gaming_keyboard | true_wireless_earbuds | portable_charger"},
            "top_n":         {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
            "snapshot_date": {"type": "string", "description": "ISO date. Default: today."},
        },
        "required": ["category"],
    },
}


def run(category: str, top_n: int = 10, snapshot_date: str | None = None) -> list[dict]:
    snap = snapshot_date or date.today().isoformat()
    meta = {r["asin"]: r for r in (
        supabase.table("asins").select("asin,product_name,brand,category")
        .eq("category", category).execute()
    ).data or []}
    bms = (supabase.table("brand_momentum_daily")
           .select("*").eq("snapshot_date", snap).execute()).data or []
    joined = [
        {**r, "product_name": meta[r["asin"]]["product_name"], "brand": meta[r["asin"]]["brand"]}
        for r in bms if r["asin"] in meta
    ]
    joined.sort(key=lambda x: x.get("bms_score") or 0, reverse=True)
    return joined[:top_n]


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
