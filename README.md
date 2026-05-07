# Pipeline Manager — Online Mortgage Processing App

**Online mortgage processing workspace with cloud AI support and local fallback tools.**
Runs in your browser as a processing workspace for mortgage teams.
Built for mortgage processors, loan officers, processing managers, and their teams.

Cloud AI and local fallback tools are available for enhanced processing features.

---

## QUICK START

1. Open **VS Code**
2. Open the terminal: `` Ctrl+` ``
3. Run:
   ```
   cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
   streamlit run app.py
   ```
4. Browser opens at **http://localhost:8501**
5. Log in with your account, or click **Try Sandbox** to explore without an account

To stop: press `Ctrl+C` in the terminal

---

## FIRST-TIME SETUP (do once)

### Step 1 — Python check
```
python --version
```
Need 3.10 or higher. Download from python.org if not installed.

### Step 2 — Install packages
```
pip install streamlit pypdf thefuzz python-Levenshtein python-dotenv
```
5 packages. No API keys. No accounts. No `.env` file needed for core features.

### Step 3 — Fannie/Freddie guideline PDFs (optional but powerful)
Place these exact filenames on your Desktop:
```
C:\Users\user\OneDrive\Desktop\Fannie Mae.pdf
C:\Users\user\OneDrive\Desktop\Freddie Mac.pdf
```
Capital letters and spacing must match exactly. Download free from FannieMae.com and FreddieMac.com.
If you skip this, everything else in the app still works — just the "Check Guidelines" feature won't have anything to search.

### Step 4 — Run
```
streamlit run app.py
```

---

## FILE STRUCTURE — Every file explained

```
Processor-Assistant/
|
|-- app.py                 Main file. Every page, button, form, and layout lives here.
|                          Edit this file to change how anything looks or behaves.
|                          Professional UI with tight layout, clean icons, and
|                          status-colored badges throughout.
|
|-- ai_engine.py           The processing brain. Pure Python regex + pattern matching.
|                          Reads PDFs, extracts conditions, drafts emails, runs the
|                          bank statement 50-rule analysis, detects risk flags,
|                          extracts contacts, parses 1003 applications, parses
|                          purchase contracts. Includes bank statement field
|                          extraction for PNC, Chase, Bank of America, Wells Fargo,
|                          and generic statement formats.
|
|-- ai_router.py           Single entry point for all AI-enhanced features.
|                          Routes requests to Cloud AI, Ollama, or the local fallback
|                          engine based on user config. Falls back gracefully
|                          if a backend is unavailable.
|
|-- cloud_client.py        Optional cloud AI backend. Supports Anthropic Claude
|                          and OpenAI. Requires an internet connection and a valid
|                          API key. Used for enhanced condition extraction, smarter
|                          email drafting, and AI-powered document analysis.
|
|-- ollama_client.py       Optional local LLM enhancement. Connects to a locally
|                          running Ollama instance (e.g., Llama, Mistral).
|                          Local fallback tools for script-based processing.
|
|-- doc_verify.py          Quick Doc Verify engine. Identifies document type,
|                          counts pages, checks date freshness, fuzzy-matches
|                          borrower names against your pipeline.
|
|-- email_watch.py         Email inbox watcher. Connects to Gmail/Outlook/Yahoo
|                          via IMAP, checks for unread emails with PDF attachments,
|                          downloads them, runs doc_verify, queues for review.
|
|-- crm.py                 Pipeline data layer. All CRUD for loans. Reads/writes
|                          pipeline.json. Auto-flags overdue loans based on 24hr
|                          response timer (stamps requested_at when loan moves to
|                          Requested status). Supports created_by, assigned_to,
|                          share_id, lock expiry, closing dates, and condition
|                          tracking per loan.
|
|-- billing.py             Billing and usage tracker. Tracks monthly document
|                          scans per user and calculates costs against the
|                          pricing tiers.
|
|-- fraud_check.py         Fraud detection engine. Scans W-2, pay stub, and
|                          bank statement PDFs for common fraud indicators.
|                          Flags when 2+ clues found using local regex checks.
|
|-- export.py              Export module. Generates downloadable outputs from
|                          scan results: CSV condition tables and HTML condition
|                          snapshot reports (print-to-PDF ready).
|
|-- folder_search.py       Folder search engine. Walks subfolders, fuzzy-matches
|                          filenames and PDF content to condition keywords.
|                          Includes find_bank_statements() for targeted searches.
|
|-- guidelines.py          Fannie/Freddie index and search engine. Breaks PDFs
|                          into overlapping 1,500-char chunks, caches as JSON.
|                          First run: 2-5 min. After that: instant from cache.
|
|-- sharing.py             Private loan sharing. Each user has a personal inbox
|                          folder. Sharing = writing a JSON file into someone's
|                          inbox folder. No central hub. Activity notifications
|                          (opened, updated, status changed) drop lightweight
|                          .notify.json files into shared members' inboxes.
|
|-- db.py                  Local SQLite database. Stores user accounts (name,
|                          role, password hash) and scan history. Creates
|                          processor.db automatically on first run.
|
|-- prompts.py             Output templates — stacking order format, research
|                          link patterns, risk flag labels.
|
|-- test_extraction.py     Extraction test suite. Runs all document extraction
|                          functions against realistic mock text. No real PDFs
|                          needed — tests the regex/pattern logic directly.
|
|-- pipeline.json          All loan pipeline data. Auto-created on first run.
|                          Pre-loaded with sample loans showing all statuses.
|
|-- team.json              Personal team roster. Auto-created when you add
|                          teammates. Stores name, role, inbox path per person.
|
|-- email_config.json      Email watch credentials. Created when you save
|                          settings. Stored locally — never sent anywhere.
|
|-- processor.db           SQLite database file. Auto-created. Holds logins
|                          and scan history.
|
|-- loan_activity/         Per-loan activity logs. Tracks status changes,
|                          reassignments, note edits, and other actions
|                          with timestamps and user attribution.
|
|-- removed/               Removed/trashed loans with configurable retention
|                          (7-90 days or forever). Restore or permanently
|                          delete from the Removed section in Pipeline.
|
|-- incoming/              Where email attachment PDFs land when Email Watch
|                          downloads them. Files sit here until you act on them.
|
|-- guidelines_index/      Cache folder for Fannie/Freddie index. Auto-created.
|   |-- Fannie_Mae.json    Built on first use (~2 min, 1,191 pages)
|   |-- Freddie_Mac.json   Built on first use (~5 min, 2,882 pages)
|   +-- *.hash             Detects when source PDFs changed; rebuilds cache
|
|-- requirements.txt       Full package list. Run: pip install -r requirements.txt
+-- README.md              This file.
```

---

## THE APP PAGES

---

### 1. Document Scanner
The main workhorse — this is the default landing page. Upload any mortgage PDF, and the app processes it based on document type.

#### Quick Verify (top of scanner — use this first)
Drop any PDF — no configuration needed. Instant checks:

| Check | What it does |
|---|---|
| **Doc type** | Identifies from 14+ known types (bank statement, pay stub, W-2, 1099, VOE, appraisal, 1003, purchase contract, approval letter, title doc, closing disclosure, credit report, insurance, loan estimate, tax return) |
| **Page count** | Compares to type-specific minimums. Bank statements need 2+, appraisals need 8+. |
| **Date freshness** | Finds newest date, calculates age. Flags bank statements/pay stubs older than 30 days. |
| **Borrower match** | Fuzzy-matches names from the PDF against every loan in your pipeline. |

**Verdict card:**
- Green — all checks pass, ready for review
- Yellow — minor flag, double-check flagged items
- Red — needs attention before saving

**Actions:** Save to folder, Scan this doc (full scan), Open in Reader

---

#### Full Document Scan (below Quick Verify)

1. Upload a PDF (or multiple)
2. Doc type is **auto-detected** and pre-selected in the dropdown — override if needed
3. Click Scan Document

**Bulk Upload mode:** Upload multiple PDFs at once. Doc type is always auto-detected per file. A **Scan All** button processes every uploaded file in one click.

**Duplicate detection:** If two uploaded PDFs are identical (same file uploaded twice), a warning banner appears before scanning.

**Page grouping / PDF merge:** If multiple uploaded PDFs are the same doc type (e.g., two bank statement pages), the app offers to merge them into a single PDF before scanning.

Routes to different outputs by document type:

**Approval Letter, CD, LE, Credit Report, COC, Broker Package** — Condition table with expandable rows sorted by priority. Each condition row has:
- Status buttons (Important / Needed / Requested / Ready to Clear / Cleared)
- Party multiselect (Borrower, Title, Appraiser, etc.)
- Notes field
- Fetch from Folder — search borrower's folder for matching files
- Check Guidelines — search Fannie/Freddie for relevant sections
- Find & Analyze Bank Stmt — auto-appears on conditions mentioning deposits/bank statements

**Draft Email** — Check conditions, pick language (English/Spanish), pick recipient (Borrower, Title, Underwriter, Insurance, Closer, Appraiser), generate professional email instantly. Works for all 6 recipient types in both languages.

After any draft generates, a **📬 Compose in Gmail** button appears — opens Gmail in a new tab with To, Subject, and body pre-filled. No API needed, works instantly.

**Condition Export** — Download conditions as CSV or generate a printable HTML snapshot report.

**Bank Statement** — 50-rule analysis + Account Summary card. Checks:
- Green: item confirmed in the statement
- Red: problem found (NSF, overdraft, returned item, gambling, crypto, foreign currency, charge-off)
- Yellow: required item not found (account number, statement period, holder name)
- Blue: optional item found that may need a letter (large deposit, tax refund, pension)
- Purple: cannot determine from text — verify manually

**Bank Statement Account Summary card** — Automatically extracted from real statement PDFs:
- Account holder name(s)
- Account number (masked)
- Financial institution
- Statement period (start date → end date)
- Beginning balance
- Ending balance
- Total deposits / total withdrawals

Works with PNC, Chase, Bank of America, Wells Fargo, and generic statement formats. Handles comma-formatted dollar amounts and multi-column table layouts (PNC format).

**1003 Application** — Two-column structured field extraction (borrower info, loan terms, property). Missing fields shown in red. Push to Pipeline in one click.

**Purchase Contract** — Three-column extraction (parties, transaction/title, agents). Includes contingencies and addendums. Draft Title Email generates a ready-to-send email with all transaction details.

**Fraud Check** — Available for W-2, pay stubs, and bank statements. Scans for common fraud indicators using regex pattern matching and flags when 2+ clues are detected.

---

### 2. My Pipeline
Loan tracking dashboard. Compact, scrollable pipeline — Excel-thin rows with tabbed column alignment across all loans.

**Status colors:**
- Red (Pending) — waiting on borrower or docs
- Orange (Requested) — docs requested, 24hr response timer starts automatically
- Green (Cleared) — all conditions met, ready to close
- Gray (Overdue) — auto-flagged after 24hrs with no response to a Requested loan
- Closed — funded and done

**24hr Response Timer:**
When a loan is set to Requested, a countdown badge appears: `⏱ 18.5h to respond`.
After 24hrs with no status change, the loan auto-flips to Overdue and shows `⚠ NO RESPONSE Xh overdue`.
Lock expiry is tracked separately and has no effect on this timer.

**Status change confirmation:**
Manually changing a loan status shows "Are you sure?" with ✓ Yes / ✗ No before saving.
Every manual change is logged with timestamp and username in the loan's activity trail.

**Sort options:** Newest, Closing Date, Lock Expiry, Last Name, First Name, Loan #, Status, Loan Amount (High/Low), Loan Type, Borrower A→Z

**Each loan row shows (tabbed grid alignment):**
- Loan # | Borrower | Status | Lock badges | Close/Lock dates | Progress bar | %
- Closing date and lock expiry labeled and right-aligned in their own column
- **Order-out badges** always visible on every row: `○ HOI` / `⏳ HOI` / `✓ HOI` for HOI, Title, and Appraisal — gray (not sent), amber (requested), green (received)

**📋 Notes & Conditions panel (inline expand per loan):**
- Loan notes
- All conditions with color-coded status badges
- Status History — every manual status change with timestamp and user

**📄 Docs & Contacts panel (inline expand per loan):**
- Generate HOI / Title request docs
- Contact cards for insurance and title with 📞 phone, ✉ email, and 📬 Gmail compose button
- **Order Status** section — three dropdowns (HOI | Title | Appraisal) cycling Not Sent → Requested → Received. Updates save instantly, log to activity trail with user + timestamp, and reflect immediately on the row badges

**📋 Notes & Conditions panel:**
- Each outstanding condition shows a **📧 Remind** button — looks up the party's email (Borrower, Title, etc.) and opens Gmail pre-filled with a professional reminder about that specific condition

**Pipeline area is scrollable** — fills ~75% of viewport height. Loans stay visible without needing to scroll the whole page.

**Per-loan detail view:**
- Status change, folder open, notes, assignment
- Share with teammates, send updates
- **Interactive conditions** — each condition has:
  - Checkbox to mark complete
  - Status buttons (Important / Needed / Requested / Ready to Clear / Cleared)
  - Party multiselect (Borrower, Title, Appraiser, etc.)
  - Notes field
  - Fetch from Folder — search borrower's folder for matching files
  - Check Guidelines — search Fannie/Freddie for relevant sections
  - Find & Analyze Bank Stmt — auto-appears on bank-related conditions
- **Email Draft section** — below conditions:
  - Pick a party from dropdown (auto-populated from stored contacts on this loan)
  - Contact name + email auto-displays when a known party is selected
  - "To: email@address.com" pre-filled if email is stored
  - Draft Email or Draft with AI buttons
- Contact management (borrower, title, agents) — every contact card shows name, phone, email, and a **📬 Gmail** button that opens a pre-addressed compose window
- Activity log with timestamped history
- Lock expiry and closing date countdown

**Upcoming Deadlines** — sidebar widget showing loans with approaching lock/closing dates, sorted by urgency.

**Filtering:** by status, search by loan number or borrower name, "My Loans" toggle.

**Inbox:** Shared loans appear as a banner at the top. Accept or dismiss.

**Removed Loans:** Configurable retention (7-90 days or forever). Restore or permanently delete.

**Auto-overdue:** Loans past due date automatically flagged on page load.

---

### 3. My Team
One-time setup for private loan sharing. No server. No hub.

1. Set your inbox folder path
2. Add teammates: name, role, their inbox path
3. Green dot = reachable. Red dot = unreachable or wrong path.

**How sharing works:**
1. Share on any loan — pick teammates — Share Now
2. App writes JSON directly into each person's inbox folder
3. They accept from their Inbox banner
4. They work on the loan, update status/notes
5. Send Update pushes changes back
6. You accept the update — changes sync

**Activity notifications:**
When a shared loan is opened, updated, or has a status change, a lightweight notification is dropped into every shared member's inbox automatically. Notifications appear in a 🔔 banner in the Team page — shows who did what, on which loan, and when. Dismiss individually with ✕.

Works over office WiFi, mapped network drives, or shared OneDrive subfolders.

---

### 4. Email Watch
Auto-checks your inbox for new PDF attachments, verifies each one, stages for review.

**Sidebar nav:** Email Watch is a top-level section with two sub-pages — **Controls** (setup, start/stop, credentials) and **Results** (live match queue with attachment count badge). Monitor incoming attachments while still working in Pipeline or Scanner.

**Setup:** Pick provider (Gmail/Outlook/Yahoo/Custom), enter email and App Password, set check interval, save and start.

**What happens:** Downloads attachment to `incoming/`, runs Quick Doc Verify, queues a review card. You see it in Email Watch, Quick Verify, and the sidebar indicator.

**Actions:** Click the 🖼️/📄/📋 **Preview** icon to expand an inline preview (images render directly, PDFs embed, text/CSV shows the first 3,000 chars). Then Save to folder, Download, Open in Reader, or Dismiss. Nothing auto-saves.

---

### 5. Document Reader
Browse any local folder and read any PDF without uploading to the scanner.

- Paste folder path, browse, open any file
- Jump to any page or search by keyword
- Launchable directly from Quick Verify and bank statement results

---

### 6. My History
Available when logged in (not Sandbox). Shows all past document scans saved to the local database — date, doc type, conditions extracted, bank rules, risk flags.

---

### 7. Sandbox Mode
No account needed. Uploaded documents are not saved. Non-sensitive extracted loan data and recent scan history/cache may persist for continuity. Good for demos or evaluation.

---

### 8. Settings
Configure optional AI backends and app preferences.

**Cloud AI** — Connect Anthropic Claude or OpenAI for enhanced document analysis, smarter email drafting, and AI-powered condition extraction. Requires API key and internet.

**Ollama (Local LLM)** — Connect to a locally running Ollama instance for AI features with local model support.

**AI Router** — Automatically routes AI requests to the best available backend (Cloud > Ollama > Local fallback engine). Falls back gracefully.

**Billing** — Track monthly scan usage per user against pricing tiers.

---

## AI BACKENDS

Pipeline Manager works in three modes:

| Mode | Requirements | What it does |
|---|---|---|
| **Local fallback** | Nothing extra | Full app with regex-based extraction, pattern matching, rule engines |
| **Ollama (local LLM)** | Ollama installed + running locally | Enhanced extraction, smarter drafting, local AI support |
| **Cloud AI** | API key + internet | Anthropic Claude or OpenAI for highest-quality AI features |

The AI router (`ai_router.py`) manages backend selection and fallback. You can configure priority in the Settings page. The local fallback engine is always available as the final fallback.

---

## TEAM SETUP — Processor + Loan Officer working together

Anyone on the team can create a loan. You choose exactly who to share each one with.

**One-time per person:**
1. Sign Up with name and role
2. Go to My Team
3. Set your inbox folder path
4. Add each teammate: name, role, their inbox path

**Day-to-day workflow:**

| Who | Action |
|---|---|
| LO creates a loan | Adds it in Pipeline, shares with processor |
| Processor receives it | Opens app, sees Inbox banner, Accept |
| Processor works it | Updates status, marks conditions, adds notes |
| Processor sends update | Clicks Send Update |
| LO checks progress | Opens app, accepts update, sees changes |
| Either adds more people | Share again, add manager or underwriter |

---

## COMMON TASKS

### "I just got an approval letter"
1. Document Scanner — upload — auto-detects as Approval Letter — Scan
2. Review conditions (sorted by priority)
3. Check borrower conditions — pick language — Draft Email — copy to Outlook
4. Check title conditions — send to Title — Draft Email — copy to Outlook
5. Add to Pipeline with a due date

### "I need to scan multiple docs at once"
1. Document Scanner — Bulk Upload tab — drop all files
2. Each file is auto-detected (no dropdown needed)
3. Duplicate files flagged before scanning
4. Same-type PDFs offered for merge into one
5. Click Scan All to process everything in one go

### "A borrower emailed me something — what is it?"
1. Email Watch picks it up automatically (if running)
   OR Document Scanner — Quick Verify — drop the PDF
2. Verdict card shows: type, pages, date age, pipeline match
3. Save to folder or Dismiss

### "The approval asks for bank statements — do I already have them?"
1. Open the condition in loan detail — it has a Find & Analyze Bank Stmt button
2. Paste folder path (auto-fills) — Search
3. Click Analyze on any result for full 50-rule analysis

### "I need to scan a bank statement"
1. Document Scanner — upload — auto-detects as Bank Statement — Scan
2. Account Summary card: name, account number, institution, period, beginning/ending balance
3. 50 rules checked: Pass / Flag / Missing / Info / Manual

### "I got a 1003 and need borrower info"
1. Document Scanner — upload — select 1003 Application — Scan
2. Two-column field panel shows everything extracted
3. Red dots = missing. Push to Pipeline in one click.

### "I got a purchase contract"
1. Document Scanner — upload — select Purchase Contract — Scan
2. Three-column panel: parties, transaction, agents, contingencies
3. Draft Title Email generates a ready-to-send email

### "What does Fannie Mae say about this condition?"
1. Open the condition in loan detail or scanner — Check Guidelines
2. Exact Fannie/Freddie sections with page numbers

### "I need to email conditions in Spanish"
1. Scan the approval letter — check conditions — Language: Spanish — Draft Email

### "I want to email a party on a loan"
1. My Pipeline — open loan detail — scroll to Email Draft section
2. Pick the party (Borrower, Title, etc.) — stored contacts auto-fill name + email
3. Draft Email or Draft with AI

### "I want to share this loan"
1. My Pipeline — find the loan — Share — pick teammates — Share Now

### "I need to check a document for fraud indicators"
1. Document Scanner — upload W-2, pay stub, or bank statement
2. Fraud check runs automatically, flags 2+ indicators

### "I need to export conditions"
1. After scanning, use the CSV export for spreadsheet data
2. Or generate an HTML snapshot report for printing/sharing

---

## TROUBLESHOOTING

| Problem | Fix |
|---|---|
| **App won't start — streamlit not found** | Run `pip install streamlit` then try again. Or use `python -m streamlit run app.py` |
| **"No specific conditions found"** | PDF is a scanned image. Open in Adobe Acrobat — Tools — Recognize Text, then re-upload. |
| **Bank statement shows conditions instead of analysis** | Make sure you selected Bank Statement as the document type before scanning |
| **Bank statement Account Summary shows blanks** | PDF may be image-only with no text layer. Try OCR first. Scanned statements won't extract. |
| **Quick Verify shows "unknown" for doc type** | PDF may be image-only with no text layer. Try OCR first. |
| **Email Watch says "Login failed"** | Use an App Password, not your real password. Follow setup steps in Email Watch page. |
| **Email Watch says "Connection refused"** | Enable IMAP access in your email provider settings. |
| **Share button says "not in team list"** | Go to My Team and add that person with their inbox folder path. |
| **Teammate's inbox shows red dot** | Their machine is unreachable or the path is wrong. |
| **Fetch finds nothing** | Folder may have image PDFs with no text. Try "All PDFs" scope or search parent folder. |
| **Guidelines indexing freezes** | Reopen at http://localhost:8501, click Check Guidelines again — resumes from cache. |
| **Port 8501 already in use** | Another Streamlit is running. Ctrl+C in that terminal, or use `--server.port 8502` |
| **pipeline.json got wiped** | Run `git checkout pipeline.json` to restore last committed version. |
| **Ollama not connecting** | Make sure Ollama is running locally (`ollama serve`). Check Settings page for connection status. |
| **Cloud AI not working** | Verify your API key in Settings. Check internet connection. The app uses local fallback tools automatically. |
| **Duplicate file warning on upload** | Two identical files were uploaded. Remove the duplicate before scanning. |

---

## SAVING & PUSHING TO GITHUB

Your code is at: `https://github.com/145brice/Processor-Assistant`

```
cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
git add .
git commit -m "describe what changed"
git push
```

**What gets saved to GitHub:**
- All `.py` files (app, ai_engine, ai_router, cloud_client, ollama_client, doc_verify, email_watch, crm, billing, fraud_check, export, folder_search, guidelines, sharing, db, prompts, test_extraction)
- `pipeline.json` (loan data)
- `team.json` (team roster)
- `README.md`, `SETUP.md`, `requirements.txt`

**What does NOT get saved (stays local only):**
- `email_config.json` — email credentials (never push this)
- `ai_config.json` — API keys for cloud AI (never push this)
- `processor.db` — login accounts (recreate on a new machine)
- `incoming/` — downloaded email attachments (temporary staging)
- `guidelines_index/` — Fannie/Freddie cache (too large, rebuilt automatically)
- `.env` — environment variables (if used)

---

## WHAT RUNS LOCALLY vs WHAT NEEDS INTERNET

| Feature | Status |
|---|---|
| Scan any mortgage PDF | Online workspace with local fallback |
| Quick Doc Verify (type, pages, dates, borrower match) | Online workspace with local fallback |
| Auto-detect doc type on upload | Online workspace with local fallback |
| Duplicate file detection on bulk upload | Online workspace with local fallback |
| PDF merge for same-type multi-page docs | Online workspace with local fallback |
| Bank statement 50-rule analysis | Online workspace with local fallback |
| Bank statement Account Summary extraction | Online workspace with local fallback |
| Fraud check (W-2, pay stub, bank statement) | Online workspace with local fallback |
| Draft email — English + Spanish, all 6 recipient types | Online workspace with local fallback |
| Condition export (CSV + HTML snapshot) | Online workspace with local fallback |
| Fetch from folder / Find bank statements | Online workspace with local fallback |
| Check Fannie/Freddie Guidelines | Online workspace with local fallback |
| Document Reader | Online workspace with local fallback |
| My Pipeline (compact, scrollable, Excel-thin rows) | Online workspace with local fallback |
| Interactive conditions in loan detail | Online workspace with local fallback |
| Email Draft in loan detail (auto-fill from stored contacts) | Online workspace with local fallback |
| 1003 field extraction | Online workspace with local fallback |
| Purchase Contract extraction + title email | Online workspace with local fallback |
| Team sharing (loan handoff between teammates) | Online workspace |
| Login / Signup | Online access |
| Email Watch (inbox polling) | Mail server connection |
| Ollama local LLM | Runs on your machine |
| Cloud AI (Claude / OpenAI) | Needs internet + API key |
| Push to GitHub | Needs internet (backup only — your choice) |

---

## PRIVACY

- PDFs you upload for scanning are **read in memory only** — never written to disk by this app.
- Email Watch downloads PDFs to your local `incoming/` folder — nothing goes to any cloud.
- Your email credentials are saved in `email_config.json` on your machine — never transmitted.
- API keys for cloud AI are stored in `ai_config.json` locally — never shared.
- Shared loans travel as JSON files directly between personal inbox folders — no central server.
- Your pipeline, history, activity logs, and team list are stored locally only.
- Fraud checks use local regex checks unless you explicitly use Cloud AI.
- Nothing leaves your computer except when you explicitly use Cloud AI or push to GitHub.
