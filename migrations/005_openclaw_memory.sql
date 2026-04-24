-- OpenClaw Memory Layer
-- Stores agent-generated insights and execution traces.

-- ── Agent outputs (what actors write) ──────────────────
CREATE TABLE IF NOT EXISTS market_insights_daily (
  id              uuid          DEFAULT gen_random_uuid() PRIMARY KEY,
  snapshot_date   date          NOT NULL,
  category        text,
  agent_name      text          NOT NULL,
  insight_type    text          NOT NULL,
  question        text,
  headline        text          NOT NULL,
  body_markdown   text          NOT NULL,
  telegram_text   text          NOT NULL,
  supporting_data jsonb         DEFAULT '{}'::jsonb,
  evidence_asins  text[]        DEFAULT '{}',
  confidence      numeric(3,2),
  created_at      timestamptz   DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_insights_date_agent
  ON market_insights_daily (snapshot_date DESC, agent_name);
CREATE INDEX IF NOT EXISTS idx_insights_category
  ON market_insights_daily (category, snapshot_date DESC);

-- ── Execution trace (what actors did) ──────────────────
CREATE TABLE IF NOT EXISTS openclaw_agent_runs (
  id             uuid          DEFAULT gen_random_uuid() PRIMARY KEY,
  run_date       date          NOT NULL,
  agent_name     text          NOT NULL,
  category       text,
  status         text          NOT NULL,        -- ok | error | partial
  skills_called  jsonb         DEFAULT '[]'::jsonb,
  input_tokens   integer,
  output_tokens  integer,
  latency_ms     integer,
  error_message  text,
  started_at     timestamptz   DEFAULT now(),
  finished_at    timestamptz
);

CREATE INDEX IF NOT EXISTS idx_runs_date_agent
  ON openclaw_agent_runs (run_date DESC, agent_name);

-- ── Telegram subscriptions (who gets daily briefs) ─────
CREATE TABLE IF NOT EXISTS telegram_subscribers (
  chat_id        bigint        PRIMARY KEY,
  username       text,
  categories     text[]        DEFAULT '{gaming_keyboard,true_wireless_earbuds,portable_charger}',
  daily_brief    boolean       DEFAULT true,
  alert_severity text          DEFAULT 'high',
  created_at     timestamptz   DEFAULT now()
);
