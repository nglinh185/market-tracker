# Skill — `query_reviews`

- **Group:** sentiment
- **Source:** `reviews_raw`
- **Script:** `openclaw/skills/sentiment/query_reviews.py`

## Purpose
Return raw review records for a specific ASIN, optionally filtered by sentiment polarity. Used to quote representative customer voices as evidence for every sentiment claim.

## Inputs
| Field       | Type   | Required | Default | Notes                                                |
| ----------- | ------ | -------- | ------- | ---------------------------------------------------- |
| `asin`      | `str`  | **yes**  | —       |                                                      |
| `sentiment` | `str`  | no       | `any`   | `positive` \| `neutral` \| `negative` \| `any`       |
| `limit`     | `int`  | no       | `5`     | 1–25. Text is truncated to 600 chars per record.     |

## Output shape
```json
[
  {
    "review_id":       "R1234...",
    "review_date":     "2026-04-18",
    "rating":          2,
    "title":           "Disappointing battery life",
    "review_text":     "…",
    "sentiment_label": "negative",
    "sentiment_score": -0.62,
    "helpful_votes":   4,
    "verified":        true
  }
]
```

## CLI
```bash
python openclaw/skills/sentiment/query_reviews.py '{"asin":"B0D14N2QZF","sentiment":"negative","limit":5}'
```

## Used by
- `sentiment_detective`
