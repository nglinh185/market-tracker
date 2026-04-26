---
name: query_reviews
description: "Return raw Amazon review records for a specific ASIN with optional sentiment filter (positive/negative/neutral). Use when user wants to see actual customer review quotes, evidence behind sentiment claims, or what specific reviews say. NOT for: aggregated sentiment scores (use query_sentiment), or aspect breakdown (use query_aspects)."
metadata:
  {
    "openclaw":
      {
        "emoji": "📝",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_reviews — Raw Review Records

Returns up to 25 raw reviews for an ASIN, optionally filtered by sentiment polarity. Text is truncated to 600 chars per record.

## When to Use

✅ **USE this skill when:**
- "Show me 5 negative reviews for B0D14N2QZF"
- "Cho t đọc review tiêu cực của ASIN này"
- "What do unhappy customers say?"
- "Quote customer evidence for sentiment drop"

❌ **DON'T use this skill when:**
- User wants aggregate scores → `query_sentiment`
- User wants aspect breakdown → `query_aspects`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_reviews.py '<json-args>'
```

### Arguments
| Field       | Type | Required | Default | Notes                                              |
|-------------|------|----------|---------|----------------------------------------------------|
| `asin`      | str  | **yes**  | —       |                                                    |
| `sentiment` | str  | no       | `any`   | `positive` \| `neutral` \| `negative` \| `any`     |
| `limit`     | int  | no       | `5`     | 1–25                                               |

### Examples

```bash
# 5 negative reviews
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_reviews.py '{"asin":"B0D14N2QZF","sentiment":"negative","limit":5}'

# Schema
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/sentiment/query_reviews.py --schema
```

## Output Shape

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

## Notes
- Source: `reviews_raw` table
- Read-only.
