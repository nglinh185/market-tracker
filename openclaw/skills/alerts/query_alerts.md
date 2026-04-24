# Skill — `query_alerts`

- **Group:** alerts
- **Source:** `alerts`
- **Script:** `openclaw/skills/alerts/query_alerts.py`

## Purpose
Return rule-based alerts from `scripts/analyze_alerts.py`. Alert types and default thresholds:

| Type          | Trigger                                   | Severity                   |
| ------------- | ----------------------------------------- | -------------------------- |
| `price_drop`  | ≥15% drop in 1 day                        | high (≥30%) / medium       |
| `stockout`    | `in_stock` true → false                   | medium                     |
| `bsr_drop`    | BSR worsened by ≥500 ranks                | medium                     |
| `image_change`| Any row in `image_change_events`          | medium                     |
| `new_entrant` | Row in `entrant_exit_events` (entrant)    | high if top10 else medium  |
| `exit`        | Row in `entrant_exit_events` (exit)       | medium                     |

## Inputs
| Field      | Type   | Required | Default     |
| ---------- | ------ | -------- | ----------- |
| `category` | `str`  | no       | all         |
| `severity` | `str`  | no       | `any`       |
| `days`     | `int`  | no       | `1` (1–14)  |
| `limit`    | `int`  | no       | `30`        |

## Output shape
```json
[
  {
    "snapshot_date":  "2026-04-21",
    "asin":           "B07QQB9VCV",
    "browse_node":    "gaming_keyboard",
    "alert_type":     "stockout",
    "severity":       "medium",
    "message":        "Logitech G PRO went out of stock",
    "metadata_json":  { "prev_snapshot": "2026-04-20" }
  }
]
```

## CLI
```bash
python openclaw/skills/alerts/query_alerts.py '{"category":"gaming_keyboard","severity":"high","days":3}'
```

## Used by
- `momentum_strategist` (primary — always called first)
