-- Migration 005 — persist Prophet 7-day price forecasts to Supabase.
--
-- Why: forecasts are written to data/forecasts/*.json by analyze_price_forecast.py,
-- which is gitignored and ephemeral on GitHub Actions runners. The OpenClaw VM
-- (separate machine) cannot see those files, so the query_price_forecast skill
-- always returned "No forecast available". Persisting to Supabase fixes the
-- VM <-> CI data flow gap.
--
-- One row per (snapshot_date, asin, ds): the forecast point `ds` produced when
-- the model ran on `snapshot_date`. Re-runs on the same day overwrite via UPSERT.

CREATE TABLE IF NOT EXISTS price_forecast_daily (
    id             BIGSERIAL PRIMARY KEY,
    snapshot_date  DATE        NOT NULL,        -- date the forecast was generated
    asin           TEXT        NOT NULL,
    ds             DATE        NOT NULL,        -- forecasted date (1..7 days ahead)
    yhat           NUMERIC(10,2),
    yhat_lower     NUMERIC(10,2),
    yhat_upper     NUMERIC(10,2),
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, asin, ds)
);

CREATE INDEX IF NOT EXISTS idx_price_forecast_asin_date
    ON price_forecast_daily (asin, snapshot_date DESC);
