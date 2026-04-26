---
name: query_rankings
description: "Return top-N best-selling Amazon products in a category for a specific date, ordered by rank (BSR). Use when user asks about top products, best sellers, current rankings, or what's hot in a category (gaming_keyboard | true_wireless_earbuds | portable_charger). Returns title, brand, price, stars, review count, sponsored flag. NOT for: brand momentum (use query_bms), or sentiment (use query_sentiment)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🏆",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_rankings — Top-N Category Rankings

Returns the top-N products in a category for a given date, ordered by BSR rank. The raw top-50 table other signals derive from.

## When to Use

✅ **USE this skill when:**
- "Top 10 portable_charger today"
- "Best sellers gaming keyboard tuần này"
- "Current rankings for earbuds category"
- "What's #1 in keyboards?"

❌ **DON'T use this skill when:**
- User wants momentum (who's gaining) → `query_bms`
- User wants sentiment → `query_sentiment`
- User wants new entrants/exits → `query_entrant_exits`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_rankings.py '<json-args>'
```

### Arguments
| Field           | Type | Required | Default     |
|-----------------|------|----------|-------------|
| `category`      | str  | **yes**  | —           |
| `top_n`         | int  | no       | `20` (1–50) |
| `snapshot_date` | str  | no       | today (ISO) |

### Examples

```bash
# Top 10 portable chargers today
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_rankings.py '{"category":"portable_charger","top_n":10}'

# Top 20 keyboards on a specific date
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_rankings.py '{"category":"gaming_keyboard","snapshot_date":"2026-04-25"}'
```

## Output Shape

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

## Notes
- Source: `category_rankings` table
- Read-only.
