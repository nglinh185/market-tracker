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
        "Aggregate aspect-level sentiment across all reviews for an ASIN. "
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
    rows = (supabase.table("reviews_raw")
            .select("aspects_json")
            .eq("asin", asin)
            .not_.is_("aspects_json", "null")
            .limit(2000)
            .execute()).data or []

    agg: dict[str, dict] = defaultdict(lambda: {
        "name": "", "total_mentions": 0, "positive": 0, "negative": 0,
        "summaries": [], "sentiments": []
    })
    for r in rows:
        for a in (r.get("aspects_json") or []):
            name = (a.get("name") or "").lower().strip()
            if not name:
                continue
            slot = agg[name]
            slot["name"] = name
            slot["total_mentions"] += int(a.get("mentions") or 1)
            slot["positive"]       += int(a.get("positive") or 0)
            slot["negative"]       += int(a.get("negative") or 0)
            if a.get("sentiment"):
                slot["sentiments"].append(a["sentiment"])
            if a.get("summary") and len(slot["summaries"]) < 3:
                slot["summaries"].append(a["summary"])

    out = []
    for slot in agg.values():
        pos, neg = slot["positive"], slot["negative"]
        tot = pos + neg
        if tot == 0:
            polarity = max(set(slot["sentiments"]), key=slot["sentiments"].count) if slot["sentiments"] else "neutral"
        else:
            polarity = "positive" if pos/tot >= 0.65 else "negative" if neg/tot >= 0.65 else "mixed"
        out.append({
            "name":           slot["name"],
            "sentiment":      polarity,
            "total_mentions": slot["total_mentions"],
            "positive":       pos,
            "negative":       neg,
            "summary":        slot["summaries"][0] if slot["summaries"] else None,
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
