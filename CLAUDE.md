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
- **Runtime:** OpenClaw 2026.4.20 on VMware Ubuntu 24.04, model `openai/gpt-4o-mini` via `OPENAI_API_KEY` (owned by the OpenClaw Gateway, not this repo).
- **Multi-agent deployment** (3 specialist Telegram bots, 1:1 channel binding):
  - 🕵️ **Competitor Spy** (`@babyspyyy_bot`) — competitor moves: BMS, rankings, ad share, image redesigns
  - 🔍 **Sentiment Detective** (`@babydetective_bot`) — customer voice: sentiment trends, aspects, raw quotes
  - 🎯 **Momentum Strategist** (`@babystrategist_bot`) — synthesizer: alerts, forecast, LQS → 3-list weekly brief
- **Cron schedules** (Asia/Ho_Chi_Minh): daily 8 AM brief (Strategist), Mon 9 AM competitor recap (Spy), Wed 9 AM sentiment digest (Detective).

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
├── scripts/                  ← ingest + analytics pipeline (run daily / weekly)
│   ├── ingest_category.py    ← daily: 3 categories → category_rankings + asins
│   ├── ingest_watchlist.py   ← daily: 30 ASINs → daily_snapshots + pHash
│   ├── ingest_reviews.py     ← weekly: reviews_raw via web_wanderer actor
│   ├── seed_watchlist.py     ← one-off: mark watchlist ASINs in asins table
│   ├── run_analytics.py      ← orchestrates the analytics chain (below)
│   ├── analyze_entrant_exit.py
│   ├── analyze_changes.py    ← pHash image diff + content diff
│   ├── analyze_sponsored.py
│   ├── analyze_price_tier.py
│   ├── analyze_sentiment.py  ← RoBERTa
│   ├── analyze_bms.py
│   ├── analyze_lqs.py
│   ├── analyze_alerts.py
│   ├── analyze_price_forecast.py
│   ├── evaluate_sentiment.py ← stars-as-ground-truth eval (thesis appendix)
│   └── evaluate_forecast.py  ← walk-forward Prophet backtest
├── migrations/               ← SQL schema (001–005 active)
├── dashboard/                ← Streamlit pages
├── data/forecasts/           ← Prophet outputs
└── openclaw/                 ← agentic workspace
    ├── SOUL.md               ← workspace default voice (fallback only — deployed agents have their own)
    ├── AGENTS.md             ← workspace rules (Skill contract, routing, safety)
    ├── manifest.yaml         ← Gateway registry (skills, agents, triggers)
    ├── skills/               ← Python CLIs (read-only data access)
    │   ├── sentiment/        ← 3 skills: sentiment, reviews, aspects
    │   ├── market/           ← 6 skills: bms, rankings, entrant_exits,
    │   │                        sponsored_share, price_tiers, price_forecast
    │   ├── listing/          ← 3 skills: snapshots, image_changes, lqs
    │   └── alerts/           ← 1 skill: alerts
    ├── wrappers/             ← OpenClaw AgentSkill wrappers (YAML-frontmatter SKILL.md per skill)
    │   ├── query_bms/SKILL.md
    │   ├── query_sentiment/SKILL.md
    │   └── …                  ← 13 total, registered via skills.load.extraDirs
    └── agents/               ← per-agent isolated workspaces
        ├── sentiment_detective/        ← bound to @babydetective_bot
        │   ├── SOUL.md         ← voice + rules
        │   ├── IDENTITY.md     ← name, emoji, vibe
        │   ├── AGENTS.md       ← skill list with JSON examples + triggers
        │   └── USER.md         ← DS student context, EN/VI preferences
        ├── competitor_spy/             ← bound to @babyspyyy_bot
        │   └── (same 4 files)
        └── momentum_strategist/        ← bound to @babystrategist_bot
            └── (same 4 files)
```

---

## 4. Gateway + Skills Architecture

```
  ┌─────────────────┐ ┌─────────────────┐ ┌──────────────────┐
  │ @babyspyyy_bot  │ │@babydetective…  │ │@babystrategist…  │
  │   (Telegram)    │ │    (Telegram)   │ │   (Telegram)     │
  └────────┬────────┘ └────────┬────────┘ └────────┬─────────┘
           │ telegram:default  │ telegram:detective│ telegram:strategist
           ▼                   ▼                   ▼
     ┌──────────────────────────────────────────────────────┐
     │           OpenClaw Gateway  (1:1 channel binding)    │
     └──────┬───────────────────┬───────────────────┬───────┘
            ▼                   ▼                   ▼
     ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
     │ competitor_ │    │ sentiment_  │    │ momentum_       │
     │ spy         │    │ detective   │    │ strategist      │
     │ (SOUL.md)   │    │ (SOUL.md)   │    │ (SOUL.md)       │
     │ 6 skills    │    │ 4 skills    │    │ 5 skills        │
     └──────┬──────┘    └──────┬──────┘    └────────┬────────┘
            │                  │                    │
            └──────────────────┴────────────────────┘
                               │  agent runtime calls Python CLI
                               ▼
                     ┌──────────────────────┐
                     │  Skill (Python CLI)  │
                     │  stdin: JSON args    │
                     │  stdout: JSON data   │
                     └──────────┬───────────┘
                                │ read-only
                                ▼
                     ┌──────────────────────┐
                     │  Supabase (Postgres) │
                     │  via lib/db.py       │
                     └──────────────────────┘
```

**Contract for every Skill** (enforced in `openclaw/AGENTS.md`):

1. `SKILL = {...}` dict at module top (name, group, description, input_schema)
2. `run(**kwargs)` returns JSON-serializable `list[dict] | dict`
3. CLI: `python path/to/skill.py '<json-args>'` → JSON stdout; `--schema` prints the SKILL dict.
4. **OpenClaw wrapper:** each skill also has a YAML-frontmatter `openclaw/wrappers/<skill>/SKILL.md` that points to the venv Python invocation. Registered via `skills.load.extraDirs` in `~/.openclaw/openclaw.json`.

Skills are **read-only**. Mutations belong in `scripts/`.

**Agent routing** is **per-channel** (no keyword routing): each Telegram bot account binds 1:1 to a single agent via `agents bind --bind telegram:<accountId>`. Each agent's workspace contains a separate `AGENTS.md` listing trigger keywords (EN + VI) that the LLM uses to decide which skill to call.

---

## 5. Development Commands

### OpenClaw Gateway (run from `~/Documents/openclaw` in the VM)

```bash
# Service control (systemd-backed)
node openclaw.mjs gateway status
node openclaw.mjs gateway restart

# Channels (3 Telegram accounts: default, detective, strategist)
node openclaw.mjs channels list
node openclaw.mjs channels add --channel telegram --account <id> --token "$TOKEN" --name "..."

# Agents (3 specialists)
node openclaw.mjs agents list
node openclaw.mjs agents bindings

# Skills (13 wrappers, source = openclaw-extra)
node openclaw.mjs skills list

# Cron (3 jobs in Asia/Ho_Chi_Minh)
node openclaw.mjs cron list
node openclaw.mjs cron run <jobId>

# Pairing (per-bot, when /start gives a pairing code)
node openclaw.mjs pairing list
node openclaw.mjs pairing approve telegram <code>

# Device scope upgrade (CLI sometimes needs admin scope for cron/agents add)
node openclaw.mjs devices list
node openclaw.mjs devices approve <requestId>
```

### Skills — direct execution (for testing, in VM with venv)

```bash
# Run any skill directly with JSON args
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_bms.py '{"category":"gaming_keyboard","top_n":10}'

# Inspect a skill's input schema
/home/ubuntu/market-tracker/venv/bin/python /home/ubuntu/market-tracker/openclaw/skills/market/query_bms.py --schema

# Run the full daily pipeline (before agent queries)
python scripts/run_analytics.py        # orchestrates all 9 analytics in correct order
```

### Dashboard

```bash
streamlit run dashboard/app.py
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

## 8. Known Limitations (defendable in thesis)

- **Telegram polling occasionally stalls** (`getUpdates failed` errors in logs). VMware NAT instability; auto-recovers but messages can lag 30–60s. Mention as a deployment limitation.
- **9router `gpt-5.5` proxy** at `localhost:20128` was originally configured as primary model but is currently down — agents fall back to `openai/gpt-4o-mini` which works correctly. Document the failover behavior.
- **Migration 005** is now `005_price_forecast.sql` — adds `price_forecast_daily` so the OpenClaw VM can serve forecasts produced by GitHub Actions (file-based forecasts on the CI runner are ephemeral and unreachable from the VM). The earlier `005_openclaw_memory.sql` was dead (Gateway has its own memory store) and was removed.
- **No keyword routing inside one Telegram bot.** OpenClaw bindings are 1:1 channel-to-agent only. We use 3 separate bots instead — see §4 architecture diagram.
- **Prophet 7-day forecast on n=14 days of data** has limited accuracy — used for trend direction, not absolute price prediction. Disclosed in `analyze_price_forecast.py` docstring and `query_price_forecast` SKILL.md.
- **`query_aspects` returns Amazon's pre-aggregated product summary** (not per-review aggregation by us). Earlier bug double-aggregated; fixed 2026-04-27.
