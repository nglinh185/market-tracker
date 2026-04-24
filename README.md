# Amazon Market Intelligence Tracker

DS thesis — daily intelligence on 30 watchlist ASINs across 3 Amazon categories
(`gaming_keyboard`, `true_wireless_earbuds`, `portable_charger`).

> Full architecture: see [`CLAUDE.md`](CLAUDE.md). Live status: [`PROGRESS.md`](PROGRESS.md).

## Stack

- **Apify** — scraping (junglee/Amazon-crawler + web_wanderer/amazon-reviews-extractor)
- **Supabase** (Postgres) — warehouse, schema under `migrations/`
- **scikit-learn** KMeans — price tiers
- **RoBERTa** (`cardiffnlp/twitter-roberta-base-sentiment-latest`) — review sentiment
- **Prophet** — 7-day price forecast
- **imagehash** (pHash) — image-change detection
- **Streamlit + Plotly** — dashboard under `dashboard/`
- **OpenClaw** — agentic layer (read-only Skills over Supabase) under `openclaw/`

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in SUPABASE_URL, SUPABASE_KEY, APIFY_TOKEN
```

Run migrations 001–004 in order via Supabase SQL Editor.

## Daily pipeline

```bash
# 1. Ingest (writes to Supabase)
python scripts/ingest_category.py      # 3 categories -> category_rankings + asins
python scripts/ingest_watchlist.py     # 30 ASINs -> daily_snapshots + pHash
python scripts/seed_watchlist.py       # (one-off) mark watchlist ASINs is_active

# 2. Analytics (reads + writes derived tables)
python scripts/run_analytics.py
#   = entrant_exit -> changes -> sponsored -> price_tier
#     -> sentiment -> bms -> lqs -> alerts -> forecast

# 3. Reviews (weekly — tốn Apify credits)
python scripts/ingest_reviews.py       # reviews_raw
python scripts/analyze_sentiment.py    # RoBERTa -> sentiment_label/score
```

Orchestrator: `python scripts/run_all.py` runs the full daily chain.

## Dashboard

```bash
streamlit run dashboard/app.py
```

6 pages: Market Overview · Price Intelligence · Brand Competition · Listing Quality ·
Sentiment & Reviews · Alerts Center.

## OpenClaw Skills

13 read-only Skills under `openclaw/skills/`. Each accepts `python <skill>.py '<json-args>'`
and supports `--schema`:

```bash
python openclaw/skills/market/query_bms.py --schema
python openclaw/skills/market/query_bms.py '{"category":"gaming_keyboard","top_n":10}'
```

See [`openclaw/AGENTS.md`](openclaw/AGENTS.md) for the Skill contract.

## Repo layout

```
market-tracker/
├── config.py                  # categories, watchlist, actor IDs
├── lib/                       # Supabase client, Apify helper, parsers, image store
├── scripts/                   # ingest_* + analyze_*  (all DB mutations live here)
├── migrations/                # 001..004 SQL
├── dashboard/                 # Streamlit pages
├── openclaw/                  # skills + agent SOULs + manifest
└── thesis/                    # LaTeX thesis source
```

Legacy root-level `collector_*.py` and `db.py` are thin deprecation shims that forward to
`scripts/ingest_*.py` and `lib/db.py`. Prefer the new paths.
