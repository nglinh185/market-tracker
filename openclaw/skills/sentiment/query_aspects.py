"""
Skill: query_aspects
Aggregated aspect sentiment from reviews_raw.aspects_json.
"""
from __future__ import annotations
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase


SKILL = {
    "name": "query_aspects",
    "group": "sentiment",
    "description": (
        "Return Amazon's product-level aspect summary for an ASIN "
        "(already pre-aggregated by Amazon across the full review base). "
        "Returns [{name, sentiment, total_mentions, positive, negative, summary}] "
        "ranked by total_mentions. Use to identify what customers love vs hate."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "asin":  {"type": "string"},
            "top_n": {"type": "integer", "default": 10, "minimum": 1, "maximum": 50},
        },
        "required": ["asin"],
    },
}


def run(asin: str, top_n: int = 10) -> list[dict]:
    # aspects_json from Apify is Amazon's PRODUCT-LEVEL summary (same for every review row).
    # Take the most recent non-null row instead of aggregating, to avoid n-times inflation.
    rows = (supabase.table("reviews_raw")
            .select("aspects_json,review_date")
            .eq("asin", asin)
            .not_.is_("aspects_json", "null")
            .order("review_date", desc=True)
            .limit(1)
            .execute()).data or []

    if not rows:
        return []

    aspects = rows[0].get("aspects_json") or []
    out = []
    for a in aspects:
        name = (a.get("name") or "").strip()
        if not name:
            continue
        pos = int(a.get("positive") or 0)
        neg = int(a.get("negative") or 0)
        tot = pos + neg
        if tot == 0:
            polarity = a.get("sentiment") or "neutral"
        else:
            polarity = "positive" if pos/tot >= 0.65 else "negative" if neg/tot >= 0.65 else "mixed"
        out.append({
            "name":           name.lower(),
            "sentiment":      polarity,
            "total_mentions": int(a.get("mentions") or 0),
            "positive":       pos,
            "negative":       neg,
            "summary":        a.get("summary"),
        })
    out.sort(key=lambda x: x["total_mentions"], reverse=True)
    return out[:top_n]


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
