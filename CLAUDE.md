# CLAUDE.md — Market Tracker Master Guide

> Single source of truth for any Claude / OpenClaw agent entering this repo.
> Read this first. Then `openclaw/AGENTS.md` for workspace rules, then the relevant `SOUL.md` for voice.

---

## 1. Project

**Amazon Market Intelligence Tracker** — DS thesis project.

- **Owner:** Vietnamese DS student (beginner/intermediate, knows pandas/sklearn)
- **Thesis deadline:** 2026-05-02
- **Goal:** Daily intelligence on 30 watchlist ASINs across 3 categories (`gaming_keyboard`, `true_wireless_earbuds`, `portable_charger`), surfaced as a Telegram brief.
- **Repo:** https://github.com/nglinh185/market-tracker
- **CI:** GitHub Actions workflow `Daily Amazon Data Ingest` runs daily (Apify → Supabase).
- **Runtime:** OpenClaw 2026.4.20 on VMware Workstation, model `openai/gpt-4o-mini` via `OPENAI_API_KEY`. Telegram channel connected; Gateway runtime verified. **Project skill registration pending** — Telegram currently lists only default OpenClaw skills (healthcheck, node-connect, openai-whisper-api, skill-creator, taskflow, taskflow-inbox-triage, weather), not the market-tracker workspace skills.

---

## 2. Tech Stack

| Layer             | Tool                                                                 |
| ----------------- | -------------------------------------------------------------------- |
| Scraping          | Apify (Amazon actor) → JSON                                          |
| Warehouse         | Supabase (Postgres) — 15+ tables, schema in `migrations/`            |
| ML — clustering   | scikit-learn KMeans (price tiers)                                    |
| ML — sentiment    | RoBERTa (`cardiffnlp/twitter-roberta-base-sentiment-latest`)         |
| ML — forecast     | Prophet (7-day price forecast)                                       |
| ML — image diff   | `imagehash` pHash, threshold 10                                      |
| Dashboard         | Streamlit + Plotly (`dashboard/`)                                    |
| Agentic layer     | **OpenClaw** (Gateway + Skills + SOUL) — see §4                      |
| Delivery          | Telegram (native OpenClaw Channel — do NOT hand-roll a bot)          |

Python deps: `requirements.txt`. Repo secrets: `.env` (`SUPABASE_URL`, `SUPABASE_KEY`, `APIFY_TOKEN`). Telegram pairing + LLM key (`OPENAI_API_KEY`) are owned by the OpenClaw Gateway, not this repo.

> Keepa is **not** part of this architecture. All historical + current Amazon data flows through Apify.

---

## 3. Repo Layout

```
market-tracker/
├── CLAUDE.md                 ← you are here
├── PROGRESS.md               ← live status log (update after every task)
├── lib/
│   └── db.py                 ← Supabase client (ALL DB access goes through here)
├── scripts/                  ← analytics pipeline (run daily)
│   ├── fetch_apify.py
│   ├── analyze_bms.py
│   ├── analyze_sentiment.py
│   ├── analyze_aspects.py
│   ├── analyze_price_tiers.py
│   ├── analyze_price_forecast.py
│   ├── analyze_changes.py    ← pHash image diff
│   ├── analyze_lqs.py
│   └── analyze_alerts.py
├── migrations/               ← SQL schema (001–004 active; 005 pending deletion)
├── dashboard/                ← Streamlit pages
├── data/forecasts/           ← Prophet outputs
└── openclaw/                 ← agentic workspace
    ├── SOUL.md               ← workspace default voice
    ├── AGENTS.md             ← workspace rules (Skill contract, routing, safety)
    ├── manifest.yaml         ← Gateway registry (skills, agents, triggers)
    ├── skills/
    │   ├── sentiment/        ← 3 skills: sentiment, reviews, aspects
    │   ├── market/           ← 6 skills: bms, rankings, entrant_exits,
    │   │                        sponsored_share, price_tiers, price_forecast
    │   ├── listing/          ← 3 skills: snapshots, image_changes, lqs
    │   └── alerts/           ← 1 skill: alerts
    └── agents/
        ├── sentiment_detective/SOUL.md
        ├── competitor_spy/SOUL.md
        └── momentum_strategist/SOUL.md    ← default agent
```

---

## 4. Gateway + Skills Architecture

```
 ┌─────────────┐   Telegram message    ┌──────────────────┐
 │   Phone     │ ────────────────────▶ │  OpenClaw        │
 │  Telegram   │                       │  Gateway         │
 └─────────────┘ ◀──────────────────── │  (native channel)│
                    brief / answer     └──────┬───────────┘
                                              │ routes by triggers
                                              ▼
                                     ┌────────────────────┐
                                     │  Agent (SOUL.md)   │
                                     │  sentiment_detect. │
                                     │  competitor_spy    │
                                     │  momentum_strateg. │
                                     └──────┬─────────────┘
                                            │ calls Skills
                                            ▼
                                     ┌────────────────────┐
                                     │ Skill (Python CLI) │
                                     │ stdin: JSON args   │
                                     │ stdout: JSON data  │
                                     └──────┬─────────────┘
                                            │ read-only
                                            ▼
                                     ┌────────────────────┐
                                     │ Supabase (Postgres)│
                                     │ via lib/db.py      │
                                     └────────────────────┘
```

**Contract for every Skill** (enforced in `openclaw/AGENTS.md`):

1. `SKILL = {...}` dict at module top (name, group, description, input_schema)
2. `run(**kwargs)` returns JSON-serializable `list[dict] | dict`
3. CLI: `python path/to/skill.py '<json-args>'` → JSON stdout; `--schema` prints the SKILL dict.

Skills are **read-only**. Mutations belong in `scripts/`.

**Agent routing** is keyword-based via `manifest.yaml.agents[].triggers` (EN + VI). Default agent: `momentum_strategist`.

---

## 5. Development Commands

### OpenClaw Gateway

```bash
# First-time setup (creates local Gateway daemon + pairs Telegram)
openclaw onboard

# Start the Gateway (long-running; serves Telegram + local CLI)
openclaw gateway

# Manage Telegram pairing
openclaw pairing list
openclaw pairing approve telegram <chat_id>

# Send a message to a subscriber (useful for scheduled briefs)
openclaw message send --channel telegram --to <chat_id> --text "..."

# Reload workspace after editing manifest/SOUL
openclaw reload
```

### Skills — direct execution (for testing)

```bash
# Run any skill directly with JSON args
python openclaw/skills/market/query_bms.py '{"category":"gaming_keyboard","top_n":10}'

# Inspect a skill's input schema
python openclaw/skills/market/query_bms.py --schema

# Run the full daily pipeline (before agent queries)
python scripts/fetch_apify.py
python scripts/analyze_bms.py
python scripts/analyze_sentiment.py
python scripts/analyze_aspects.py
python scripts/analyze_price_tiers.py
python scripts/analyze_price_forecast.py
python scripts/analyze_changes.py
python scripts/analyze_lqs.py
python scripts/analyze_alerts.py
```

### Dashboard

```bash
streamlit run dashboard/Home.py
```

---

## 6. Guardrails

- **DB access only via `lib/db.supabase`** — never instantiate a second client.
- **Skills are read-only.** Writes happen in `scripts/*.py` and run as scheduled jobs.
- **Voice lives in SOUL.md, rules live in AGENTS.md.** Don't mix them.
- **Vietnamese + English** triggers / messages are first-class. Keep replies terse, quote numbers + ASINs.
- **No custom agent scaffolding.** If the Gateway does it, use the Gateway.

---

## 7. Implicit State Synchronization

Every task completion or logic change should trigger an update to **PROGRESS.md** (status rows) and, if architecture shifts, to **this file**.

> **Honest limitation:** Markdown instructions cannot *enforce* auto-updates — Claude can only update these files when it remembers or is reminded. Genuine automation requires a `Stop` hook in `.claude/settings.json`. Ask the owner to wire one up if strict enforcement is needed.

---

## 8. Known Unknowns

- Exact Skill invocation shape the Gateway uses (stdin stream? HTTP? CLI-with-JSON?). Current assumption: CLI-with-JSON. Easy 5-min rewrite across all 13 skills if wrong.
- Per-agent SOUL.md placement — docs confirm workspace SOUL.md only; per-agent placement under `agents/<name>/SOUL.md` is a best guess.
- `migrations/005_openclaw_memory.sql` — Gateway has its own memory store, so this migration is likely dead. Awaiting owner decision to delete.
