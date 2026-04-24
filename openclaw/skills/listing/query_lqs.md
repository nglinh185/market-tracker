# Skill — `query_lqs`

- **Group:** listing
- **Source:** `listing_quality_score_daily` joined with `asins`
- **Script:** `openclaw/skills/listing/query_lqs.py`

## Purpose
Return Listing Quality Score (LQS, 0–100) for every ASIN in a category, sorted descending. Components from `scripts/analyze_lqs.py`:

| Component         | Max |
| ----------------- | --- |
| `title_score`     | 10  |
| `bullet_score`    | 15  |
| `image_score`     | 15  |
| `aplus_score`     | 15  |
| `rating_score`    | 20  |
| `review_score`    | 15  |
| `sentiment_score` | 10  |
| **Total**         | 100 |

## Inputs
| Field           | Type   | Required | Default     |
| --------------- | ------ | -------- | ----------- |
| `category`      | `str`  | **yes**  | —           |
| `snapshot_date` | `str`  | no       | today (ISO) |

## Output shape
```json
[
  {
    "snapshot_date":   "2026-04-21",
    "asin":            "B0D14N2QZF",
    "product_name":    "AULA F75 Pro",
    "brand":           "AULA",
    "title_score":     10,
    "bullet_score":    15,
    "image_score":     15,
    "aplus_score":     15,
    "rating_score":    18,
    "review_score":    12,
    "sentiment_score":  8,
    "lqs_total":       93
  }
]
```

## CLI
```bash
python openclaw/skills/listing/query_lqs.py '{"category":"gaming_keyboard"}'
```

## Used by
- `momentum_strategist` (primary — flags low-LQS top sellers as cheap wins)
