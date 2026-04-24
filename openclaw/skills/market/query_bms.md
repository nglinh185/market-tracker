# Skill — `query_bms`

- **Group:** market
- **Source:** `brand_momentum_daily` joined with `asins`
- **Script:** `openclaw/skills/market/query_bms.py`

## Purpose
Return Brand Momentum Score (BMS) rankings for a category. BMS composite:

> `bms = 0.5 × bsr_velocity_norm + 0.3 × review_velocity_norm + 0.2 × sentiment_norm`

Results are sorted descending by `bms_score` and enriched with `product_name` and `brand`.

## Inputs
| Field           | Type   | Required | Default     |
| --------------- | ------ | -------- | ----------- |
| `category`      | `str`  | **yes**  | —           |
| `top_n`         | `int`  | no       | `10` (1–50) |
| `snapshot_date` | `str`  | no       | today (ISO) |

## Output shape
```json
[
  {
    "snapshot_date":   "2026-04-21",
    "asin":            "B0D14N2QZF",
    "product_name":    "AULA F75 Pro",
    "brand":           "AULA",
    "bsr_velocity":    0.12,
    "review_velocity": 8.0,
    "sentiment_score": 0.41,
    "bms_score":       0.81
  }
]
```

## CLI
```bash
python openclaw/skills/market/query_bms.py '{"category":"gaming_keyboard","top_n":5}'
```

## Used by
- `competitor_spy` (primary)
- `momentum_strategist`
