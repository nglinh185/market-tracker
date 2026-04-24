"""
Skill: query_reviews
Raw review records for an ASIN — qualitative evidence for sentiment reasoning.
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
    "name": "query_reviews",
    "group": "sentiment",
    "description": (
        "Return raw review records (review_text, rating, title, review_date, sentiment_label) "
        "for a specific ASIN, optionally filtered by sentiment polarity. "
        "Use this to quote representative customer voices as evidence."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "asin":      {"type": "string"},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "any"], "default": "any"},
            "limit":     {"type": "integer", "default": 5, "minimum": 1, "maximum": 25},
        },
        "required": ["asin"],
    },
}


def run(asin: str, sentiment: str = "any", limit: int = 5) -> list[dict]:
    q = (supabase.table("reviews_raw")
         .select("review_id,review_date,rating,title,review_text,sentiment_label,sentiment_score,helpful_votes,verified")
         .eq("asin", asin)
         .order("review_date", desc=True)
         .limit(limit))
    if sentiment != "any":
        q = q.eq("sentiment_label", sentiment)
    rows = q.execute().data or []
    for r in rows:
        if r.get("review_text"):
            r["review_text"] = r["review_text"][:600]
    return rows


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
