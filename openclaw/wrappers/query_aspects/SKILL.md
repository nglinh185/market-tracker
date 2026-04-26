---
name: query_aspects
description: "Return aspect-level sentiment breakdown for an Amazon ASIN — what specific product features (battery, sound, build quality, etc.) customers praise vs complain about, ranked by mention count. Use when user asks about product strengths/weaknesses, what features customers care about, or aspect-level analysis. NOT for: overall sentiment scores (use query_sentiment), or raw quotes (use query_reviews)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🔍",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_aspects — Aspect-Level Sentiment

Aggregates aspect-level sentiment from `reviews_raw.aspects_json` (JSONB). Ranks aspects by total mentions with computed polarity (`positive` / `negative` / `mixed`).

## When to Use

✅ **USE this skill when:**
- "What do customers like/dislike about B0D14N2QZF?"
- "Aspect analysis cho ASIN này"
- "Pain points of this product"
- "Top features customers mention"

❌ **DON'T use this skill when:**
- User wants overall sentiment trend → `query_sentiment`
- User wants raw review text → `query_reviews`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_aspects.py '<json-args>'
```

### Arguments
| Field   | Type | Required | Default | Notes |
|---------|------|----------|---------|-------|
| `asin`  | str  | **yes**  | —       |       |
| `top_n` | int  | no       | `10`    | 1–50  |

### Examples

```bash
# Top 15 aspects
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_aspects.py '{"asin":"B0D14N2QZF","top_n":15}'

# Schema
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_aspects.py --schema
```

## Output Shape

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

Polarity rule: `positive` if pos/(pos+neg) ≥ 0.65, `negative` if neg ratio ≥ 0.65, else `mixed`.

## Notes
- Read-only.
