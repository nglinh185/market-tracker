-- Migration 002 — Thêm columns mới cho analytics
-- Chạy trong Supabase SQL Editor

ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS list_price      NUMERIC(10,2);
ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS discount_pct    NUMERIC(5,2);
ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS stars_breakdown JSONB;
ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS ebc_html_hash   VARCHAR(32);

ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS sentiment_label TEXT;
ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS sentiment_score NUMERIC(5,4);
