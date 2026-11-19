# Tasks

Do them in order. Each card is one branch and one merge. Every card's checks include the
**standard checks**:

```bash
# from the repo root
python -m pytest -q backend/tests pii_sanitizer/tests test_privacy_filter.py test_product_updates.py
cd web && npm run lint && npm run build
```

and the **privacy scan** on your diff (all must print nothing):

```bash
git diff main -- . ':(exclude)docs' | grep -nE "inline_data|application/pdf.*(gemini|anthropic|openai)|PA_PDF_VISION" 
git diff main -- backend web ':(exclude)backend/tests' | grep -nE "GEMINI_API_KEY|GOOGLE_API_KEY|ANTHROPIC_API_KEY|OPENAI_API_KEY"
```

Status legend: `[ ]` to do, `[x]` merged.

---

## Phase 0: foundations

### [x] T-00 Skeleton

Delivered with this brief: `backend/pa_api` (health endpoint, context, models, 501 stubs),
`web/` (layout, sidebar, placeholder pages, typed API client). Standard checks pass.

### [x] T-03 Request context hooks in the engine

- **Goal:** engine modules read the current user and AI key from `pa_api.context` when the
  API is serving a request, and from Streamlit otherwise.
- **Read:** `ARCHITECTURE.md` "How the API reaches the engine"; `crm._current_user_key`,
  `crm._is_sandbox`; `cloud_client.get_config`; `backend/pa_api/context.py`.
- **Change:** in `crm.py` and `cloud_client.py` only, at the top of those three functions:
  `from backend.pa_api import context as _pa_ctx` inside a `try`, and if
  `_pa_ctx.current()` is not `None`, use it. In `get_config`, an active context returns
  `{"enabled": bool(key), "provider": "gemini", "api_key": key, "model": DEFAULT_MODELS["gemini"]}`
  and **never** reads environment keys or `cloud_config.json`.
- **Must not:** change behaviour when no context is active.
- **Check:** standard checks, plus new `backend/tests/test_context_hooks.py`:
  1. with `GEMINI_API_KEY=fake-server-key` set and a context whose `gemini_key=""`,
     `cloud_client.get_config()["api_key"] == ""` and `is_enabled()` is `False`;
  2. with context key `"AIza-user"`, `get_config()["api_key"] == "AIza-user"`;
  3. `crm._current_user_key()` returns the context user key, `""` in sandbox;
  4. with no context, `crm._current_user_key()` behaves as before (returns `""` outside Streamlit).

### [x] T-04 Sign-in check for API requests

- **Goal:** `pa_api.auth.get_context` (a FastAPI dependency) turns the request into a
  `RequestContext`.
- **Read:** `ARCHITECTURE.md` "Login and identity"; `backend/pa_api/auth.py` (stub).
- **Change:** validate `Authorization: Bearer` by calling `{SUPABASE_URL}/auth/v1/user` with
  headers `apikey: SUPABASE_ANON_KEY` and the bearer token (httpx, 10 s timeout, cache per
  token 60 s). Build the context: `user_key = user["id"]`, `email`, `gemini_key =
  supabase_auth.load_user_gemini_key(user_key, email)`. `X-PA-Sandbox: 1` and no bearer →
  sandbox context. Neither → `401`. Wrap each request so `context.use(ctx)` is active while
  the endpoint runs.
- **Must not:** log tokens or keys.
- **Check:** standard checks, plus `backend/tests/test_auth.py` with httpx mocked: valid token
  → context with that id; invalid → 401; sandbox header → sandbox context; key loaded once per
  request.

---

## Phase 1: shell, sign-in, AI key

### [x] T-10 App shell

- **Goal:** the signed-in layout looks and behaves like the current app.
- **Read:** `APP_INVENTORY.md` "Sidebar" and "Persistent header"; `web/src/components/Sidebar.tsx`
  and `Header.tsx` (skeleton); screenshots in `screenshots/` for the look.
- **Change:** light and dark themes (navy sidebar `#1a2840`-ish, brand blue `#4368b8`, slate
  greys), theme toggle stored in `localStorage`. Sidebar groups and items exactly as listed,
  More Tools and Settings collapsed by default, each sub-group collapsible, open/closed state
  remembered. Header status chips with counts from `GET /api/loans` (`counts`); clicking a
  chip opens `/pipeline?status=...`. Works at 390 px wide (sidebar becomes a drawer).
- **Check:** standard checks; manual: every sidebar link opens its page; chips show counts.

### [x] T-11 Privacy and Terms pages

- **Read:** `show_privacy_policy_page`, `show_terms_page` in `app.py`.
- **Change:** `/privacy` and `/terms` with the same text, word for word, plus the footer links.
- **Check:** standard checks; text matches the Streamlit pages.

### [x] T-12 Login, callback, sandbox, route guard

- **Read:** `show_login_page`; `ARCHITECTURE.md` "Login and identity".
- **Change:** `/login` (two columns: pitch on the left, "Continue with Google" and "Try with a
  sample loan" on the right); `/auth/callback` finishes the Supabase session and goes to
  `/scanner`; sandbox button sets `pa_sandbox=1` and goes to `/scanner`; `middleware.ts`
  sends signed-out, non-sandbox visitors to `/login`; logout clears session and sandbox.
- **Check:** standard checks; manual: Google sign-in round trip on localhost (add
  `http://localhost:3000/auth/callback` to Supabase redirect URLs); sandbox works signed out.

### [x] T-13 `/api/me` and terms

- **Change:** implement `GET /api/me` and `POST /api/me/accept-terms` per the contract
  (`features.more_tools` from `product_config.advanced_tools_enabled()`, `features.owner` from
  `PA_OWNER_ADMIN_EMAILS`). Web: show name and role in the sidebar, terms dialog on first
  sign-in, "Sandbox mode" label.
- **Check:** standard checks; tests for signed-in and sandbox responses.

### [x] T-15 AI key endpoints with live test

- **Goal:** users cannot save a key that does not work, and they learn why.
- **Change:** `GET/PUT/DELETE /api/ai-key`, `POST /api/ai-key/test` per the contract. `PUT`
  runs `cloud_client.ping("gemini", key)` first and saves only on success. Turn failures into
  plain reasons: invalid key, billing not enabled or free tier, quota exceeded, network
  problem. Never return or log the key.
- **Check:** standard checks; tests with `ping` mocked for each failure reason and for success
  (saved once); a test that no response body contains the key.

### [x] T-16 AI settings page and setup wizard

- **Read:** `_render_gemini_key_prompt`, `show_ollama_page`, `GEMINI_BILLING_NOTICE`,
  `GEMINI_TRAINING_NOTICE` in `app.py`.
- **Change:** `/settings/ai` (status, paste key, Test, Remove, notices, optional video) and the
  3-step wizard shown on signed-in pages when `me.ai.has_key` is false and not dismissed. Step
  3 calls `PUT /api/ai-key` and shows a green check or the plain reason.
- **Check:** standard checks; manual: wizard flow, skip, re-open from the scanner banner.

---

## Phase 2: core screens

### [x] T-20 Upload and detection

- **Change:** `POST /api/scan/detect` (PDF only, 40 MB each, in memory). Web `/scanner`: intro,
  setup banner when no key, multi-file upload, detection list (checkbox, name, type dropdown
  with every `DocType`, confidence), Check All / Uncheck All / Remove unchecked shown only for
  2+ files, "Scan (N selected)".
- **Check:** standard checks; test with a generated fake PDF; files over 40 MB → 413.

### [x] T-21 Scanning

- **Read:** the scan loop in `show_dashboard` (search `_scan_queue`), `_normalize_scanned_conditions`,
  `ai_engine.process_document`, `doc_verify._match_borrower`, `tiers.check_scan_quota`,
  `billing.log_scan`, `scan_history_store`.
- **Change:** `POST /api/scan` per the contract. Port `_normalize_scanned_conditions` into
  `backend/pa_api/normalize.py` (copy the logic, keep behaviour). Quota: owner emails and
  sandbox skip it; over the limit → `402`. Save the batch to history for signed-in users.
  Web: scan each checked file in turn with progress text, then the results list.
- **Must not:** pass PDF bytes to any AI function; set `user_approved_cloud` true without a
  user key.
- **Check:** standard checks, plus `backend/tests/test_scan_privacy.py`: build a fake approval
  PDF containing an invented SSN, name, phone and address; patch
  `cloud_client._generate` to record its `prompt` and `system`; call `POST /api/scan` with a
  context that has a fake key; assert none of the invented values appear in anything recorded.

### [x] T-22 Result card and outputs

- **Read:** result rendering in `show_dashboard`; `scan_outputs.py`.
- **Change:** `POST /api/outputs/email-drafts|csv|pdf`. Web result card: summary line,
  extraction note, contacts, fields table, conditions (party, status), Copy results, Export
  PDF, Export CSV, the two email drafts with copy buttons and "Open in Gmail".
- **Check:** standard checks; CSV and PDF download and open.

### [x] T-23 Loan matching actions

- **Change:** `POST /api/loans/from-scan` and `/api/loans/{id}/merge-scan` (same merge rules as
  the scanner: add conditions not already present by description, update contacts, purchase
  contract closing date). Web: match box with Merge into Loan / Open Loan, Open & Verify /
  Start New Loan Instead, + Start New Loan from this Doc.
- **Check:** standard checks; tests for merge without duplicates.

### [x] T-24 Pipeline

- **Change:** loan list, create, status, delete, removed, restore, import endpoints. Web
  `/pipeline`: + Add Loan form, Bulk Import, status filter (from `?status=`), search, sort,
  My loans toggle, loan cards as in the inventory, removed loans section.
- **Check:** standard checks; tests against a temporary pipeline (patch storage to a temp
  file; never touch real data).

### [x] T-25 Loan detail: core

- **Change:** `GET/PATCH /api/loans/{id}`, `PUT /api/loans/{id}/conditions`. Web `/loans/[id]`:
  header, Change Status, Assigned To, Conditions tab (edit status per condition, Save),
  Summarized tab, Notes (Save).
- **Check:** standard checks; manual round trip of a status and a note.

### [x] T-26 Loan detail: activity, contacts, documents, requests

- **Read:** the rest of `show_loan_detail`.
- **Change:** activity endpoint and list; contacts panel; documents list; Draft Email, Generate
  HOI Request, Generate Title Request (port the text builders to the API; they produce text,
  no sending); upload a document to scan into this loan (reuses `POST /api/scan` + merge).
- **Check:** standard checks.

### [x] T-27 History, usage, pricing, overview

- **Change:** `GET/DELETE /api/scans`, `GET /api/usage`, `GET /api/pricing`. Pages `/history`
  (restore into scanner), `/settings/usage`, `/pricing`, `/overview` with onboarding checklist.
- **Check:** standard checks.

### [ ] T-28 Core parity review

- **Goal:** prove the new core matches the old one.
- **Change:** none unless you find gaps; list gaps as new cards.
- **Check:** walk every bullet in `APP_INVENTORY.md` for Login, Scanner, Pipeline, Loan detail,
  History, AI Settings, Usage, Pricing, Overview in both apps with the sample loan and the fake
  approval; write the results table into this card.

**Parity results (2026-11-19, checked against the code and the running app in sample mode).**

| Area | Matches the old app | Gap | Plan |
|---|---|---|---|
| Login | Google, sample loan, terms and privacy links | Login rate limit (`PA_LOGIN_MAX_FAILS`) is Supabase's now | Accept |
| Scanner | Upload, detect, type override, bulk actions, scan, quota, AI note, loan match actions, contacts, fields, conditions, copy/PDF/CSV, two email drafts | Clear all / upload more; restore a saved scan into the scanner; per-condition actions (email this item, simplify, Spanish); merge pages of one bank statement | First two: **fix now**. Others: T-30 (Spanish reply), later card |
| Pipeline | Add loan, import, status filter from `?status=`, search, My loans, status change, delete, removed + restore, progress | Sort control; lock-expired and missing-docs badges; close/lock dates and contacts line on cards; Assigned To; Empty Removed and retention text | Sort and card details: **fix now**. Assigned To and Empty Removed: need the team/trash contract, T-33 |
| Shared-loan inbox, notifications, Send Update Now | none | Team features | T-33 |
| Loan detail | Status, conditions edit and save, notes, contacts, documents, activity, Draft Email, HOI/Title Word files, scan into loan | Summarized tab; Assigned To; archived conditions; Draft with AI; Flag Question; Scan Folder Against Conditions (desktop folder) | Summarized + Assigned To: **fix now**. Rest: later cards, folder scan dropped |
| History | List, delete | Restore into the scanner | **fix now** |
| AI Settings | Key, test, remove, billing and training notices, video | Cloud AI on/off switch (new app: on whenever a key exists) | Decision for owner |
| Usage / Pricing / Overview | Usage this month, tiers, beta offer, links, onboarding checklist | Usage history list | Later card (needs an endpoint) |

---

## Phase 3: More Tools

For each tool: read its `show_*_page` function, identify the module calls, expose them as
`POST /api/tools/<route_key>` with input and output shapes written into `API_CONTRACT.md`
first, then build `/tools/<route_key>`. Same privacy rules: any AI use goes through
`cloud_client` with redaction.

- [ ] **T-30** Quick Tools: snapshot, report_issue, missing_docs, doc_expiry, spanish_reply
- [ ] **T-31** Advanced Tools: income_verifier, auto_data_entry, credit_summary, dti_calculator,
  condition_clearer, compliance_checker
- [ ] **T-32** Pipeline Advanced + Automation: closing_package, pipeline_dashboard,
  guideline_checker, fraud_detector, multi_borrower, los_export, rate_lock_monitor,
  underwriting_tracker, document_classifier, escrow_calculator
- [ ] **T-33** Team page

Not planned for the rebuild (decide later): Reader, Chat, Email Watch, Lender Learning.

---

## Phase 4: deploy

### [ ] T-40 New Railway services (owner approves)

- **Change:** `backend/Dockerfile` (copy of the production Dockerfile, start command for
  uvicorn), Railway services `pa-api` and `pa-web` deploying from branch `rebuild`, variables
  per `ARCHITECTURE.md` (never the forbidden ones). Add the `pa-web` URL to Supabase redirect
  URLs.
- **Must not:** touch the production `Processor-Assistant` service or its variables.
- **Check:** `/api/health` 200 on `pa-api`; sign-in and sandbox work on `pa-web`; the privacy
  scan from T-21 passes against `pa-api` with fake data.

### [ ] T-41 Switch-over (owner only)

Point `processor.edgelandings.com` to `pa-web`; keep the Streamlit service on its Railway URL
for two weeks; then merge `rebuild` into `main` and retire Streamlit.
