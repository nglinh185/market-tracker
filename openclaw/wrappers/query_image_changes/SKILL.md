---
name: query_image_changes
description: "Return Amazon listing main-image change events detected via perceptual hash (pHash). Use when user asks about visual redesign, image swap, listing creative changes, or competitors changing their hero image. NOT for: title/bullet text changes, or sentiment (use query_sentiment)."
metadata:
  {
    "openclaw":
      {
        "emoji": "🖼️",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_image_changes — pHash Image Diff Events

Returns image-change events from `imagehash` pHash diffs. Hamming distance threshold default 10; higher = more significant visual redesign.

## When to Use

✅ **USE this skill when:**
- "Did B0D14N2QZF change its main image?"
- "ASIN nào vừa đổi ảnh?"
- "Visual redesign events last week"
- "Competitors swapping hero images"

❌ **DON'T use this skill when:**
- User wants sentiment → `query_sentiment`
- User wants price → `query_snapshots`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_image_changes.py '<json-args>'
```

### Arguments
| Field       | Type      | Required | Default    |
|-------------|-----------|----------|------------|
| `asin_list` | list[str] | no       | all ASINs  |
| `days`      | int       | no       | `7` (1–30) |

### Examples

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_image_changes.py '{"asin_list":["B0D14N2QZF"],"days":30}'
```

## Output Shape

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

## Notes
- Source: `image_change_events` table
- Threshold: `config.PHASH_THRESHOLD` (default 10)
- Read-only.
