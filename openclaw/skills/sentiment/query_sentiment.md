# Skill — `query_sentiment`

- **Group:** sentiment
- **Source:** `review_sentiment_daily`
- **Script:** `openclaw/skills/sentiment/query_sentiment.py`

## Purpose
Return daily sentiment aggregates (`avg_sentiment_score`, `positive_ratio`, `negative_ratio`, `review_count_new`) for a list of ASINs over the last *N* days. Use to detect sentiment swings or multi-day trajectories.

## Inputs
| Field       | Type          | Required | Default | Notes                                  |
| ----------- | ------------- | -------- | ------- | -------------------------------------- |
| `asin_list` | `list[str]`   | no       | `[]`    | Empty = all ASINs in the table.        |
| `days`      | `int`         | no       | `7`     | 1–90.                                  |

## Output shape
```json
[
  {
    "snapshot_date":        "2026-04-21",
    "asin":                 "B0D14N2QZF",
    "review_count_new":     42,
    "avg_sentiment_score":  0.41,
    "positive_ratio":       0.78,
    "negative_ratio":       0.12
  }
]
```

## CLI
```bash
python openclaw/skills/sentiment/query_sentiment.py '{"asin_list":["B0D14N2QZF"],"days":14}'
python openclaw/skills/sentiment/query_sentiment.py --schema
```

## Used by
- `sentiment_detective` (primary)
- `momentum_strategist` (sanity check)
