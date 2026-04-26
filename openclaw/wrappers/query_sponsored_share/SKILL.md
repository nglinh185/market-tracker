---
name: query_sponsored_share
description: "Return Amazon sponsored share-of-voice leaders for a category keyword — which brands are buying the most ad slots, with overlap into organic top results. Use when user asks about advertising competition, who's spending on ads, sponsored slot share, or paid vs organic dominance. NOT for: organic rankings (use query_rankings), or brand momentum (use query_bms)."
metadata:
  {
    "openclaw":
      {
        "emoji": "💰",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_sponsored_share — Sponsored Ad Share-of-Voice

Returns sponsored share-of-voice leaders for a category keyword over the last N days.

## When to Use

✅ **USE this skill when:**
- "Who's buying the most sponsored slots in earbuds?"
- "Brand nào đang đẩy mạnh ads gaming keyboard?"
- "Top advertisers in this category"
- "Paid search dominance"

❌ **DON'T use this skill when:**
- User wants organic ranking → `query_rankings`
- User wants brand momentum → `query_bms`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_sponsored_share.py '<json-args>'
```

### Arguments
| Field      | Type | Required | Default     |
|------------|------|----------|-------------|
| `category` | str  | **yes**  | —           |
| `days`     | int  | no       | `7` (1–30)  |
| `top_n`    | int  | no       | `10`        |

### Examples

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_sponsored_share.py '{"category":"true_wireless_earbuds","days":7}'
```

## Output Shape

```json
[
  {
    "snapshot_date":         "2026-04-20",
    "keyword":               "gaming keyboard",
    "brand":                 "Redragon",
    "sponsored_slot_count":  7,
    "share_of_voice":        0.22,
    "organic_overlap_count": 3
  }
]
```

## Notes
- Source: `sponsored_ad_share_daily` table
- Read-only.
