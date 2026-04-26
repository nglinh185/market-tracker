---
name: query_bms
description: "Return Brand Momentum Score (BMS) rankings for an Amazon category from market-tracker. Use when user asks about brand momentum, BMS, top movers, or which brands/ASINs are gaining traction in a category (gaming_keyboard | true_wireless_earbuds | portable_charger). NOT for: sentiment-only queries, price-only queries, or non-Amazon data."
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_bms — Brand Momentum Score

Returns BMS rankings for a category, sorted desc by `bms_score`, enriched with `product_name` and `brand`.

BMS composite:
```
bms = 0.5 × bsr_velocity_norm + 0.3 × review_velocity_norm + 0.2 × sentiment_norm
```

## When to Use

✅ **USE this skill when:**
- "Top BMS gaming_keyboard hôm nay"
- "Which earbuds brands have the most momentum?"
- "Brand momentum score for portable_charger"
- "Top movers in the keyboard category"

❌ **DON'T use this skill when:**
- User wants only sentiment → use `query_sentiment`
- User wants only price forecast → use `query_price_forecast`
- Category is not in: `gaming_keyboard`, `true_wireless_earbuds`, `portable_charger`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_bms.py '<json-args>'
```

### Arguments (JSON)
| Field           | Type   | Required | Default     |
| --------------- | ------ | -------- | ----------- |
| `category`      | string | **yes**  | —           |
| `top_n`         | int    | no       | `10` (1–50) |
| `snapshot_date` | string | no       | today (ISO) |

### Examples

```bash
# Top 5 brand momentum in gaming keyboards today
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_bms.py '{"category":"gaming_keyboard","top_n":5}'

# Top 10 in earbuds for a specific date
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_bms.py '{"category":"true_wireless_earbuds","top_n":10,"snapshot_date":"2026-04-25"}'

# Inspect input schema
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_bms.py --schema
```

## Output Shape

JSON array of objects:

```json
[
  {
    "snapshot_date":   "2026-04-26",
    "asin":            "B0C9ZJHQHM",
    "product_name":    "Womier SK80 75% Keyboard …",
    "brand":           null,
    "bsr_velocity":    0.1624,
    "review_velocity": 4.0,
    "sentiment_score": 0.6967,
    "bms_score":       0.4843
  }
]
```

## Notes

- Read-only skill, queries `brand_momentum_daily` joined with `asins` in Supabase.
- Requires daily analytics pipeline to have run (`scripts/run_analytics.py`).
- If no data for the date, returns `[]`.
