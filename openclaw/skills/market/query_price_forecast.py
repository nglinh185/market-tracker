"""
Skill: query_price_forecast
Prophet 7-day price forecast for an ASIN.
Reads from Supabase (price_forecast_daily) first; falls back to local
data/forecasts/*.json so a freshly-deployed VM can serve forecasts immediately
after CI runs the analytics, without depending on file sync between machines.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from dotenv import load_dotenv
load_dotenv()
from lib.db import supabase


FORECAST_DIR = Path(__file__).resolve().parents[3] / "data" / "forecasts"


SKILL = {
    "name": "query_price_forecast",
    "group": "market",
    "description": (
        "Return Prophet 7-day price forecast for an ASIN: "
        "[{ds, yhat, yhat_lower, yhat_upper}]. "
        "Source: price_forecast_daily (Supabase) with fallback to data/forecasts/*.json."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"asin": {"type": "string"}},
        "required": ["asin"],
    },
}


def _from_supabase(asin: str) -> list[dict] | None:
    # Read the most recent forecast batch for this ASIN.
    latest = (supabase.table("price_forecast_daily")
              .select("snapshot_date").eq("asin", asin)
              .order("snapshot_date", desc=True).limit(1).execute()).data or []
    if not latest:
        return None
    snap = latest[0]["snapshot_date"]
    rows = (supabase.table("price_forecast_daily")
            .select("ds,yhat,yhat_lower,yhat_upper")
            .eq("asin", asin).eq("snapshot_date", snap)
            .order("ds").execute()).data or []
    return rows or None


def _from_file(asin: str) -> tuple[str, list[dict]] | None:
    if not FORECAST_DIR.exists():
        return None
    for fp in sorted(FORECAST_DIR.glob("price_forecast_*.json"), reverse=True):
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if asin in data:
            return fp.name, data[asin]
    return None


def run(asin: str) -> dict:
    try:
        rows = _from_supabase(asin)
        if rows:
            return {"asin": asin, "source": "price_forecast_daily", "forecast": rows}
    except Exception:
        # Migration 005 not yet applied, or transient Supabase error — fall through.
        pass

    file_hit = _from_file(asin)
    if file_hit:
        fname, points = file_hit
        return {"asin": asin, "source": fname, "forecast": points}

    return {"asin": asin, "forecast": [], "note": "No forecast available (need ≥3 data points)."}


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
