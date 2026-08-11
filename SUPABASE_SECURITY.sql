-- Processor Assistant: Supabase production security schema
-- Run in Supabase SQL Editor after setting Google Auth.
-- Goals:
--   - Authenticated users can only access their own rows.
--   - Service role may still be used by the Streamlit backend, but app code must pass user-scoped keys.
--   - Gemini keys are stored by the app as encrypted JSON under settings key user_ai:<auth.uid()>.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

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
    closing_date TEXT,
    lock_expiry TEXT,
    commitment_date TEXT,
    missing_docs TEXT,
    folder_path TEXT,
    created_by TEXT,
    assigned_to TEXT,
    lender TEXT,
    loan_amount TEXT,
    purchase_price TEXT,
    loan_type TEXT,
    loan_officer TEXT,
    loan_processor TEXT,
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

CREATE TABLE IF NOT EXISTS parsed_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_key TEXT NOT NULL,
    doc_type TEXT,
    filename TEXT,
    result_json JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Add missing columns safely for existing projects.
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
ALTER TABLE loans ADD COLUMN IF NOT EXISTS created TEXT;
ALTER TABLE loans ADD COLUMN IF NOT EXISTS updated TEXT;
ALTER TABLE activity_log ADD COLUMN IF NOT EXISTS owner_user_key TEXT;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS user_key TEXT;
ALTER TABLE settings ADD COLUMN IF NOT EXISTS user_email TEXT;

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE parsed_results ENABLE ROW LEVEL SECURITY;

-- Remove old permissive policies if present.
DROP POLICY IF EXISTS "anon_all_users" ON users;
DROP POLICY IF EXISTS "anon_all_loans" ON loans;
DROP POLICY IF EXISTS "anon_all_activity" ON activity_log;
DROP POLICY IF EXISTS "anon_all_settings" ON settings;
DROP POLICY IF EXISTS "users_own_rows" ON users;
DROP POLICY IF EXISTS "loans_owner_or_shared" ON loans;
DROP POLICY IF EXISTS "activity_owner" ON activity_log;
DROP POLICY IF EXISTS "settings_owner" ON settings;
DROP POLICY IF EXISTS "parsed_results_owner" ON parsed_results;

-- Users can read/update only their own user row when the row id is their Supabase auth uid.
CREATE POLICY "users_own_rows" ON users
FOR ALL TO authenticated
USING (id = auth.uid()::text)
WITH CHECK (id = auth.uid()::text);

-- Loans are visible/editable only to owner/creator/assignee/shared user.
CREATE POLICY "loans_owner_or_shared" ON loans
FOR ALL TO authenticated
USING (
    owner_user_key = auth.uid()::text
    OR created_by_user_key = auth.uid()::text
    OR assigned_user_key = auth.uid()::text
    OR shared_with_user_keys ? auth.uid()::text
)
WITH CHECK (
    owner_user_key = auth.uid()::text
    OR created_by_user_key = auth.uid()::text
    OR assigned_user_key = auth.uid()::text
    OR shared_with_user_keys ? auth.uid()::text
);

CREATE POLICY "activity_owner" ON activity_log
FOR ALL TO authenticated
USING (owner_user_key = auth.uid()::text)
WITH CHECK (owner_user_key = auth.uid()::text);

-- Settings keys are namespaced by auth uid:
--   user_ai:<uid>              encrypted Gemini key
--   pipeline_json:<uid>        durable per-user pipeline snapshot
--   lender_format_profiles:<uid> owner-private de-identified format profiles
CREATE POLICY "settings_owner" ON settings
FOR ALL TO authenticated
USING (
    key = ('user_ai:' || auth.uid()::text)
    OR key = ('pipeline_json:' || auth.uid()::text)
    OR key = ('lender_format_profiles:' || auth.uid()::text)
)
WITH CHECK (
    key = ('user_ai:' || auth.uid()::text)
    OR key = ('pipeline_json:' || auth.uid()::text)
    OR key = ('lender_format_profiles:' || auth.uid()::text)
);

CREATE POLICY "parsed_results_owner" ON parsed_results
FOR ALL TO authenticated
USING (owner_user_key = auth.uid()::text)
WITH CHECK (owner_user_key = auth.uid()::text);

CREATE INDEX IF NOT EXISTS idx_loans_owner_user_key ON loans(owner_user_key);
CREATE INDEX IF NOT EXISTS idx_loans_created_by_user_key ON loans(created_by_user_key);
CREATE INDEX IF NOT EXISTS idx_loans_assigned_user_key ON loans(assigned_user_key);
CREATE INDEX IF NOT EXISTS idx_activity_owner_user_key ON activity_log(owner_user_key);
CREATE INDEX IF NOT EXISTS idx_parsed_results_owner_user_key ON parsed_results(owner_user_key);
CREATE INDEX IF NOT EXISTS idx_settings_user_key ON settings(user_key);
CREATE INDEX IF NOT EXISTS idx_settings_user_email ON settings(user_email);
