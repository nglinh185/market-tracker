# Skill — `query_entrant_exits`

- **Group:** market
- **Source:** `entrant_exit_events`
- **Script:** `openclaw/skills/market/query_entrant_exits.py`

## Purpose
Return top-50 entry/exit events for a category over the last *N* days. `is_top10` flag marks high-impact moves. Derived from day-to-day rank diffs in `scripts/analyze_entrant_exit.py`.

## Inputs
| Field      | Type   | Required | Default     |
| ---------- | ------ | -------- | ----------- |
| `category` | `str`  | **yes**  | —           |
| `days`     | `int`  | no       | `7` (1–30)  |

## Output shape
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

## CLI
```bash
python openclaw/skills/market/query_entrant_exits.py '{"category":"gaming_keyboard","days":14}'
```

## Used by
- `competitor_spy` (primary)
