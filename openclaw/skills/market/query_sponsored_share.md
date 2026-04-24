# Skill — `query_sponsored_share`

- **Group:** market
- **Source:** `sponsored_ad_share_daily`
- **Script:** `openclaw/skills/market/query_sponsored_share.py`

## Purpose
Return sponsored share-of-voice leaders for a category keyword over the last *N* days. Matches against `keyword` via ILIKE on the underscore-to-space form of the category id.

## Inputs
| Field      | Type   | Required | Default     |
| ---------- | ------ | -------- | ----------- |
| `category` | `str`  | **yes**  | —           |
| `days`     | `int`  | no       | `7` (1–30)  |
| `top_n`    | `int`  | no       | `10`        |

## Output shape
```json
[
  {
    "snapshot_date":          "2026-04-20",
    "keyword":                "gaming keyboard",
    "brand":                  "Redragon",
    "sponsored_slot_count":   7,
    "share_of_voice":         0.22,
    "organic_overlap_count":  3
  }
]
```

## CLI
```bash
python openclaw/skills/market/query_sponsored_share.py '{"category":"true_wireless_earbuds","days":7}'
```

## Used by
- `competitor_spy`
