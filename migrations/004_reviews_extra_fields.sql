-- Migration 004 — Thêm fields từ web_wanderer actor vào reviews_raw
--               + Tạo bảng product_review_summary

-- 1. Thêm 4 columns vào reviews_raw
ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS helpful_votes  INT     DEFAULT 0;
ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS is_vine        BOOLEAN DEFAULT FALSE;
ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS has_images     BOOLEAN DEFAULT FALSE;
ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS country        TEXT;

-- 2. Bảng product_review_summary — lưu AI summary + rating breakdown theo ASIN
--    (product-level data, 1 row/ASIN, upsert mỗi lần crawl)
CREATE TABLE IF NOT EXISTS product_review_summary (
    id              BIGSERIAL PRIMARY KEY,
    asin            TEXT        NOT NULL UNIQUE,
    ai_summary      TEXT,                        -- reviewsAISummary từ Amazon AI
    average_rating  NUMERIC(3,1),
    total_ratings   INT,
    pct_five_stars  NUMERIC(5,1),
    pct_four_stars  NUMERIC(5,1),
    pct_three_stars NUMERIC(5,1),
    pct_two_stars   NUMERIC(5,1),
    pct_one_star    NUMERIC(5,1),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
