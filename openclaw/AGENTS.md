# AGENTS — Workspace Rules

Instructions for any agent (OpenClaw or otherwise) operating inside this workspace.

## Project

Amazon Market Tracker. Thesis project. Tracks top-50 + watchlist of 30 ASINs across 3 categories: `gaming_keyboard`, `true_wireless_earbuds`, `portable_charger`.

Stack: Apify → Supabase (Postgres) → scikit-learn + RoBERTa + Prophet → Streamlit dashboard. Data ingestion is daily; ML runs nightly.

## Where things live

| Path                                       | Purpose                                     |
| ------------------------------------------ | ------------------------------------------- |
| `lib/db.py`                                | Supabase client. Use for every DB call.     |
| `lib/apify.py`                             | Apify orchestration — don't touch.          |
| `lib/parsers/`                             | JSON→row parsers — don't touch.             |
| `scripts/analyze_*.py`                     | Nightly ML analytics — don't touch.         |
| `openclaw/skills/**/*.py`                  | Standalone Skills invocable by the Gateway. |
| `openclaw/agents/*/SOUL.md`                | Per-agent personality.                      |
| `openclaw/SOUL.md`                         | Workspace-level default voice.              |
| `openclaw/manifest.yaml`                   | Skill + agent registry.                     |
| `dashboard/`                               | Streamlit UI. Independent of OpenClaw.      |

## Skill invocation contract

Every Skill under `openclaw/skills/**` exposes:
1. `SKILL` — module-level dict with `name`, `description`, `input_schema`.
2. `run(**kwargs) -> dict | list` — importable callable.
3. CLI: `python skills/x/y.py '{"arg":"val"}'` prints JSON to stdout.
4. `python skills/x/y.py --schema` prints the input schema.

A Skill must never print to stdout except its final JSON payload. Errors go to stderr.

## Database contract

- All reads/writes go through `lib/db.supabase` — never construct a new Supabase client.
- Environment: `SUPABASE_URL`, `SUPABASE_KEY` live in `.env` at repo root.
- Time column is always `snapshot_date` (ISO string). Default to `date.today().isoformat()`.

## Agent routing

Three named agents (see `openclaw/agents/*/SOUL.md`):

- **sentiment_detective** — WHY review sentiment changes. Uses: `query_sentiment`, `query_reviews`, `query_aspects`, `query_snapshots`.
- **competitor_spy** — WHAT competitors are doing. Uses: `query_bms`, `query_rankings`, `query_entrant_exits`, `query_sponsored_share`, `query_price_tiers`, `query_image_changes`.
- **momentum_strategist** — WHAT to do next week. Uses: `query_alerts`, `query_bms`, `query_price_forecast`, `query_lqs`, `query_sentiment`.

Route by intent:
- Keywords "sentiment / review / complaint / praise / aspect" → **sentiment_detective**
- Keywords "competitor / rival / entrant / sponsored / ad / share" → **competitor_spy**
- Everything else, and any `/brief` command → **momentum_strategist**

## Output rules

- Every claim cites an ASIN, a number, or both.
- Never invent ASINs, brands, or review quotes. If a Skill returns no data, say so.
- For Telegram output: under 3800 chars per message. Escape MarkdownV2 reserved chars: `_ * [ ] ( ) ~ \` > # + - = | { } . !`

## Safety

- Do not modify `scripts/analyze_*.py` without explicit user approval — they feed the ML pipeline.
- Do not write to Supabase from a Skill. Skills are read-only.
- If asked to run a destructive DB operation, refuse and explain.
