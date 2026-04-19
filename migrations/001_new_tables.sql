-- ============================================================
-- Migration 001 — Các bảng mới cho thesis pipeline
-- Chạy trong Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================

-- 1. Cập nhật bảng asins: thêm is_active nếu chưa có
ALTER TABLE asins ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT FALSE;

-- 2. Cập nhật category_rankings: thêm is_sponsored nếu chưa có
ALTER TABLE category_rankings ADD COLUMN IF NOT EXISTS is_sponsored BOOLEAN DEFAULT FALSE;

-- 3. Cập nhật daily_snapshots: thêm các cột mới
ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS bullet_count   INT;
ALTER TABLE daily_snapshots ADD COLUMN IF NOT EXISTS description    TEXT;

-- ============================================================
-- Entrant / Exit Detection
-- ============================================================
CREATE TABLE IF NOT EXISTS entrant_exit_events (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_date   DATE        NOT NULL,
    browse_node     TEXT        NOT NULL,
    asin            TEXT        NOT NULL,
    event_type      TEXT        NOT NULL CHECK (event_type IN ('entrant', 'exit')),
    rank_today      INT,                        -- NULL nếu event_type = 'exit'
    rank_yesterday  INT,                        -- NULL nếu event_type = 'entrant'
    is_top10        BOOLEAN     DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, browse_node, asin, event_type)
);

-- ============================================================
-- Price Tier (K-Means)
-- ============================================================
CREATE TABLE IF NOT EXISTS price_tier_daily (
    id             BIGSERIAL PRIMARY KEY,
    snapshot_date  DATE  NOT NULL,
    browse_node    TEXT  NOT NULL,
    asin           TEXT  NOT NULL,
    price          NUMERIC(10,2),
    cluster_label  INT,                        -- 0, 1, 2
    cluster_name   TEXT,                       -- 'entry', 'mid', 'premium'
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, browse_node, asin)
);

-- ============================================================
-- Reviews
-- ============================================================
CREATE TABLE IF NOT EXISTS reviews_raw (
    id            BIGSERIAL PRIMARY KEY,
    asin          TEXT NOT NULL,
    review_id     TEXT NOT NULL,
    review_date   DATE,
    rating        INT,
    title         TEXT,
    review_text   TEXT,
    verified      BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (asin, review_id)
);

CREATE TABLE IF NOT EXISTS review_sentiment_daily (
    id                  BIGSERIAL PRIMARY KEY,
    snapshot_date       DATE NOT NULL,
    asin                TEXT NOT NULL,
    review_count_new    INT  DEFAULT 0,
    avg_sentiment_score NUMERIC(5,4),          -- -1.0 đến 1.0
    positive_ratio      NUMERIC(5,4),
    negative_ratio      NUMERIC(5,4),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, asin)
);

-- ============================================================
-- Brand Momentum Score
-- ============================================================
CREATE TABLE IF NOT EXISTS brand_momentum_daily (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    asin            TEXT NOT NULL,
    bsr_velocity    NUMERIC(10,4),             -- (BSR_prev - BSR_today) / BSR_prev
    review_velocity NUMERIC(10,4),             -- review_count delta / ngày
    sentiment_score NUMERIC(5,4),
    bms_score       NUMERIC(5,4),             -- weighted composite 0-1
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, asin)
);

-- ============================================================
-- Image Change Events
-- ============================================================
CREATE TABLE IF NOT EXISTS image_change_events (
    id             BIGSERIAL PRIMARY KEY,
    snapshot_date  DATE NOT NULL,
    asin           TEXT NOT NULL,
    hash_before    TEXT,
    hash_after     TEXT,
    hash_distance  INT,
    change_flag    BOOLEAN DEFAULT FALSE,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, asin)
);

-- ============================================================
-- Content Change Events (DOM diff)
-- ============================================================
CREATE TABLE IF NOT EXISTS content_change_events (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    asin            TEXT NOT NULL,
    change_area     TEXT NOT NULL CHECK (change_area IN ('title', 'bullets', 'description', 'aplus')),
    change_level    TEXT NOT NULL CHECK (change_level IN ('minor', 'major')),
    diff_summary    TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Listing Quality Score (LQS)
-- ============================================================
CREATE TABLE IF NOT EXISTS listing_quality_score_daily (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    asin            TEXT NOT NULL,
    title_score     NUMERIC(5,2),
    bullet_score    NUMERIC(5,2),
    image_score     NUMERIC(5,2),
    video_score     NUMERIC(5,2),
    aplus_score     NUMERIC(5,2),
    rating_score    NUMERIC(5,2),
    review_score    NUMERIC(5,2),
    sentiment_score NUMERIC(5,2),
    freshness_score NUMERIC(5,2),
    lqs_total       NUMERIC(5,2),             -- 0-100
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, asin)
);

-- ============================================================
-- Sponsored Ads
-- ============================================================
CREATE TABLE IF NOT EXISTS sponsored_ads_raw (
    id               BIGSERIAL PRIMARY KEY,
    snapshot_date    DATE NOT NULL,
    keyword          TEXT NOT NULL,
    browse_node      TEXT,
    ad_rank          INT,
    asin             TEXT,
    brand            TEXT,
    ad_type          TEXT,                    -- 'sponsored_product', 'sponsored_brand'
    placement_type   TEXT,                    -- 'top', 'middle', 'sidebar'
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sponsored_ad_share_daily (
    id                    BIGSERIAL PRIMARY KEY,
    snapshot_date         DATE NOT NULL,
    keyword               TEXT NOT NULL,
    brand                 TEXT NOT NULL,
    sponsored_slot_count  INT  DEFAULT 0,
    share_of_voice        NUMERIC(5,4),       -- slot_count / total_slots
    organic_overlap_count INT  DEFAULT 0,     -- số lần brand có cả organic lẫn sponsored
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (snapshot_date, keyword, brand)
);

-- ============================================================
-- Alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id               BIGSERIAL PRIMARY KEY,
    snapshot_date    DATE NOT NULL,
    asin             TEXT,
    browse_node      TEXT,
    alert_type       TEXT NOT NULL,           -- 'price_drop', 'stockout', 'image_change', etc.
    severity         TEXT CHECK (severity IN ('low', 'medium', 'high')),
    message          TEXT,
    metadata_json    JSONB,
    is_deduplicated  BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- Indexes để query nhanh hơn
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_category_rankings_date_node ON category_rankings (snapshot_date, browse_node);
CREATE INDEX IF NOT EXISTS idx_daily_snapshots_asin_date   ON daily_snapshots (asin, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_reviews_raw_asin            ON reviews_raw (asin);
CREATE INDEX IF NOT EXISTS idx_alerts_date_type            ON alerts (snapshot_date, alert_type);
CREATE INDEX IF NOT EXISTS idx_entrant_exit_date_node      ON entrant_exit_events (snapshot_date, browse_node);
