---
name: query_listing_content
description: "Return static listing content for one ASIN: title, description, bullet_count, image_url, stars, reviews_count, and listing health flags. Use BEFORE recommending listing edits — grounding recommendations in real data prevents hallucination. Individual bullet text is NOT available (not stored); flag thin listings by bullet_count only."
metadata:
  {
    "openclaw":
      {
        "emoji": "📋",
        "requires": { "bins": ["python3"] }
      }
  }
---

# query_listing_content — Static Listing Content for an ASIN

Returns the latest stored listing content and auto-computed health flags.

## When to Use

✅ **USE this skill when:**
- About to recommend listing improvements ("improve title", "add bullets")
- User asks "what does this listing look like?"
- Strategist needs to ground an action in real listing data before sending it

❌ **DON'T use this skill when:**
- User wants price/BSR history → `query_snapshots`
- User wants sentiment → `query_sentiment`
- User wants LQS score → `query_lqs`

## Command

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_listing_content.py '<json-args>'
```

### Arguments
| Field  | Type | Required |
|--------|------|----------|
| `asin` | str  | **yes**  |

### Example

```bash
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/listing/query_listing_content.py '{"asin":"B0D14N2QZF"}'
```

## Output Shape

```json
{
  "asin":          "B0D14N2QZF",
  "found":         true,
  "brand":         "Anker",
  "category":      "portable_charger",
  "title":         "Anker 313 Power Bank...",
  "title_words":   12,
  "bullet_count":  5,
  "description":   "Compact and lightweight...",
  "has_aplus":     true,
  "image_url":     "https://...",
  "stars":         4.6,
  "reviews_count": 2310,
  "as_of":         "2026-05-06",
  "listing_flags": [],
  "note":          "bullet_count is a count only..."
}
```

## ⚠️ Hard Rule

`bullet_count` is a **count only**. Individual bullet text is NOT stored in the database.

- ✅ Say: "Only `3` bullets — add at least 2 more focusing on battery capacity and charging speed."
- ❌ Never say: "Rewrite bullet #3 — currently says X." (You do not have this data.)
