-- Execution receipts introduced by the operational integrity release.
-- Safe to apply more than once; existing receipt rows are preserved.
CREATE TABLE IF NOT EXISTS nous_execution_receipts (
  id text PRIMARY KEY,
  user_id text NOT NULL,
  operation text NOT NULL,
  status text NOT NULL,
  verified boolean NOT NULL DEFAULT false,
  started_at timestamptz NOT NULL,
  completed_at timestamptz,
  evidence jsonb NOT NULL DEFAULT '{}'::jsonb,
  verification jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS nous_execution_receipts_user_created_idx
  ON nous_execution_receipts (user_id, created_at DESC);
