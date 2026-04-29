# Skill — `query_aspects`

- **Group:** sentiment
- **Source:** `reviews_raw.aspects_json` (JSONB)
- **Script:** `openclaw/skills/sentiment/query_aspects.py`

## Purpose
Return Amazon's product-level aspect summary for an ASIN. The `aspects_json` field stored on `reviews_raw` is the **same pre-aggregated summary that Amazon publishes per product** (mentions / positive / negative / summary computed by Amazon over the full review base, not per single review). To avoid n×inflation, this skill takes the most-recent non-null row for the ASIN, then ranks aspects by `total_mentions` and computes a polarity label (`positive` / `negative` / `mixed` / `neutral`) from the positive/negative split.

> Earlier versions of this skill summed across every review row, which inflated `total_mentions` by N (one per review). Fixed 2026-04-27 — see PROGRESS.md changelog.

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
