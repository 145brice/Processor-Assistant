# App inventory

Everything the current Streamlit app does, page by page. Line numbers are for `app.py` at
commit `18f36b0` and will drift; search for the function name if a line number is off.

"Phase" says when the page is rebuilt: **Core** = tasks T-10 to T-27, **Tools** = T-30 to
T-33, **Later** = after switch-over or possibly dropped.

## Global layout

### Sidebar (`show_sidebar`, line 4555)

Top to bottom:

1. Theme toggle (light/dark), app name, user name and role (or "Sandbox mode").
2. **Scanner** (route key `dashboard`), **Pipeline - saved scans** (`pipeline`), caption "Loan
   history and saved scan results", **Overview** (`overview`).
3. **More Tools** group, collapsed by default. Inside it, five collapsible sub-groups:
   - Workspace: Reader, Team, Chat, Usage/Billing, History
   - Quick Tools: Loan Snapshot, Report Issue, Missing Docs, Doc Expiry, Spanish Reply
   - Advanced Tools: Income Verifier, Auto Data Entry, Credit Summary, DTI Calculator,
     Condition Clearer, Compliance Checker
   - Pipeline Advanced: Closing Package, Guideline Checker, Fraud Detector, Multi-Borrower,
     LOS Export
   - Advanced Automation: Rate Lock Monitor, Underwriting Tracker, Document Classifier,
     Escrow Calculator
4. **Settings** group, collapsed: Beta offer (or Pricing), Usage / Billing, a "Cloud AI ON ·
   Gemini · model" badge, Turn Cloud AI on/off, AI Settings.
5. Owner-only "Private Usage Counter" (active users, totals). Shown only to emails in
   `PA_PRIVATE_ADMIN_EMAILS`.
6. Logout.

More Tools is shown when `product_config.advanced_tools_enabled()` is true (default on;
`PA_ENABLE_ADVANCED_TOOLS=0` hides it and `visible_page()` redirects those routes to the
scanner).

### Persistent header (`show_persistent_header`, line 14411)

On every signed-in page: a close button, "MY PIPELINE" and status chips with counts: All,
Pending UW, Requested, Cleared, Overdue, Closed. Clicking a chip opens the pipeline filtered
by that status. A small coloured bar on the right shows the status mix.

### AI key setup wizard (`_render_gemini_key_prompt`, line 3619)

Shown at the top of the app to signed-in, non-sandbox users without a Gemini key, until they
skip it. Three steps: (1) welcome and paid-tier billing notice with Skip / I already have a
key / Let's set it up; (2) five instructions and an "Open Google AI Studio" link to
`https://aistudio.google.com/app/apikey`; (3) paste the key (must start with `AIza`), Save &
Continue. Saved encrypted to the account via `_save_user_gemini_key_for_account`. Optional
setup video from `PA_GEMINI_SETUP_VIDEO`. Users who skip see a yellow "Gemini API Key
Required" box on the scanner with "Set up key".

### Onboarding checklist (around line 4000)

Steps "Create your account", "Set up AI key", "Scan a loan document", with done states.

## Core pages

### Login (`show_login_page`, line 4203) · Core · T-12

Two-column page. Google sign-in through Supabase OAuth (`supabase_auth.begin_google_oauth`,
`exchange_google_code`). "Try with a sample loan" enters sandbox mode. Terms must be accepted
(`supabase_auth.accept_terms`). Rate-limited (`PA_LOGIN_MAX_FAILS`,
`PA_LOGIN_WINDOW_SECONDS`).

### Scanner (`show_dashboard`, route `dashboard`, line 4841) · Core · T-20 to T-23

The main screen.

1. Header "Scan documents" with intro text. If no key: "Get set up in 3 quick steps" box.
2. **Saved scans** expander: recent parsed scans (until deleted) with Restore.
3. **Upload loan PDFs**: multiple PDFs, 40 MB each.
4. "Privacy and data handling" expander and "Import pipeline spreadsheet" button.
5. **Detection list**, one row per file: checkbox, file name, document type dropdown
   (pre-filled by `ai_engine.detect_doc_type`), confidence. Duplicate pages and multi-part
   documents are grouped with merge choices. With 2+ files: Check All, Uncheck All, Remove
   unchecked.
6. **Scan (N selected)** button. For each checked file: `ai_engine.process_document(bytes,
   doc_type, user_approved_cloud=...)`; AI is used for Approval Letter and Purchase Contract
   when the user has a key. Monthly quota check per tier (`tiers.check_scan_quota`), usage
   logged (`billing.log_scan`). Each result is matched to a loan (`doc_verify._match_borrower`).
7. **Results**: "N document(s) scanned", + Upload More, Clear All. "Scan outputs": Copy
   results, Export PDF, Export CSV (`scan_outputs`), "Borrower needs-list email" and "Loan
   officer status update" drafts.
8. **Per-file result card**: summary line `OK file - Type (N cond) - match`, extraction note,
   loan match box (match → Merge into Loan / Open Loan; possible → Open & Verify / Start New
   Loan Instead; none → "+ Start New Loan from this Doc"), contacts, extracted fields table,
   conditions with party and status, per-condition actions (Email this item, Simplify
   wording, Translate / Spanish Reply), Draft emails.
9. Document types: Approval Letter, Loan Estimate (LE), 1003 Application, Purchase Contract,
   Credit Report, Bank Statement, Change of Circumstance (COC), Broker Package (BP), Pay Stub,
   W-2, 1099, Tax Return, Appraisal, Title Commitment, Hazard Insurance, Mortgage Statement,
   VA Certificate of Eligibility, DD-214, Government ID, Unknown.

### Pipeline (`show_pipeline`, route `pipeline`, line 7611) · Core · T-24

1. "View saved scan history", **+Add Loan** (form: loan number, borrower, status, dates,
   missing docs), **Bulk Import CSV/JSON**, status filter, search by loan number or borrower,
   sort (Newest and others), "My loans" toggle.
2. Loan cards: loan number, borrower, status, close and lock dates, lock-expired and missing
   badges, contacts line (seller, agents, title, HOI), progress % bar, delete (x). Status
   dropdown (Pending Underwriting, Requested, Cleared, Overdue, Closed), Assign To dropdown,
   "Notes & Conditions - Show", "Docs & Contacts - Show".
3. Inbox of loans shared by teammates (Accept / Dismiss), notifications, removed loans
   (Restore / Empty Removed, retention days), "Generate HOI" / "Generate Title" requests,
   "Send Update Now", upload documents to auto-fill a loan.
4. Data: `crm.get_all_loans`, `add_loan`, `update_loan`, `set_status`, `delete_loan`,
   `get_trash`, `restore_loan`, `bulk_import_loans`. Statuses: `crm.STATUS_OPTIONS`.

### Loan detail (`show_loan_detail`, route `loan_detail`, line 12104) · Core · T-25, T-26

The largest page (about 2,300 lines). Back to Pipeline; loan header; Change Status, Assigned
To; **Conditions** tab (status per condition: Needed, Requested, Important, Ready to Clear,
Cleared; Save Condition Updates; archived conditions) and **Summarized** tab; Notes (Save
Notes); documents (Save Docs; upload a document to scan and fill loan data; Scan Approval
Letter; Scan Folder Against Conditions); merge pending scan into this loan with approval
steps; contacts merge; Draft Email / Draft with AI / Open in Gmail; Generate HOI Request,
Generate Title Request; Flag Question; activity log (`crm.get_activity`).

### History (`show_history`, route `history`, line 11079) · Core · T-27

Saved parsed scans for the account (`scan_history_store.load`), restore into the scanner.

### AI Settings (`show_ollama_page`, routes `ai_settings`/`ollama`, line 11587) · Core · T-16

Provider shown as "Google Gemini" (fixed), key input, model, test connection
(`cloud_client.ping`), Cloud AI on/off, billing and training notices, setup video.

### Usage / Billing (`show_billing_page`, route `billing`, line 11977) · Core · T-27

Scans used this month, tier, history (`billing.get_usage`, `get_history`), upgrade links
(`tiers.stripe_payment_link`). During free beta (`tiers.free_beta_mode`) labelled "Usage".

### Pricing / Beta offer (`show_pricing_page`, route `pricing`, line 11792) · Core · T-27

Tier cards (`tiers.TIERS`): Free 20 scans, Starter, Pro, Unlimited; beta offer text from
`product_config.beta_offer()`.

### Overview (`show_overview_page`, route `overview`, line 4171) · Core · T-27

Post-login landing with value-prop highlights and the onboarding checklist.

### Privacy Policy and Terms (`show_privacy_policy_page` line 14473, `show_terms_page` line 14520) · Core · T-11

Static text. Copy the text exactly.

## More Tools pages

| Route key | Sidebar label | Function (line) | What it does | Phase |
|---|---|---|---|---|
| `reader` | Reader | `show_reader` (9189) | Browse a folder, open and search files | Later (desktop-only idea) |
| `team` | Team | `show_team_page` (9664) | Inbox folder and team members | Tools · T-33 |
| `chat` | Chat | `show_chat_page` (11898) | In-app chat between users (`chat_store`) | Later |
| `email_watch_controls`, `email_watch` | Email Watch | `show_email_watch_controls_page` (11108), `show_email_watch_page` (11295) | Background inbox watcher: credentials, start/stop, matched attachments queue | Later (needs a worker service) |
| `snapshot` | Loan Snapshot | `show_snapshot_page` (9792) | Complete vs missing documents for the current loan | Tools · T-30 |
| `report_issue` | Report Issue | `show_report_issue_page` (9881) | Save an issue report with SSN/account masking | Tools · T-30 |
| `missing_docs` | Missing Docs | `show_missing_docs_page` (9935) | Missing-documents checker and email | Tools · T-30 |
| `doc_expiry` | Doc Expiry | `show_doc_expiry_page` (9997) | Document expiry tracker | Tools · T-30 |
| `spanish_reply` | Spanish Reply | `show_spanish_reply_page` (10074) | Detect language, translate, draft reply | Tools · T-30 |
| `income_verifier` | Income Verifier | `show_income_verifier_page` (10203) | Income/employment verification vs 1003 | Tools · T-31 |
| `auto_data_entry` | Auto Data Entry | `show_auto_data_entry_page` (10259) | Fill forms from extracted data | Tools · T-31 |
| `credit_summary` | Credit Summary | `show_credit_summary_page` (10311) | Credit report import and summary | Tools · T-31 |
| `dti_calculator` | DTI Calculator | `show_dti_calculator_page` (10384) | Debt-to-income and closing costs | Tools · T-31 |
| `condition_clearer` | Condition Clearer | `show_condition_clearer_page` (10520) | Underwriting condition clearing | Tools · T-31 |
| `compliance_checker` | Compliance Checker | `show_compliance_checker_page` (10550) | Compliance checklist and flags | Tools · T-31 |
| `closing_package` | Closing Package | `show_closing_package_page` (10613) | Build a closing package | Tools · T-32 |
| `pipeline_dashboard` | (no sidebar link) | `show_pipeline_dashboard_page` (10646) | Pipeline deadline alerts | Tools · T-32 |
| `guideline_checker` | Guideline Checker | `show_guideline_checker_page` (10696) | Investor guideline checks | Tools · T-32 |
| `fraud_detector` | Fraud Detector | `show_fraud_detector_page` (10743) | Red-flag detector | Tools · T-32 |
| `multi_borrower` | Multi-Borrower | `show_multi_borrower_page` (10785) | Multiple borrowers per loan | Tools · T-32 |
| `los_export` | LOS Export | `show_los_export_page` (10824) | Export to loan origination systems | Tools · T-32 |
| `rate_lock_monitor` | Rate Lock Monitor | `show_rate_lock_monitor_page` (10869) | Lock expiry alerts | Tools · T-32 |
| `underwriting_tracker` | Underwriting Tracker | `show_underwriting_tracker_page` (10923) | Condition tracking automation | Tools · T-32 |
| `document_classifier` | Document Classifier | `show_document_classifier_page` (10975) | Classify and route documents | Tools · T-32 |
| `escrow_calculator` | Escrow Calculator | `show_escrow_calculator_page` (11014) | Closing costs and escrow | Tools · T-32 |
| `lender_learning` | (owner only) | `show_lender_learning_page` (9461) | De-identified lender format profiles | Later |

Each tool page is mostly UI around a module of the same name (`loan_snapshot.py`,
`dti_calculator.py`, `fraud_detector.py` and so on). Read the page function, find the module
calls, expose those calls through one endpoint per tool (`/api/tools/<route_key>`), then build
the page.

## Engine modules (keep, call through the API)

| Module | Role |
|---|---|
| `ai_engine.py` | PDF text extraction and local OCR (`extract_text_from_pdf`), document type detection (`detect_doc_type`), per-type extractors, `process_document` (main scan entry point), conditions, contacts, email drafting. |
| `cloud_client.py` | All AI calls, always after redaction. `get_config`, `is_enabled`, `ping`, `enhance_conditions`, purchase-contract and approval extraction. |
| `pii_sanitizer/` | Redaction before AI and scrubbing of AI replies (`integration.redact_for_cloud`, `redact_for_cloud_resilient`, `redact_gemini_output`). spaCy name model in production. |
| `privacy_filter.py` | Older redaction rules still used inside `pii_sanitizer`. |
| `doc_verify.py` | Document checks and `_match_borrower` (loan matching). |
| `crm.py` | Loans: list, add, update, status, documents, activity, trash. Stored as a per-user snapshot in Supabase (`supabase_sync`), JSON fallback; sandbox reads `pipeline.sample.json`. |
| `supabase_auth.py` | Google OAuth, user profiles, terms, encrypted Gemini key storage, browser sessions, settings table helpers. |
| `supabase_sync.py` | Pipeline snapshots and backups in Supabase. |
| `scan_history_store.py` | Saved parsed scans per user. |
| `scan_outputs.py` | Condition rows, CSV and PDF export, email drafts (`email_drafts`, `summary_text`, `csv_bytes`, `pdf_bytes`). The `render_*` functions are Streamlit UI: do not call them from the API. |
| `approval_intelligence.py` | Private per-processor lender statistics and condition ownership. |
| `tiers.py` | Tiers, scan limits, free beta mode, Stripe links. |
| `billing.py` | Monthly scan counts (SQLite file; resets on redeploy, see ARCHITECTURE). |
| `product_config.py` | Feature switches, beta offer text, setup video. |
| `email_service.py`, `email_watch.py`, `account_email_watch.py`, `email_store.py` | Email sending (Resend) and the inbox watcher. |

## Data shapes in use today

Scan batch (one per scanned file, kept in the scanner and saved to history):

```json
{
  "file": "approval.pdf",
  "type": "Approval Letter",
  "result": {
    "success": true,
    "doc_type": "Approval Letter",
    "conditions": "pipe-delimited rows or a list of condition objects",
    "extracted_data": {},
    "contacts": {},
    "risks": "",
    "ai_log": "CLOUD/SCRIPT/PRIVACY BLOCK log line",
    "image_only": false,
    "error": ""
  },
  "loan_match": {"loan_id": 12, "loan_num": "LN-2026-010", "borrower": "Derek & Monica Ruiz",
                 "confidence": 95, "suggestion": "match | possible | unknown"}
}
```

Condition (normalized by `_normalize_scanned_conditions` in `app.py`):
`{"num": 1, "desc": "...", "party": "Borrower|Title|Underwriter|Insurance|Closer|Appraiser|Employer|Realtor|Seller", "status": "Needed|Requested|Important|Ready to Clear|Cleared"}`.
`sample_loan.json` is a complete example.

Loan: see the `loans` table in `SUPABASE_SCHEMA.sql` (id, loan_num, borrower,
property_address, status, due_date, lender, loan_amount, purchase_price, loan_type,
closing_date, lock_expiry, missing_docs, assigned_to, notes, contacts, conditions, documents,
owner and sharing fields).
