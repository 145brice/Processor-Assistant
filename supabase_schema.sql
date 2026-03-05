-- Processor Traien - Supabase Database Schema
-- Run this in your Supabase SQL Editor (Dashboard > SQL Editor > New Query)

-- Scan History: stores ONLY structured results, never raw documents
CREATE TABLE IF NOT EXISTS scan_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    conditions TEXT NOT NULL DEFAULT '',
    risks TEXT NOT NULL DEFAULT '',
    bank_rules TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security: users can only see their own data
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own history"
    ON scan_history FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own history"
    ON scan_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Admin Patterns: anonymized rule results for learning (NO PII)
CREATE TABLE IF NOT EXISTS admin_patterns (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    doc_type TEXT NOT NULL,
    rule_results JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Only service role can write to admin_patterns (app writes via service key)
ALTER TABLE admin_patterns ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role can manage patterns"
    ON admin_patterns FOR ALL
    USING (true)
    WITH CHECK (true);

-- Index for faster history queries
CREATE INDEX IF NOT EXISTS idx_scan_history_user_id ON scan_history(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_history_created_at ON scan_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_admin_patterns_doc_type ON admin_patterns(doc_type);
