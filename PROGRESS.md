# PROGRESS.md — Market Tracker

> Live status log. Update after every completed task or logic change.
> Companion to `CLAUDE.md` (architecture) and `openclaw/AGENTS.md` (rules).

---

## Timeline

| Item              | Date       |
| ----------------- | ---------- |
| Today             | 2026-04-24 |
| Thesis deadline   | 2026-05-02 |
| Days remaining    | **8**      |

---

## Phase tracker

| Phase                                     | Status     | Notes                                                   |
| ----------------------------------------- | ---------- | ------------------------------------------------------- |
| 1. Data pipeline (Apify → Supabase)       | ✅ done    | 15 tables, 4 migrations, 30 watchlist ASINs; GitHub Actions daily ingest running successfully |
| 2. ML analytics (BMS, sentiment, LQS, …)  | ✅ done    | 9 scripts in `scripts/`, outputs in Supabase + `data/`. RoBERTa sentiment wired via `scripts/analyze_sentiment.py` |
| 3. Streamlit dashboard                    | ✅ done    | 6 pages under `dashboard/`                              |
| 4. OpenClaw workspace scaffold            | ✅ done    | `manifest.yaml`, `SOUL.md`, `AGENTS.md` in place        |
| 5. Skills — 13 Python + 13 SKILL.md       | ✅ done    | see Skills audit below                                  |
| 6. Agents — 3 SOUL.md                     | ✅ done    | see Souls audit below                                   |
| 7. Gateway onboarding (`openclaw onboard`)| ✅ done    | OpenClaw 2026.4.20 installed in VMware Workstation; Telegram pairing approved; `/status` + `/start` verified |
| 8. First live Telegram brief              | 🟡 partial | Telegram bot responds to basic commands; end-to-end market-intelligence brief content still needs validation |
| 9. RoBERTa Colab integration              | 🟡 external | Notebook exists in Colab as an experiment. Repo already runs RoBERTa via `analyze_sentiment.py`; Colab code is separate and not currently ported |
|10. Thesis write-up                        | ⏳ pending | LaTeX skeleton under `thesis/`                          |

---

## Skills audit (13/13)

| # | Skill id                | Group     | `.py` | `.md` | Schema dict | CLI tested |
|---|-------------------------|-----------|:-----:|:-----:|:-----------:|:----------:|
| 1 | `query_sentiment`       | sentiment |  ✅   |  ✅   |     ✅      |     ⏳     |
| 2 | `query_reviews`         | sentiment |  ✅   |  ✅   |     ✅      |     ⏳     |
| 3 | `query_aspects`         | sentiment |  ✅   |  ✅   |     ✅      |     ⏳     |
| 4 | `query_bms`             | market    |  ✅   |  ✅   |     ✅      |     ⏳     |
| 5 | `query_rankings`        | market    |  ✅   |  ✅   |     ✅      |     ⏳     |
| 6 | `query_entrant_exits`   | market    |  ✅   |  ✅   |     ✅      |     ⏳     |
| 7 | `query_sponsored_share` | market    |  ✅   |  ✅   |     ✅      |     ⏳     |
| 8 | `query_price_tiers`     | market    |  ✅   |  ✅   |     ✅      |     ⏳     |
| 9 | `query_price_forecast`  | market    |  ✅   |  ✅   |     ✅      |     ⏳     |
|10 | `query_snapshots`       | listing   |  ✅   |  ✅   |     ✅      |     ⏳     |
|11 | `query_image_changes`   | listing   |  ✅   |  ✅   |     ✅      |     ⏳     |
|12 | `query_lqs`             | listing   |  ✅   |  ✅   |     ✅      |     ⏳     |
|13 | `query_alerts`          | alerts    |  ✅   |  ✅   |     ✅      |     ⏳     |

Test command template: `python openclaw/skills/<group>/<skill>.py '<json-args>'`

---

## Souls audit (3/3)

| Agent                   | `SOUL.md` | Skills wired                                                                                       | Default |
|-------------------------|:---------:|----------------------------------------------------------------------------------------------------|:-------:|
| `sentiment_detective`   |    ✅     | query_sentiment, query_reviews, query_aspects, query_snapshots                                     |         |
| `competitor_spy`        |    ✅     | query_bms, query_rankings, query_entrant_exits, query_sponsored_share, query_price_tiers, query_image_changes |  |
| `momentum_strategist`   |    ✅     | query_alerts, query_bms, query_price_forecast, query_lqs, query_sentiment                          |   ⭐    |

All three have `SOUL.md` with: Rules of engagement · Forbidden · Shape of a good output · Skills you may call.

Workspace-level defaults: `openclaw/SOUL.md` + `openclaw/AGENTS.md`.

---

## Deployment / Runtime status

| Component                        | Status      | Evidence / Notes                                                           |
|----------------------------------|:-----------:|-----------------------------------------------------------------------------|
| GitHub repo                      | ✅ done     | Pushed to https://github.com/nglinh185/market-tracker                       |
| GitHub Actions — Daily Ingest    | ✅ done     | Workflow `Daily Amazon Data Ingest` has successful recent runs              |
| Apify ingest                     | ✅ done     | Daily workflow collects Amazon data from Apify                              |
| OpenClaw runtime                 | ✅ done     | Installed in VMware Workstation, version 2026.4.20, runtime = direct        |
| OpenClaw model                   | ✅ done     | `openai/gpt-4o-mini` via `OPENAI_API_KEY`                                   |
| Telegram pairing                 | ✅ done     | Pairing approved; `/status` returns Gateway status                          |
| Telegram chat                    | ✅ done     | `/start` returns bot greeting                                               |
| Market brief over Telegram       | 🟡 partial  | Bot connected; actual market-intelligence brief content not yet validated   |
| RoBERTa sentiment (repo)         | ✅ done     | `scripts/analyze_sentiment.py` uses `cardiffnlp/twitter-roberta-base-sentiment-latest` |
| RoBERTa Colab notebook           | 🟡 external | Separate experimental notebook; not currently ported into repo pipeline     |

---

## Blockers / open questions

1. **Skill invocation shape** — current skills use `CLI + JSON arg`. Still unverified against Gateway's actual Skill protocol (even though Telegram chat works, Skill routing has not been exercised end-to-end). 5-min rewrite across all 13 files if wrong.
2. **Market brief content validation** — Telegram bot answers basic commands, but agent replies containing real market intelligence (BMS rankings, alerts, entrant/exit, etc.) have not been verified end-to-end.
3. **RoBERTa Colab ↔ repo alignment** — repo already runs RoBERTa offline; the Colab notebook duplicates this experiment. Decide: archive the Colab, or port any Colab-only improvements (e.g. aspect-level fine-tuning) back into `scripts/analyze_sentiment.py`.
4. **Per-agent SOUL.md placement** — docs confirm workspace `SOUL.md`; per-agent placement under `agents/<name>/SOUL.md` is still an inference.
5. **`migrations/005_openclaw_memory.sql`** — Gateway ships its own memory store, making this migration likely dead. Owner decision pending.

---

## Implicit state sync — honest note

CLAUDE.md asks for auto-updates to this file on every task. Markdown cannot enforce that — it's a reminder, not a mechanism. To make it real, add a `Stop` hook in `.claude/settings.json` that appends a status line here. Ask Claude to wire it via the `update-config` skill when ready.

---

## Changelog

- **2026-04-24** — Deployment + runtime milestone:
  - Code pushed to GitHub: https://github.com/nglinh185/market-tracker.
  - GitHub Actions `Daily Amazon Data Ingest` verified running successfully (daily Apify pull).
  - OpenClaw 2026.4.20 installed on VMware Workstation; runtime = direct, model = `openai/gpt-4o-mini` (via `OPENAI_API_KEY`).
  - Telegram pairing approved; `/status` and `/start` verified end-to-end with the bot.
  - Market-intelligence brief content over Telegram flagged as 🟡 partial — Skill routing not yet validated through an actual agent reply.
  - RoBERTa Colab notebook noted as external experiment; repo still uses `scripts/analyze_sentiment.py` as the canonical sentiment path.
- **2026-04-24** — Hardening pass:
  - Added `.env.example` and `README.md` (setup + run commands).
  - `config.py`: `ACTOR_CATEGORY` / `ACTOR_REVIEWS` read from env with defaults; filled in review actor ID (`gFtgG31RZJYlphznm`); added `DEBUG` flag + `require_env()` helper.
  - `scripts/ingest_reviews.py`: uses `config.ACTOR_REVIEWS` (was hardcoded); fixed aspects upsert bug that would blank other columns.
  - `scripts/ingest_category.py` / `ingest_watchlist.py`: fail-fast env check via `require_env`.
  - `lib/parsers/product.py`: `_parse_stock` now returns `None` when actor omits stock field (was silently defaulting `True`).
  - `scripts/run_analytics.py`: inserted `analyze_sentiment.py` before `analyze_bms` + `analyze_lqs` so BMS/LQS no longer get null sentiment on non-Monday runs.
  - Legacy root `collector_category.py` / `collector_product.py` converted to thin forwarders (previous versions used stale env vars `ACTOR_ID` / `CATEGORY_URL`).
- **2026-04-20** — Workspace scaffolded (manifest + SOUL + AGENTS). 13 skills + 13 SKILL.md sidecars written. 3 agent SOULs written. CLAUDE.md + PROGRESS.md initialized.
