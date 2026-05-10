# Skill — `query_listing_content`

- **Group:** listing
- **Source:** `asins` + latest row from `daily_snapshots`
- **Script:** `openclaw/skills/listing/query_listing_content.py`

## Purpose
Return the static listing content for one ASIN (title, description,
bullet_count, image_url, stars, reviews_count) from the latest available
snapshot. Use before recommending listing edits so recommendations are
grounded in real data.

> **Note:** individual bullet text is **not** stored — only `bullet_count`.
> Flag thin listings (< 5 bullets) but do not quote or invent specific bullets.

## Inputs
| Field  | Type  | Required | Default |
| ------ | ----- | -------- | ------- |
| `asin` | `str` | **yes**  | —       |

## Output shape
```json
{
  "asin":          "B0D14N2QZF",
  "found":         true,
  "brand":         "AULA",
  "category":      "gaming_keyboard",
  "title":         "AULA F75 Pro Gasket Mechanical Keyboard …",
  "title_words":   18,
  "bullet_count":  6,
  "description":   "…",
  "has_aplus":     true,
  "image_url":     "https://m.media-amazon.com/images/I/…",
  "stars":         4.4,
  "reviews_count": 1234,
  "as_of":         "2026-05-07",
  "listing_flags": [],
  "note":          "bullet_count is a count only — …"
}
```

If no snapshot exists for the ASIN, returns `{"asin": …, "found": false, "note": "…"}`.

## Listing health flags
Mirror the LQS thresholds in `scripts/analyze_lqs.py`:

- `title too short (<words> words, target ≥10)`
- `thin bullets (<n> bullets, target ≥5)`
- `no description stored`
- `no A+ content detected`

## CLI
```bash
python openclaw/skills/listing/query_listing_content.py '{"asin":"B0D14N2QZF"}'
```

## Used by
- `momentum_strategist` (primary — grounds listing-rewrite recommendations in real titles/bullet counts; prevents hallucinated bullet text)
