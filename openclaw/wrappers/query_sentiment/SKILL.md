---
name: query_sentiment
description: "Return daily customer sentiment aggregates (avg score, positive/negative ratio, review count) for Amazon ASINs from market-tracker. Use when user asks about customer sentiment, review trends, sentiment swings, voice of customer, or how customers feel about specific products over time. NOT for: raw review text (use query_reviews), or aspect-level breakdown (use query_aspects)."
metadata:
  {
    "openclaw":
      {
        "emoji": "💬",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_sentiment — Daily Sentiment Aggregates

Returns sentiment time series from RoBERTa-scored reviews, aggregated daily per ASIN.

## When to Use

✅ **USE this skill when:**
- "Sentiment for B0D14N2QZF last 14 days"
- "Sentiment trend cho ASIN này tuần qua"
- "Are customers happier this week?"
- "Show sentiment swings"

❌ **DON'T use this skill when:**
- User wants individual review quotes → use `query_reviews`
- User wants aspect breakdown (battery, sound, etc.) → use `query_aspects`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_sentiment.py '<json-args>'
```

### Arguments
| Field       | Type        | Required | Default | Notes                          |
|-------------|-------------|----------|---------|--------------------------------|
| `asin_list` | list[str]   | no       | `[]`    | Empty = all ASINs in DB        |
| `days`      | int         | no       | `7`     | 1–90                           |

### Examples

```bash
# Sentiment for one ASIN, last 14 days
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_sentiment.py '{"asin_list":["B0D14N2QZF"],"days":14}'

# All watchlist ASINs, default 7 days
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_sentiment.py '{}'

# Schema
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_sentiment.py --schema
```

## Output Shape

```json
[
  {
    "snapshot_date":       "2026-04-26",
    "asin":                "B0D14N2QZF",
    "review_count_new":    42,
    "avg_sentiment_score": 0.41,
    "positive_ratio":      0.78,
    "negative_ratio":      0.12
  }
]
```

## Notes
- Source table: `review_sentiment_daily`
- Powered by `cardiffnlp/twitter-roberta-base-sentiment-latest`
- Read-only.
