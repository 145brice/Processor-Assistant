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
    loan_num TEXT,
    borrower TEXT,
    property_address TEXT,
    status TEXT,
    lender TEXT,
    loan_amount TEXT,
    purchase_price TEXT,
    loan_type TEXT,
    closing_date TEXT,
    loan_officer TEXT,
    loan_processor TEXT,
    contacts_json TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS activity_log (
    id BIGSERIAL PRIMARY KEY,
    loan_id INTEGER NOT NULL,
    ts TIMESTAMPTZ NOT NULL,
    action TEXT,
    detail TEXT,
    "user" TEXT,
    UNIQUE (loan_id, ts, action)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value_json TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security with permissive policy (anon key can read/write).
-- Tighten later if you add multi-tenant separation.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE loans ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "anon_all_users" ON users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all_loans" ON loans FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all_activity" ON activity_log FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all_settings" ON settings FOR ALL USING (true) WITH CHECK (true);
