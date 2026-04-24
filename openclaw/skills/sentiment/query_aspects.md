# Skill — `query_aspects`

- **Group:** sentiment
- **Source:** `reviews_raw.aspects_json` (JSONB)
- **Script:** `openclaw/skills/sentiment/query_aspects.py`

## Purpose
Aggregate aspect-level sentiment across every review for an ASIN. Returns aspects ranked by total mentions, with a computed polarity label (`positive` / `negative` / `mixed` / `neutral`) based on the positive/negative mention split.

## Inputs
| Field   | Type   | Required | Default | Notes     |
| ------- | ------ | -------- | ------- | --------- |
| `asin`  | `str`  | **yes**  | —       |           |
| `top_n` | `int`  | no       | `10`    | 1–50.     |

## Output shape
```json
[
  {
    "name":           "battery life",
    "sentiment":      "negative",
    "total_mentions": 87,
    "positive":       12,
    "negative":       68,
    "summary":        "Users report 3-4 hour runtime, half of advertised 8h."
  }
]
```

Polarity rule: `positive` if positive/(pos+neg) ≥ 0.65, `negative` if negative ratio ≥ 0.65, otherwise `mixed`. Falls back to majority-vote over raw sentiment labels if no pos/neg counts.

## CLI
```bash
python openclaw/skills/sentiment/query_aspects.py '{"asin":"B0D14N2QZF","top_n":15}'
```

## Used by
- `sentiment_detective` (primary — identifies what customers actually talk about)
