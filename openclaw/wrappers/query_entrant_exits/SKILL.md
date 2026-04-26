---
name: query_entrant_exits
description: "Return Amazon top-50 entry/exit events for a category over the last N days — which ASINs newly entered or dropped out of the top 50, with high-impact `is_top10` flag. Use when user asks about new competitors, products that disappeared, market churn, or who's emerging/falling. NOT for: ranking changes within top 50 (use query_rankings), or brand momentum (use query_bms)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🚪",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_entrant_exits — Top-50 Churn Events

Returns entry/exit events for a category over the last N days. Derived from day-to-day rank diffs. `is_top10` flags high-impact moves (entry into / exit from top 10).

## When to Use

✅ **USE this skill when:**
- "New entrants in gaming keyboard last week"
- "Sản phẩm nào mới nhảy vào top 50 earbuds?"
- "Who exited the top rankings?"
- "Market churn analysis"

❌ **DON'T use this skill when:**
- User wants current rankings → `query_rankings`
- User wants brand momentum → `query_bms`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_entrant_exits.py '<json-args>'
```

### Arguments
| Field      | Type | Required | Default     |
|------------|------|----------|-------------|
| `category` | str  | **yes**  | —           |
| `days`     | int  | no       | `7` (1–30)  |

### Examples

```bash
# Last 14 days of churn in gaming keyboards
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_entrant_exits.py '{"category":"gaming_keyboard","days":14}'
```

## Output Shape

```json
[
  {
    "snapshot_date":   "2026-04-19",
    "asin":            "B0C9ZJHQHM",
    "event_type":      "entrant",
    "rank_today":      9,
    "rank_yesterday":  null,
    "is_top10":        true
  }
]
```

## Notes
- Source: `entrant_exit_events` table
- Read-only.
