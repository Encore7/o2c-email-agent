CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS source_emails (
  source_email_id UUID PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  email_id TEXT NOT NULL,
  received_at TIMESTAMPTZ NOT NULL,
  from_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, email_id)
);

CREATE TABLE IF NOT EXISTS invoices (
  invoice_pk UUID PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  invoice_id TEXT NOT NULL,
  amount DOUBLE PRECISION NOT NULL,
  currency TEXT NOT NULL DEFAULT 'USD',
  status TEXT NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, invoice_id)
);

INSERT INTO invoices (invoice_pk, tenant_id, invoice_id, amount, currency, status)
SELECT
  gen_random_uuid(),
  'tenant_id',
  'INV-' || gs::text,
  ((gs % 37 + 1) * 125)::double precision,
  'USD',
  'open'
FROM generate_series(10000, 10099) AS gs
ON CONFLICT (tenant_id, invoice_id) DO NOTHING;

CREATE TABLE IF NOT EXISTS cases (
  case_id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  email_id TEXT NOT NULL,
  category TEXT NOT NULL,
  case_title TEXT,
  dispute_details TEXT,
  case_priority TEXT,
  next_best_action TEXT NOT NULL,
  next_best_action_reason TEXT,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, email_id)
);

CREATE TABLE IF NOT EXISTS classified_emails (
  source_email_id UUID PRIMARY KEY REFERENCES source_emails(source_email_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  email_id TEXT NOT NULL,
  received_at TIMESTAMPTZ NOT NULL,
  from_email TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  category TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  reason TEXT NOT NULL,
  classification_source TEXT NOT NULL DEFAULT 'llm_primary',
  customer_name TEXT,
  invoice_references TEXT[] NOT NULL DEFAULT '{}',
  amounts DOUBLE PRECISION[] NOT NULL DEFAULT '{}',
  mentioned_dates DATE[] NOT NULL DEFAULT '{}',
  detail TEXT,
  invoice_match_summary TEXT,
  invoice_matches JSONB,
  reply_draft_subject TEXT,
  reply_draft_body TEXT,
  extraction_source TEXT NOT NULL DEFAULT 'hybrid_llm_regex',
  case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, email_id)
);

CREATE TABLE IF NOT EXISTS outbound_emails (
  outbound_email_id UUID PRIMARY KEY,
  source_email_id UUID NOT NULL REFERENCES source_emails(source_email_id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL,
  email_id TEXT NOT NULL,
  subject TEXT NOT NULL,
  body TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'sent_simulated',
  sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_source_emails_tenant_received
  ON source_emails (tenant_id, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_invoices_tenant_invoice
  ON invoices (tenant_id, invoice_id);

CREATE INDEX IF NOT EXISTS idx_classified_emails_tenant_category_received
  ON classified_emails (tenant_id, category, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_outbound_emails_tenant_sent
  ON outbound_emails (tenant_id, sent_at DESC);

ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS classification_source TEXT NOT NULL DEFAULT 'llm_primary';
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS customer_name TEXT;
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS invoice_references TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS amounts DOUBLE PRECISION[] NOT NULL DEFAULT '{}';
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS mentioned_dates DATE[] NOT NULL DEFAULT '{}';
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS detail TEXT;
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS invoice_match_summary TEXT;
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS invoice_matches JSONB;
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS reply_draft_subject TEXT;
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS reply_draft_body TEXT;
ALTER TABLE classified_emails ADD COLUMN IF NOT EXISTS extraction_source TEXT NOT NULL DEFAULT 'hybrid_llm_regex';

ALTER TABLE cases ADD COLUMN IF NOT EXISTS case_title TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS case_priority TEXT;
ALTER TABLE cases ADD COLUMN IF NOT EXISTS next_best_action_reason TEXT;
