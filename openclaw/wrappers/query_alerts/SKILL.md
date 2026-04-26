---
name: query_alerts
description: "Return rule-based market alerts (price drop, stockout, BSR drop, image change, new entrant, exit) with severity (high/medium/low) for Amazon ASINs. Use when user asks about urgent events, what to watch, alerts today, market shocks, important changes, or 'what should I know right now'. ALWAYS call this first for daily briefs."
metadata:
  {
    "openclaw":
      {
        "emoji": "🚨",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_alerts — Rule-Based Market Alerts

Returns alerts from `scripts/analyze_alerts.py`. ALWAYS call first when user asks for daily brief.

| Type           | Trigger                                  | Severity                  |
|----------------|------------------------------------------|---------------------------|
| `price_drop`   | ≥15% drop in 1 day                       | high (≥30%) / medium      |
| `stockout`     | `in_stock` true → false                  | medium                    |
| `bsr_drop`     | BSR worsened by ≥500 ranks               | medium                    |
| `image_change` | Any row in `image_change_events`         | medium                    |
| `new_entrant`  | Row in `entrant_exit_events` (entrant)   | high if top10 else medium |
| `exit`         | Row in `entrant_exit_events` (exit)      | medium                    |

## When to Use

✅ **USE this skill when:**
- "Alerts today"
- "Có gì đáng chú ý hôm nay không?"
- "Daily brief / morning brief"
- "Price drops, stockouts, new entrants"
- "What should I know about the market right now?"

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/alerts/query_alerts.py '<json-args>'
```

### Arguments
| Field      | Type | Required | Default     |
|------------|------|----------|-------------|
| `category` | str  | no       | all         |
| `severity` | str  | no       | `any`       |
| `days`     | int  | no       | `1` (1–14)  |
| `limit`    | int  | no       | `30`        |

### Examples

```bash
# High-severity alerts in keyboards last 3 days
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/alerts/query_alerts.py '{"category":"gaming_keyboard","severity":"high","days":3}'

# All alerts today
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/alerts/query_alerts.py '{}'
```

## Output Shape

```json
[
  {
    "snapshot_date":  "2026-04-26",
    "asin":           "B07QQB9VCV",
    "browse_node":    "gaming_keyboard",
    "alert_type":     "stockout",
    "severity":       "medium",
    "message":        "Logitech G PRO went out of stock",
    "metadata_json":  { "prev_snapshot": "2026-04-25" }
  }
]
```

## Notes
- Source: `alerts` table
- Read-only.
