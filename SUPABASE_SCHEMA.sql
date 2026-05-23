-- Processor Assistant: Supabase backup schema
-- Run this ONCE in your Supabase SQL Editor (Project → SQL → New query → paste → Run)
-- All tables use upsert; updated_at always set by client.

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    display_name TEXT DEFAULT '',
    role TEXT DEFAULT 'Processor',
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY,
    owner_user_key TEXT,
    created_by_user_key TEXT,
    assigned_user_key TEXT,
    shared_with_user_keys JSONB DEFAULT '[]'::jsonb,
    loan_num TEXT,
    borrower TEXT,
    property_address TEXT,
    status TEXT,
    due_date TEXT,
    lender TEXT,
    loan_amount TEXT,
    purchase_price TEXT,
    loan_type TEXT,
    closing_date TEXT,
    lock_expiry TEXT,
    commitment_date TEXT,
    missing_docs TEXT,
    folder_path TEXT,
    created_by TEXT,
    assigned_to TEXT,
    loan_officer TEXT,
    loan_processor TEXT,
    notes TEXT,
    contacts_json TEXT,
    conditions_json TEXT,
    documents_json TEXT,
    raw_json TEXT,
    created TEXT,
    updated TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS activity_log (
    id BIGSERIAL PRIMARY KEY,
    loan_id INTEGER NOT NULL,
    owner_user_key TEXT,
    ts TIMESTAMPTZ NOT NULL,
    action TEXT,
    detail TEXT,
    "user" TEXT,
    UNIQUE (loan_id, ts, action)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    user_key TEXT,
    user_email TEXT,
    value_json TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security. For production user-isolation policies, run
-- SUPABASE_SECURITY.sql after this schema file.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Bring older projects up to the current app schema without dropping data.
ALTER TABLE loans ADD COLUMN IF NOT EXISTS owner_user_key TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS created_by_user_key TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS assigned_user_key TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS shared_with_user_keys JSONB DEFAULT '[]'::jsonb;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS due_date TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS lock_expiry TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS commitment_date TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS missing_docs TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS folder_path TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS created_by TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS assigned_to TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS conditions_json TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS documents_json TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS raw_json TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS property_address TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS created TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS updated TEXT;
ALTER TABLE activity_log ADD COLUMN IF NOT EXISTS owner_user_key TEXT;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS user_key TEXT;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS user_email TEXT;

CREATE INDEX IF NOT EXISTS idx_loans_owner_user_key ON loans(owner_user_key);
CREATE INDEX IF NOT EXISTS idx_loans_created_by_user_key ON loans(created_by_user_key);
CREATE INDEX IF NOT EXISTS idx_loans_assigned_user_key ON loans(assigned_user_key);
CREATE INDEX IF NOT EXISTS idx_activity_owner_user_key ON activity_log(owner_user_key);
CREATE INDEX IF NOT EXISTS idx_settings_user_key ON settings(user_key);
CREATE INDEX IF NOT EXISTS idx_settings_user_email ON settings(user_email);
