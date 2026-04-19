-- Migration 003 — Lưu aspect-level sentiment từ web_wanderer actor
-- Chạy trong Supabase SQL Editor nếu muốn lưu aspects vào DB

ALTER TABLE reviews_raw ADD COLUMN IF NOT EXISTS aspects_json JSONB;

-- Index để query theo aspect name nhanh hơn
-- Ví dụ: SELECT * FROM reviews_raw WHERE aspects_json @> '[{"name":"Price"}]'
CREATE INDEX IF NOT EXISTS idx_reviews_raw_aspects ON reviews_raw USING GIN (aspects_json);
