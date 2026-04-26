---
name: query_lqs
description: "Return Listing Quality Score (LQS, 0–100) for every ASIN in an Amazon category, broken down by component (title, bullet, image, A+, rating, review, sentiment). Use when user asks about listing quality, listing optimization, weakest sellers, low-LQS top sellers ('cheap wins'), or what a listing scores. NOT for: brand momentum (use query_bms), or sentiment alone (use query_sentiment)."
metadata:
  {
    "openclaw":
      {
        "emoji": "📐",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_lqs — Listing Quality Score

Returns LQS (0–100) per ASIN for a category, with component breakdown.

| Component         | Max |
|-------------------|-----|
| `title_score`     | 10  |
| `bullet_score`    | 15  |
| `image_score`     | 15  |
| `aplus_score`     | 15  |
| `rating_score`    | 20  |
| `review_score`    | 15  |
| `sentiment_score` | 10  |
| **Total**         | 100 |

## When to Use

✅ **USE this skill when:**
- "LQS scores for gaming_keyboard"
- "Listing chất lượng kém nhất trong top 50"
- "Cheap wins — top sellers with low LQS"
- "Listing optimization opportunities"

❌ **DON'T use this skill when:**
- User wants brand momentum → `query_bms`
- User wants sentiment only → `query_sentiment`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_lqs.py '<json-args>'
```

### Arguments
| Field           | Type | Required | Default     |
|-----------------|------|----------|-------------|
| `category`      | str  | **yes**  | —           |
| `snapshot_date` | str  | no       | today (ISO) |

### Examples

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_lqs.py '{"category":"gaming_keyboard"}'
```

## Output Shape

```json
[
  {
    "snapshot_date":   "2026-04-26",
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

## Notes
- Source: `listing_quality_score_daily` joined with `asins`
- Read-only.
