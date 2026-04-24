# Skill — `query_snapshots`

- **Group:** listing
- **Source:** `daily_snapshots`
- **Script:** `openclaw/skills/listing/query_snapshots.py`

## Purpose
Return the full daily price / BSR / stock / bullet / stars time series for a single ASIN. Used to correlate sentiment or rank moves with listing-side changes.

## Inputs
| Field   | Type   | Required | Default     |
| ------- | ------ | -------- | ----------- |
| `asin`  | `str`  | **yes**  | —           |
| `days`  | `int`  | no       | `14` (1–90) |

## Output shape
```json
[
  {
    "snapshot_date": "2026-04-21",
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

## CLI
```bash
python openclaw/skills/listing/query_snapshots.py '{"asin":"B0D14N2QZF","days":30}'
```

## Used by
- `sentiment_detective` — correlate sentiment drops with price/stock changes
