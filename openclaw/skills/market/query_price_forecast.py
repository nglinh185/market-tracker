"""
Skill: query_price_forecast
Prophet 7-day price forecast for an ASIN (from data/forecasts/*.json).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


FORECAST_DIR = Path(__file__).resolve().parents[3] / "data" / "forecasts"


SKILL = {
    "name": "query_price_forecast",
    "group": "market",
    "description": (
        "Return Prophet 7-day price forecast for an ASIN: "
        "[{ds, yhat, yhat_lower, yhat_upper}]. Source: data/forecasts/*.json."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"asin": {"type": "string"}},
        "required": ["asin"],
    },
}


def run(asin: str) -> dict:
    files = sorted(FORECAST_DIR.glob("price_forecast_*.json"), reverse=True) if FORECAST_DIR.exists() else []
    for fp in files:
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if asin in data:
            return {"asin": asin, "source_file": fp.name, "forecast": data[asin]}
    return {"asin": asin, "forecast": [], "note": "No forecast available (need ≥3 data points)."}


def main() -> None:
    if "--schema" in sys.argv:
        print(json.dumps(SKILL, indent=2)); return
    args = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    print(json.dumps(run(**args), default=str))


if __name__ == "__main__":
    main()
