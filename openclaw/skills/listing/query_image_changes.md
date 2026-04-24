# Skill — `query_image_changes`

- **Group:** listing
- **Source:** `image_change_events`
- **Script:** `openclaw/skills/listing/query_image_changes.py`

## Purpose
Return perceptual-hash (pHash) image-change events detected by `scripts/analyze_changes.py`. Hamming distance threshold defaults to 10 (see `config.PHASH_THRESHOLD`); higher distance = more significant visual redesign.

## Inputs
| Field       | Type          | Required | Default     |
| ----------- | ------------- | -------- | ----------- |
| `asin_list` | `list[str]`   | no       | all ASINs   |
| `days`      | `int`         | no       | `7` (1–30)  |

## Output shape
```json
[
  {
    "snapshot_date":  "2026-04-19",
    "asin":           "B0D14N2QZF",
    "hash_before":    "d4e3...",
    "hash_after":     "d4f7...",
    "hash_distance":  18,
    "change_flag":    true
  }
]
```

## CLI
```bash
python openclaw/skills/listing/query_image_changes.py '{"asin_list":["B0D14N2QZF"],"days":30}'
```

## Used by
- `competitor_spy` (primary)
