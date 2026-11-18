# Rules: never break these

Read this before every task. A task that breaks any rule is not done, even if it works.

## 1. Borrower privacy (most important)

Loan documents contain Social Security numbers, birth dates, account numbers, income and
home addresses. The owner is legally responsible for them.

1. **Document files never go to an AI service.** Never send PDF bytes, page images or base64
   of a document to Gemini, Claude, OpenAI or any other outside service. Search your diff for
   `inline_data`, `application/pdf`, `base64` near any AI call: there must be none.
2. **Only redacted text goes to AI.** All AI calls go through the existing functions in
   `cloud_client.py` (`enhance_conditions`, `extract_purchase_contract_ai`,
   `extract_approval_conditions_ai_from_pdf`). They redact with `pii_sanitizer` first. Do not
   write new code that calls an AI API directly.
3. **Never set or rely on `PA_PDF_VISION`.** It is an old opt-in that sends whole PDFs. It
   must stay unset.
4. **Do not change redaction behaviour** (`pii_sanitizer/`, `privacy_filter.py`) unless the
   task says so. If you do, all tests in `pii_sanitizer/tests` and `test_privacy_filter.py`
   must still pass, and you must not delete or loosen any test.
5. **No personal data in logs, errors or analytics.** Log document types, counts and timings,
   never names, numbers, addresses or document text. Error messages shown to users must not
   echo document content.
6. **Uploaded PDFs are processed in memory and not stored** (see the "Privacy and data
   handling" text in the current app). Do not write uploads to disk, a bucket or a database.
   Saved scans store extracted fields only, as today.

## 2. AI keys

1. **Scans use the signed-in user's own Gemini key, never the owner's.** The key is loaded
   per request from the user's account (`supabase_auth.load_user_gemini_key`).
2. **Never fall back to a server key for user scans.** `cloud_client.get_config()` falls back
   to `GEMINI_API_KEY`, `ANTHROPIC_API_KEY` and others from the environment. In the API that
   fallback must be switched off (task T-03). The existing `api_server.py` endpoints use a
   server key: do not reuse them for user scans.
3. If a user has no key, scans still work with local extraction only, and the UI points them
   to key setup.
4. Never send the user's key to the browser after it is saved. The API returns only whether a
   key is set and whether it works.

## 3. Production and deployment

1. **Never push to `main`.** Railway rebuilds production from `main` on every push. Work on a
   branch named `rebuild/T-xx-...`.
2. **Never change the production Railway service** (`Processor-Assistant`), its variables or
   its settings. A variable change triggers a rebuild. The new app gets new services (task
   T-40).
3. Do not edit `Dockerfile`, `railway.json`, `requirements.txt` or `.streamlit/` for the
   production app unless the task says so.

## 4. Data files and secrets

1. Never commit `pipeline.json`, `cloud_log.txt`, `scan_history.json`, `loan_docs/`,
   `loan_activity/`, `.env` files or anything listed in `.gitignore`. They can contain real
   borrower data.
2. Never put keys, tokens or passwords in code, tests or docs. Use environment variables, and
   add new ones to the table in `ARCHITECTURE.md`.
3. Test data must be invented. Use obviously fake names, numbers and addresses.

## 5. Code

1. Do not rewrite engine modules (`ai_engine.py`, `cloud_client.py`, `crm.py`,
   `doc_verify.py`, `pii_sanitizer/`, `tiers.py`, `billing.py`, `supabase_auth.py`,
   `supabase_sync.py`, `approval_intelligence.py`, `scan_outputs.py`). Call them. Small edits
   are allowed only where a task names them.
2. The Streamlit app (`app.py`) must keep working until the switch-over task. Do not remove
   anything from it.
3. TypeScript: `strict` mode, no `any` in `web/src/lib/`. Types must match `API_CONTRACT.md`.
4. Pin dependency versions. No packages released in the last two weeks.
5. Every task ends with its checks passing. Never skip, delete or weaken a test to make a
   check pass.
