# Market Intelligence Dashboard

Modern web dashboard for the Amazon Market Tracker thesis project. Built with Tailwind CSS + Apache ECharts + Supabase JS.

## Files

```
web-dashboard/
├── index.html      Layout + Tailwind config
├── app.js          ECharts + Supabase fetch logic
├── style.css       Custom glow + card styles
├── vercel.json     Vercel deploy config
└── README.md       This file
```

## Setup — local preview

1. **Get Supabase anon key** (NOT service_role)
   - Open https://supabase.com/dashboard → your project → Settings → API
   - Copy `Project URL` and `anon / public` key

2. **Set credentials in `index.html`** — replace the two placeholders:

   ```js
   window.APP_CONFIG = {
     SUPABASE_URL:      "https://YOUR-PROJECT.supabase.co",
     SUPABASE_ANON_KEY: "eyJhbGc...",  // anon key, not service_role
   };
   ```

3. **Verify Row Level Security (RLS)** in Supabase
   For each table the dashboard reads (`asins`, `daily_snapshots`, `reviews_raw`,
   `alerts`, `brand_momentum_daily`), enable RLS and add a read policy for `anon`:

   ```sql
   alter table public.asins enable row level security;
   create policy "anon read asins" on public.asins for select using (true);
   -- repeat for the other 4 tables
   ```

4. **Run locally** — any static server works:

   ```bash
   cd web-dashboard
   python3 -m http.server 8080
   # open http://localhost:8080
   ```

## Deploy — Vercel

```bash
# Install CLI once
npm i -g vercel

# Deploy from repo root (or from web-dashboard/)
cd web-dashboard
vercel

# Follow prompts:
#  - Set up and deploy? Y
#  - Scope? (your account)
#  - Link to existing project? N
#  - Project name? market-tracker-dashboard
#  - Directory? ./   (current dir)
#  - Override settings? N

# Production deploy
vercel --prod
```

You'll get a URL like `https://market-tracker-dashboard.vercel.app`.

## Tech notes

- **No build step.** All dependencies via CDN — Tailwind, ECharts, Supabase JS.
- **Anon key is safe to expose** if RLS is enabled with read-only policies.
  Service role key must NEVER appear in `index.html` or `app.js`.
- **ECharts > Chart.js** for this design — better donut center text, smoother lines, glow effects via `lineStyle.shadowBlur`.

## What it shows

| Section | Data source | Skill / table |
|---|---|---|
| KPI: Tracked ASINs | `asins` count | — |
| KPI: Reviews Analyzed | `reviews_raw` count | `analyze_sentiment.py` |
| KPI: Alerts Today | `alerts` (latest snapshot) | `analyze_alerts.py` |
| KPI: Top BMS This Week | `brand_momentum_daily` max | `analyze_bms.py` |
| Alerts Over Time (14d) | `alerts` grouped by type+date | — |
| Category Share | `asins` grouped by category | — |
| Top Movers | `brand_momentum_daily` top 5 | `analyze_bms.py` |

## Customization

- **Colors**: edit `tailwind.config` in `index.html` (primary accents).
- **Chart styling**: ECharts options inside `app.js` (`backgroundColor`, `color` arrays).
- **Card layout**: classes in `index.html` use Tailwind utility — change `grid-cols-4` to add/remove cards.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| All KPIs show `--` | Missing Supabase credentials in `index.html` |
| 401 in console | RLS not configured for `anon` role |
| Charts empty | Tables have no data for the date range. Run analytics pipeline. |
| Layout broken | Tailwind CDN blocked — check network tab |
