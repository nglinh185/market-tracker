---
name: query_price_tiers
description: "Return K-Means price-tier clusters (entry/mid/premium) for an Amazon category's top 50 — count, price range, mean price, and representative ASINs per tier. Use when user asks about price segmentation, pricing strategy, market positioning, entry vs premium tiers, or price clusters. NOT for: forecast (use query_price_forecast), or single-ASIN price history (use query_snapshots)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🏷️",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_price_tiers — KMeans Price Segmentation

Returns price-tier clusters (entry/mid/premium) computed via scikit-learn KMeans (k=3) over the category's top 50.

## When to Use

✅ **USE this skill when:**
- "Price tiers cho gaming_keyboard"
- "Phân khúc giá trong category này thế nào?"
- "Entry vs premium positioning"
- "Where does $50 fit in the keyboard market?"

❌ **DON'T use this skill when:**
- User wants future price → `query_price_forecast`
- User wants one ASIN's price history → `query_snapshots`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_price_tiers.py '<json-args>'
```

### Arguments
| Field           | Type | Required | Default     |
|-----------------|------|----------|-------------|
| `category`      | str  | **yes**  | —           |
| `snapshot_date` | str  | no       | today (ISO) |

### Examples

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_price_tiers.py '{"category":"true_wireless_earbuds"}'
```

## Output Shape

```json
{
  "snapshot_date": "2026-04-26",
  "category":      "gaming_keyboard",
  "tiers": {
    "entry":   { "count": 18, "price_min": 19.99, "price_max": 39.99, "price_mean": 28.45, "asins": ["..."] },
    "mid":     { "count": 24, "price_min": 40.00, "price_max": 79.99, "price_mean": 54.90, "asins": ["..."] },
    "premium": { "count":  8, "price_min": 80.00, "price_max": 199.00, "price_mean": 119.50, "asins": ["..."] }
  }
}
```

## Notes
- Source: `price_tier_daily` table
- Computed nightly by `scripts/analyze_price_tier.py`
- Read-only.
