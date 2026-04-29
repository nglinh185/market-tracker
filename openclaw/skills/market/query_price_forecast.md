# Skill — `query_price_forecast`

- **Group:** market
- **Source:** `price_forecast_daily` (Supabase) — falls back to `data/forecasts/price_forecast_<date>.json`
- **Script:** `openclaw/skills/market/query_price_forecast.py`

## Purpose
Return the latest Prophet 7-day price forecast for an ASIN. Forecasts come from `scripts/analyze_price_forecast.py` and require ≥3 historical data points. Persisted to Supabase so the OpenClaw VM can read them after CI runs the analytics on a different machine.

## Inputs
| Field  | Type   | Required |
| ------ | ------ | -------- |
| `asin` | `str`  | **yes**  |

## Output shape
```json
{
  "asin":     "B0D14N2QZF",
  "source":   "price_forecast_daily",
  "forecast": [
    { "ds": "2026-04-22", "yhat": 62.40, "yhat_lower": 60.10, "yhat_upper": 64.80 }
  ]
}
```

If no forecast exists yet, returns:
```json
{ "asin": "...", "forecast": [], "note": "No forecast available (need ≥3 data points)." }
```

## CLI
```bash
python openclaw/skills/market/query_price_forecast.py '{"asin":"B0D14N2QZF"}'
```

## Used by
- `momentum_strategist` (primary)
