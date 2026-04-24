# Skill — `query_price_tiers`

- **Group:** market
- **Source:** `price_tier_daily`
- **Script:** `openclaw/skills/market/query_price_tiers.py`

## Purpose
Return K-Means price-tier clusters (`entry` / `mid` / `premium`) for a category's top 50. Each tier includes the ASIN count, price range, mean price, and up-to-20 representative ASINs. Tiers come from scikit-learn KMeans (k=3) fit nightly in `scripts/analyze_price_tier.py`.

## Inputs
| Field           | Type   | Required | Default     |
| --------------- | ------ | -------- | ----------- |
| `category`      | `str`  | **yes**  | —           |
| `snapshot_date` | `str`  | no       | today (ISO) |

## Output shape
```json
{
  "snapshot_date": "2026-04-21",
  "category":      "gaming_keyboard",
  "tiers": {
    "entry":   { "count": 18, "price_min": 19.99, "price_max": 39.99, "price_mean": 28.45, "asins": ["..."] },
    "mid":     { "count": 24, "price_min": 40.00, "price_max": 79.99, "price_mean": 54.90, "asins": ["..."] },
    "premium": { "count":  8, "price_min": 80.00, "price_max": 199.00, "price_mean": 119.50, "asins": ["..."] }
  }
}
```

## CLI
```bash
python openclaw/skills/market/query_price_tiers.py '{"category":"true_wireless_earbuds"}'
```

## Used by
- `competitor_spy` — detects positioning shifts (new entrant landing in mid tier, etc.)
