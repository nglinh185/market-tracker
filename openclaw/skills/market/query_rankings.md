# Skill — `query_rankings`

- **Group:** market
- **Source:** `category_rankings`
- **Script:** `openclaw/skills/market/query_rankings.py`

## Purpose
Return the top-*N* products in a category for a given snapshot date, ordered by `rank`. The raw top-50 table that every other signal is derived from.

## Inputs
| Field           | Type   | Required | Default     |
| --------------- | ------ | -------- | ----------- |
| `category`      | `str`  | **yes**  | —           |
| `top_n`         | `int`  | no       | `20` (1–50) |
| `snapshot_date` | `str`  | no       | today (ISO) |

## Output shape
```json
[
  {
    "rank":          1,
    "asin":          "B0D14N2QZF",
    "title":         "AULA F75 Pro 75% Mechanical...",
    "brand":         "AULA",
    "price":         64.99,
    "stars":         4.6,
    "reviews_count": 1854,
    "is_sponsored":  false,
    "thumbnail_url": "https://..."
  }
]
```

## CLI
```bash
python openclaw/skills/market/query_rankings.py '{"category":"portable_charger","top_n":10}'
```

## Used by
- `competitor_spy`
