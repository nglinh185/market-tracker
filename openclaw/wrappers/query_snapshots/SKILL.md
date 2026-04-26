---
name: query_snapshots
description: "Return daily time series (price, BSR, stock, stars, review count, bullet count, list price, discount %) for a single Amazon ASIN. Use when user wants to see price history, BSR trend, stock movement, listing changes over time for a specific product. NOT for: category rankings (use query_rankings), or sentiment (use query_sentiment)."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_snapshots — Daily Time Series for an ASIN

Returns full daily price/BSR/stock/listing time series for a single ASIN. Used to correlate sentiment or rank moves with listing-side changes.

## When to Use

✅ **USE this skill when:**
- "Price history of B0D14N2QZF last 30 days"
- "BSR trend cho ASIN này"
- "When did this product go out of stock?"
- "Listing changes time series"

❌ **DON'T use this skill when:**
- User wants category top → `query_rankings`
- User wants future price → `query_price_forecast`
- User wants sentiment → `query_sentiment`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_snapshots.py '<json-args>'
```

### Arguments
| Field  | Type | Required | Default     |
|--------|------|----------|-------------|
| `asin` | str  | **yes**  | —           |
| `days` | int  | no       | `14` (1–90) |

### Examples

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_snapshots.py '{"asin":"B0D14N2QZF","days":30}'
```

## Output Shape

```json
[
  {
    "snapshot_date": "2026-04-26",
    "price":         64.99,
    "list_price":    79.99,
    "discount_pct":  18,
    "bsr":           123,
    "in_stock":      true,
    "stars":         4.6,
    "reviews_count": 1854,
    "bullet_count":  5
  }
]
```

## Notes
- Source: `daily_snapshots` table
- Read-only.
