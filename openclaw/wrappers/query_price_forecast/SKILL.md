---
name: query_price_forecast
description: "Return Prophet-based 7-day price forecast for a single Amazon ASIN with confidence bounds (yhat_lower / yhat_upper). Use when user asks about price prediction, future price, will price drop, price trend forecast, or expected price next week. NOT for: current/past prices (use query_snapshots), or category-wide tiers (use query_price_tiers)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🔮",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_price_forecast — Prophet 7-Day Price Forecast

Returns the latest Facebook Prophet 7-day price forecast for an ASIN. Requires ≥3 historical data points.

## When to Use

✅ **USE this skill when:**
- "Will B0D14N2QZF drop in price next week?"
- "Dự đoán giá ASIN này 7 ngày tới"
- "Price forecast for this product"
- "Expected price by next Monday"

❌ **DON'T use this skill when:**
- User wants current/historical price → `query_snapshots`
- User wants category price tiers → `query_price_tiers`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_price_forecast.py '<json-args>'
```

### Arguments
| Field  | Type | Required |
|--------|------|----------|
| `asin` | str  | **yes**  |

### Examples

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_price_forecast.py '{"asin":"B0D14N2QZF"}'
```

## Output Shape

```json
{
  "asin":     "B0D14N2QZF",
  "source":   "price_forecast_daily",
  "forecast": [
    { "ds": "2026-04-27", "yhat": 62.40, "yhat_lower": 60.10, "yhat_upper": 64.80 }
  ]
}
```

If no forecast yet:
```json
{ "asin": "...", "forecast": [], "note": "No forecast available (need ≥3 data points)." }
```

## Notes
- Source: `price_forecast_daily` (Supabase) with fallback to `data/forecasts/price_forecast_<date>.json`. The Supabase table is the canonical source so the OpenClaw VM can serve forecasts produced by GitHub Actions.
- Generated nightly by `scripts/analyze_price_forecast.py`
- n=14 days → trend analysis only, not high-precision prediction
