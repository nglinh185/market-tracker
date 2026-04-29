# PROGRESS.md — Market Tracker

> Live status log. Update after every completed task or logic change.
> Companion to `CLAUDE.md` (architecture) and `openclaw/AGENTS.md` (rules).

---

## Timeline

| Item              | Date       |
| ----------------- | ---------- |
| Today             | 2026-04-29 |
| Thesis deadline   | 2026-05-02 |
| Days remaining    | **3**      |

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
| 7. Gateway runtime + Telegram pairing     | ✅ done    | OpenClaw 2026.4.20 on VMware; Telegram channel connected; `/status` + `/start` verified |
| 8. Project skill registration (Gateway)   | ✅ done    | 13/13 skills loaded as `openclaw-extra` via `skills.load.extraDirs = openclaw/wrappers/`. Each wrapper has YAML-frontmatter SKILL.md mapping to the Python CLI under venv. |
| 9. Multi-agent deployment (3 bots)        | ✅ done    | 3 specialist agents: `competitor_spy` (`@babyspyyy_bot`), `sentiment_detective` (`@babydetective_bot`), `momentum_strategist` (`@babystrategist_bot`). Each agent has SOUL/IDENTITY/AGENTS/USER markdown. 1:1 channel binding. End-to-end verified with real Supabase data. |
|10. Cron scheduling                        | ✅ done    | 3 cron jobs in `Asia/Ho_Chi_Minh`: daily brief 8 AM (Strategist), weekly competitor 9 AM Mon (Spy), weekly sentiment 9 AM Wed (Detective). Test run delivered 3-list brief to Telegram. |
|11. RoBERTa Colab integration              | 🟡 external | Notebook to be archived under `notebooks/`. Repo runs RoBERTa via `analyze_sentiment.py`; Colab code stays as a separate experiment artifact. |
|12. Dashboard polish                       | ⏳ pending | 6 pages exist; theme/CSS/Plotly polish for thesis defense impact (Day 2-3 plan). |
|13. Output polish (Telegram bots)          | ✅ done    | SOUL.md + AGENTS.md hardened for Telegram production: no markdown tables, line caps (sentiment 25 / spy 25 / strategist 30), backtick-wrapped numbers/ASINs, mandatory next-step closer (no "Let me know…"), spell-guard `Concerns` (not `Confidences`), grouped alerts by priority. 2026-04-28. |
|14. Thesis write-up                        | ⏳ pending | LaTeX skeleton under `thesis/`. Architecture chapter ready (3-tier multi-agent + cron). |

---

## Skills audit (13/13)

All skills have a Python CLI (`scripts/skill.py`), a sidecar `.md` doc under `openclaw/skills/<group>/`, and an OpenClaw AgentSkill wrapper at `openclaw/wrappers/<skill>/SKILL.md` (YAML-frontmatter format) registered via `skills.load.extraDirs`.

| # | Skill id                | Group     | `.py` | sidecar `.md` | wrapper `SKILL.md` | CLI tested |
|---|-------------------------|-----------|:-----:|:-------------:|:------------------:|:----------:|
| 1 | `query_sentiment`       | sentiment |  ✅   |      ✅       |        ✅          |     ✅     |
| 2 | `query_reviews`         | sentiment |  ✅   |      ✅       |        ✅          |     ✅     |
| 3 | `query_aspects`         | sentiment |  ✅   |      ✅       |        ✅          |     ✅ (bug fix 2026-04-27 — see Changelog) |
| 4 | `query_bms`             | market    |  ✅   |      ✅       |        ✅          |     ✅     |
| 5 | `query_rankings`        | market    |  ✅   |      ✅       |        ✅          |     ✅     |
| 6 | `query_entrant_exits`   | market    |  ✅   |      ✅       |        ✅          |     ✅     |
| 7 | `query_sponsored_share` | market    |  ✅   |      ✅       |        ✅          |     ✅     |
| 8 | `query_price_tiers`     | market    |  ✅   |      ✅       |        ✅          |     ✅     |
| 9 | `query_price_forecast`  | market    |  ✅   |      ✅       |        ✅          |     ✅     |
|10 | `query_snapshots`       | listing   |  ✅   |      ✅       |        ✅          |     ✅     |
|11 | `query_image_changes`   | listing   |  ✅   |      ✅       |        ✅          |     ✅     |
|12 | `query_lqs`             | listing   |  ✅   |      ✅       |        ✅          |     ✅     |
|13 | `query_alerts`          | alerts    |  ✅   |      ✅       |        ✅          |     ✅     |

Test command template (in VM): `/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/<group>/<skill>.py '<json-args>'`

---

## Souls audit (3/3)

Each agent's workspace lives at `openclaw/agents/<name>/` with **four files**: `SOUL.md` (voice + rules), `IDENTITY.md` (display name + emoji + vibe), `AGENTS.md` (skill list with JSON arg examples + trigger keywords + forbidden actions), `USER.md` (DS student context, EN/VI preference, watchlist ASINs).

| Agent                   | All 4 MD files | Skills wired                                                                                                  | Telegram bot                |
|-------------------------|:--------------:|---------------------------------------------------------------------------------------------------------------|------------------------------|
| `sentiment_detective`   |       ✅       | query_sentiment, query_reviews, query_aspects, query_snapshots                                                | 🔍 `@babydetective_bot`      |
| `competitor_spy`        |       ✅       | query_bms, query_rankings, query_entrant_exits, query_sponsored_share, query_price_tiers, query_image_changes | 🕵️ `@babyspyyy_bot`          |
| `momentum_strategist`   |       ✅       | query_alerts, query_bms, query_price_forecast, query_lqs, query_sentiment                                     | 🎯 `@babystrategist_bot`     |

All three are registered as OpenClaw agents (`agents add`) with explicit `agents bind` to a dedicated Telegram account. End-to-end tested with real Supabase data on 2026-04-27.

Workspace-level defaults at `openclaw/SOUL.md` + `openclaw/AGENTS.md` exist as a fallback but are not used for the deployed agents (each specialist has its own workspace under `openclaw/agents/<name>/`).

---

## Deployment / Runtime status

| Component                        | Status      | Evidence / Notes                                                           |
|----------------------------------|:-----------:|-----------------------------------------------------------------------------|
| GitHub repo                      | ✅ done     | Pushed to https://github.com/nglinh185/market-tracker                       |
| GitHub Actions — Daily Ingest    | ✅ done     | Workflow `Daily Amazon Data Ingest` runs daily at 13:00 ICT                 |
| Apify ingest                     | ✅ done     | junglee/Amazon-crawler + web_wanderer/amazon-reviews-extractor              |
| OpenClaw runtime                 | ✅ done     | Installed in VMware Ubuntu 24.04, version 2026.4.20, runtime = direct       |
| OpenClaw model (per agent)       | ✅ done     | `openai/gpt-4o-mini` via `OPENAI_API_KEY` (in OpenClaw config, not repo)    |
| Telegram channels (×3)           | ✅ done     | 3 bots: `@babyspyyy_bot` (default→Spy), `@babydetective_bot`, `@babystrategist_bot`. All paired. |
| Project skills registration      | ✅ done     | 13/13 wrappers under `openclaw/wrappers/`, registered via `skills.load.extraDirs`. Source = `openclaw-extra`. |
| Multi-agent deployment           | ✅ done     | 3 agents added (`agents add`), each bound 1:1 to its Telegram account (`agents bind`). |
| End-to-end Telegram brief        | ✅ done     | Verified 2026-04-27: each bot returns real Supabase data on natural-language queries. Cron `daily-brief-strategist` test run delivered full 3-list brief. |
| Cron schedules (×3)              | ✅ done     | daily 8 AM (Strategist), Mon 9 AM (Spy), Wed 9 AM (Detective). All `Asia/Ho_Chi_Minh`. |
| RoBERTa sentiment (repo)         | ✅ done     | `scripts/analyze_sentiment.py` uses `cardiffnlp/twitter-roberta-base-sentiment-latest` |
| RoBERTa Colab notebook           | 🟡 external | To be archived under `notebooks/` for thesis appendix                       |
| Dashboard polish                 | ⏳ pending  | 6 Streamlit pages exist; theme + Plotly polish for thesis defense visual impact |
| Output polish (Telegram)         | ✅ done     | SOUL.md + AGENTS.md hardened (line caps, no tables, grouped alerts, banned closers, spell-guard). 2026-04-28. |

---

## Blockers / open questions

1. **Telegram polling network instability.** VM occasionally hits `Network request for 'getUpdates' failed!` — bots reconnect automatically but messages can lag 30–60s. Workaround: VMware NAT restart fixes it. Defense risk: low, but mention in limitations.
2. **Sentiment aggregation is cumulative, not daily-new.** `analyze_sentiment.py` recomputes `avg_sentiment_score` over every historical review each day; `review_sentiment_daily.review_count_new` is misleadingly named (it's the running total, not new reviews per day). BMS sentiment input therefore moves only when reviews are actually added (weekly). Disclose in the methodology chapter; not breaking.
3. **`9router-openai/cx/gpt-5.5` proxy was set up but currently unreachable** (`localhost:20128` not listening). Agents fall back to `openai/gpt-4o-mini` which works correctly. Document the failover behavior in thesis "Limitations" section.
4. **RoBERTa Colab archive** — file `notebooks/sentiment_roberta_experiment.ipynb` not yet committed. Pull from Colab and add before defense.
5. **Supabase key scoping (security).** Verified anon-key read exposure exists: the public web dashboard ships the anon key embedded in `web-dashboard/index.html` (`window.APP_CONFIG.SUPABASE_ANON_KEY`), so anyone visiting the deployed page can read whatever tables the anon role has SELECT on — including `reviews_raw` based on current schema/policies. Fixing the policies (RLS / column allowlists) requires the Supabase admin console, not code; this is a configuration follow-up, not a code bug. Action items: (a) tighten RLS on `reviews_raw`, `daily_snapshots`, `alerts`, `category_rankings`, `brand_momentum_daily`, `review_sentiment_daily`, `listing_quality_score_daily`, `price_forecast_daily` in Supabase; (b) confirm `SUPABASE_KEY` used by ingest scripts (CI, watchlist, sentiment) is service-role and is **never** copied into the Streamlit dashboard or the static `web-dashboard/`; (c) consider rotating the anon key once policies are tight, since the current key is committed to deploy artifacts.

---

## Next actions — Day 2 (2026-04-28)

1. **Output polish (Telegram bots)** — tighten SOUL.md / AGENTS.md so output uses Telegram MarkdownV2 (`*bold*`, `_italic_`), clearer section breaks, ASIN/numbers visually highlighted. ~2-3 hours.
2. **Dashboard polish** — Streamlit theme, st.metric cards, consistent Plotly color palette, header/breadcrumb, loading states across the 6 pages. ~6-10 hours (spans Day 2 PM + Day 3).

## Day 3-7

3. Thesis writeup — architecture chapter (3-tier multi-agent + cron), results chapter (sample briefs + screenshots).
4. Demo rehearsal — record a 2–3 min video demo of all 3 bots + dashboard pages.
5. Buffer for fix-bugs-as-they-arise.

---

## Implicit state sync — honest note

CLAUDE.md asks for auto-updates to this file on every task. Markdown cannot enforce that — it's a reminder, not a mechanism. To make it real, add a `Stop` hook in `.claude/settings.json` that appends a status line here. Ask Claude to wire it via the `update-config` skill when ready.

---

## Changelog

- **2026-04-29** - PR merge + forecast migration applied:
  - GitHub PR branch `claude/vigorous-jang-82408f` was merged and deleted by the owner. Local `main` fast-forwarded to `0fe0021` (`audit: pre-defense stabilization`); the existing local dashboard/SOUL/AGENTS working-tree edits were preserved untouched.
  - Supabase migration `005_price_forecast.sql` was applied successfully in SQL Editor. `price_forecast_daily` now exists, unblocking `analyze_price_forecast.py` upserts and the `query_price_forecast` skill's Supabase-first read path.
  - Manual GitHub Actions run `#14` reached `analyze_price_forecast.py` but failed because the script called `cmdstanpy.cmdstan_path()` before Prophet could configure its bundled CmdStan backend. Removed the eager `CMDSTAN` setup from both `analyze_price_forecast.py` and `evaluate_forecast.py`; next run should let Prophet initialize the backend normally and proceed to the Supabase upsert.

- **2026-04-29** — Pre-defense engineering audit and stabilization pass:
  - **GitHub Actions reviews job was dead.** `daily_ingest.yml` had a single `0 6 * * *` cron and the reviews job's `if` checked for `0 6 * * 1` — never matched, so reviews + sentiment never ran on schedule. Added a second cron (`0 7 * * 1`), guarded both jobs by `github.event.schedule`, and disallowed the reviews job on `workflow_dispatch` so manual dispatches don't accidentally burn Apify credits.
  - **Alert "exit" message bug.** `analyze_alerts.py` printed `was rank #None` on exit events because exit rows have `rank_today=None`. Now reports `rank_yesterday`. Also added `rank_yesterday` to the entrants query so the message has the data it needs.
  - **Alerts now idempotent (pragmatic fix for current pipeline).** `analyze_alerts.py` deletes today's alerts before inserting, so cron retries / manual re-runs don't duplicate rows. Trade-off: the two operations aren't transactional — a failure between delete and insert leaves today empty until the next run. Fine for thesis/demo; for production, replace with a transactional RPC or add a UNIQUE constraint on (snapshot_date, asin, alert_type, browse_node) and switch to upsert.
  - **Forecast data flow fixed (broken since inception).** `analyze_price_forecast.py` wrote forecasts to a gitignored `data/forecasts/` dir on the GitHub Actions runner — ephemeral, never reachable from the OpenClaw VM. The `query_price_forecast` skill on the VM therefore always returned "No forecast available". Added migration `005_price_forecast.sql` (`price_forecast_daily` table) and updated the analyze script to upsert there. Skill now reads Supabase first, falls back to local file.
  - **Migration 005 reused.** Old `005_openclaw_memory.sql` (dead per prior PROGRESS notes — Gateway has its own memory store) removed; replaced by `005_price_forecast.sql`.
  - **Doc fixes.** CLAUDE.md `streamlit run dashboard/Home.py` → `dashboard/app.py`. `query_aspects.md` sidecar synced with the post-2026-04-27 implementation (most-recent row, not aggregation across rows). `query_price_forecast.md` + wrapper SKILL.md describe the new Supabase source. `sentiment_detective/AGENTS.md` had `B0CRTR3PMF` listed as a `gaming_keyboard` — it's `true_wireless_earbuds`; corrected and split watchlist hints by category.
  - **Lightweight evaluation added (academically defensible).** `scripts/evaluate_sentiment.py` — distant-supervision check of RoBERTa labels against star ratings (1–2 → negative, 3 → neutral, 4–5 → positive); reports accuracy, macro-F1, per-class P/R/F1, confusion matrix. `scripts/evaluate_forecast.py` — walk-forward backtest with HOLDOUT=3 days; reports MAE, MAPE, naive-baseline MAE, and 80% PI coverage. Both write JSON under `data/eval/` for citation in the results chapter.
  - **Audit-scope correction (2026-04-29 PM).** The audit ran inside a git worktree (`.claude/worktrees/vigorous-jang-82408f`) checked out at commit `e51b203`. That sees only **committed** state, not the main working tree at `D:\market-tracker`. After the user flagged the gap I re-verified against the main tree and retracted two incorrect findings: (a) `web-dashboard/index.html` **does** exist (along with `style.css`, `vercel.json`, `README.md`) — the web dashboard is a real, working ECharts/Tailwind/Supabase app, currently untracked in git but deployable to Vercel; (b) the repo also has an untracked root-level `AGENTS.md` (sibling to `CLAUDE.md`). Both files were missed because the worktree did not contain them. Fixes for the AGENTS.md stale-script-name issues were applied in the main tree directly (untracked file). No code changes were made that depend on the missing-index.html assumption.
  - **Known issues left untouched (deliberately).** Hardcoded `/home/ubuntu` paths in OpenClaw wrappers (deployment-specific, by design). Deprecated root `collector_*.py` shims (already documented). `analyze_sentiment.py` aggregates over all-time reviews each day (`review_count_new` is misleadingly named) — methodology note added below; behavior unchanged to avoid disturbing BMS values 4 days before defense.

- **2026-04-28** — Output polish (Telegram production hardening) for all 3 agents:
  - **Hard line caps** to fit one Telegram message: Sentiment Detective ≤25 lines (one-ASIN) / ≤15 lines (trend); Competitor Spy ≤25 lines (category brief) / ≤15 lines (single mover); Momentum Strategist ≤30 lines (daily brief) / ≤20 lines (sub-query).
  - **No markdown tables anywhere** — they break on Telegram mobile. BMS top-N + three-lists + alerts are now numbered/bullet lists. Added explicit `Forbidden: markdown tables` rule in every SOUL.md.
  - **Numbers + ASINs wrapped in backticks** (`` `0.42` ``, `` `B0CDX5XGLK` ``) so MarkdownV2 escape rules don't eat them and they pop visually for scan.
  - **Banned closers**: no "Let me know…", "Hope this helps", "Want more detail?". Last line must be a concrete next step or a low-confidence/thin-data caveat.
  - **Spell guard** in Detective: section is `Concerns`, never `Confidences`. Added explicit forbidden line.
  - **Strategist alert grouping**: alerts are grouped by priority (Critical → New entrants → Action needed). Empty groups omitted. Stops the "dump everything" pattern.
  - **Action template enforced**: every action names a verb + ASIN + the metric that moves + ≤2h estimate. No more "improve listing".
  - **Numbers always have context**: bare `BMS 0.42` is forbidden; require Δ, prev value, or threshold (`BMS 0.42, Δ +0.11/7d`).
  - **Decorative emoji removed** from body text — only one per section header.
  - Files touched: `openclaw/agents/{sentiment_detective,competitor_spy,momentum_strategist}/{SOUL.md,AGENTS.md}` (6 files). No Python or skill logic touched — presentation-layer only.

- **2026-04-27** — Multi-agent deployment + cron scheduling milestone:
  - **3 specialist agents deployed** to Telegram. Each has its own workspace at `openclaw/agents/<name>/` with 4 markdown files (`SOUL.md`, `IDENTITY.md`, `AGENTS.md`, `USER.md`). Mapping:
    - 🕵️ `competitor_spy` ← `@babyspyyy_bot` (default account, repurposed Linny's bot)
    - 🔍 `sentiment_detective` ← `@babydetective_bot` (new)
    - 🎯 `momentum_strategist` ← `@babystrategist_bot` (new)
  - **OpenClaw skills registration**: 13 wrappers under `openclaw/wrappers/<skill>/SKILL.md` with YAML frontmatter, registered via `skills.load.extraDirs`. Source = `openclaw-extra`.
  - **3 cron jobs** scheduled in `Asia/Ho_Chi_Minh`:
    - `daily-brief-strategist` — 8 AM daily (Strategist)
    - `weekly-competitor-spy` — 9 AM Mon (Spy)
    - `weekly-sentiment-detective` — 9 AM Wed (Detective)
  - **End-to-end verified**: each bot returns real Supabase data; cron `daily-brief-strategist` test run delivered full 3-list brief to Telegram.
  - **Bug fix — `query_aspects.py`**: was SUMming Amazon's pre-aggregated product-level aspect summary across N reviews → inflated `total_mentions` by `N×` (e.g., 655K instead of 3.7K). Fixed to read the most recent non-null row only. Skill description updated to reflect that data is product-level, not per-review aggregation.
  - **Wrappers `python` → venv path**: all wrappers point to `/home/ubuntu/market-tracker/venv/bin/python` so OpenClaw agent runtime can find Supabase + dotenv deps.
  - **Cron requires elevated device scope** (`operator.admin`, `operator.write`, etc.) — approved via `devices approve <requestId>`.
- **2026-04-24** — Keepa cleanup + OpenClaw status correction:
  - Removed Keepa from the active tree: deleted `backfill_keepa.py`, stripped the `KEEPA_KEY` block from `.env.example`. No Keepa imports, dependencies, or references remain in code; Apify is the sole Amazon data source.
  - Corrected Telegram/OpenClaw status: Telegram bot verified with **default OpenClaw skills only** (healthcheck, node-connect, openai-whisper-api, skill-creator, taskflow, taskflow-inbox-triage, weather). Project-specific market-tracker skills still need registration/visibility validation.
  - Replaced stale `TELEGRAM_BOT_TOKEN` reference in `CLAUDE.md §2` — Telegram pairing + LLM key are owned by the OpenClaw Gateway, not this repo's `.env`.
  - Added explicit "Keepa is not part of this architecture" note in `CLAUDE.md §2`.
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
