# Processor Traien — Offline Mortgage Processing App

**100% offline. No cloud. No AI APIs. No internet required after setup.**
Runs on your local Windows machine. Opens in your browser like a website — but everything stays on your computer.
Built for mortgage processors, loan officers, processing managers, and their teams.

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
5. Log in with your account, or click **⚡ Try Sandbox** to explore without an account

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
5 packages. No API keys. No accounts. No `.env` file needed.

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
│
├── app.py                ← Main file. Every page, button, form, and layout lives here.
│                            Edit this file to change how anything looks or behaves.
│
├── ai_engine.py          ← The processing brain. No AI — pure Python regex + pattern matching.
│                            Reads PDFs, extracts conditions, drafts emails, runs the bank
│                            statement 50-rule analysis, detects risk flags, extracts contacts,
│                            parses 1003 applications, parses purchase contracts.
│
├── doc_verify.py         ← Quick Doc Verify engine. Figures out what type of document a
│                            PDF is, counts pages, extracts dates to check freshness, and
│                            fuzzy-matches borrower names against your pipeline.
│                            Used by both email_watch.py and the Quick Verify section in the UI.
│
├── email_watch.py        ← Email inbox watcher. Connects to Gmail/Outlook/Yahoo via IMAP,
│                            checks for unread emails with PDF attachments every N minutes,
│                            downloads them, runs doc_verify on each one, and queues a
│                            "Pending Review" card in the UI. Toggle on/off. No auto-save.
│
├── crm.py                ← Pipeline data layer. All create/read/update/delete for loans.
│                            Reads and writes pipeline.json. Auto-flags overdue loans.
│                            Supports created_by, assigned_to, and share_id fields per loan.
│
├── folder_search.py      ← Folder search engine. Walks every subfolder under a given path,
│                            fuzzy-matches filenames and PDF text content to condition keywords.
│                            Also has find_bank_statements() — filters specifically for bank
│                            statement PDFs by filename and content scoring.
│
├── guidelines.py         ← Fannie/Freddie index and search engine. Breaks the PDFs into
│                            overlapping 1,500-character chunks, caches them to disk as JSON,
│                            then does fuzzy keyword search per condition. First run takes
│                            2–5 minutes. Every run after is instant from cache.
│
├── sharing.py            ← Private loan sharing engine. Each user has a personal inbox folder.
│                            Sharing a loan = writing a JSON file into someone's inbox folder.
│                            No central hub. No one sees what they weren't shared on.
│
├── db.py                 ← Local SQLite database. Stores user accounts (name, role, password hash)
│                            and scan history. Creates processor.db automatically on first run.
│
├── prompts.py            ← Output templates — stacking order format, research link patterns,
│                            risk flag labels.
│
├── team.json             ← Your personal team roster. Auto-created when you add teammates.
│                            Stores: name, role, inbox folder path per person.
│
├── email_config.json     ← Email watch credentials. Created when you save settings in the
│                            Email Watch page. Stored locally — never sent anywhere.
│
├── pipeline.json         ← All loan pipeline data. Auto-created on first run. Comes pre-loaded
│                            with 7 sample loans showing all statuses. Replace with real loans.
│
├── processor.db          ← SQLite database file. Auto-created. Holds login accounts + history.
│
├── incoming/             ← Where email attachment PDFs land when Email Watch downloads them.
│                            Files sit here until you Save or Dismiss them from the UI.
│
├── guidelines_index/     ← Cache folder for Fannie/Freddie index. Auto-created.
│   ├── Fannie_Mae.json       Built on first "Check Guidelines" use (~2 min, 1,191 pages)
│   ├── Freddie_Mac.json      Built on first use (~5 min, 2,882 pages)
│   └── *.hash                Detects when the source PDFs have changed → rebuilds cache
│
├── requirements.txt      ← Full package list. Run: pip install -r requirements.txt
└── README.md             ← This file.
```

---

## THE EIGHT PAGES

---

### 1. 📋 Document Scanner
The main workhorse. Upload any mortgage PDF, and the app processes it based on what type it is.

#### Quick Verify (always at the top — use this first)
Before you even select a doc type, there's a **📥 Quick Verify** expander at the very top of the scanner. Drop any PDF here — no configuration needed. In seconds you get a full check:

**What Quick Verify checks automatically:**

| Check | What it does |
|---|---|
| **Doc type** | Reads the text, identifies the document from 14 known types (bank statement, pay stub, W-2, 1099, VOE, appraisal, 1003, purchase contract, approval letter, title doc, closing disclosure, credit report, insurance, loan estimate, tax return) |
| **Page count** | Counts pages and compares to type-specific minimums. Bank statements need 2+ pages. Appraisals need 8+. Flags if short. |
| **Date freshness** | Finds every date in the document, picks the newest one, calculates how old it is. Bank statements and pay stubs flagged if older than 30 days. Yellow if 31–60 days. Red if older. Other docs flagged at 90+ days. |
| **Borrower match** | Reads borrower names from the PDF text, fuzzy-matches against every loan in your pipeline. 80%+ = green match. 50–79% = yellow possible. Below 50% = no match. |

**Verdict card:**
- ✅ Green — all checks pass, high confidence — "Ready for review"
- ⚠️ Yellow — minor flag, probably right — "Double-check flagged items"
- 🔍 Red — needs attention before saving

**Action buttons (nothing saves without you clicking):**
- **💾 Save to folder** — copies the file to the matched borrower's pipeline folder. If no folder is set, you type the path yourself.
- **📋 Scan this doc** — promotes it to the full condition scanner below
- **📂 Open in Reader** — opens in Document Reader for manual review

When Email Watch is running, incoming email attachments also appear inside this expander — same verify card, same Save/Dismiss controls.

---

#### Full Document Scan (below Quick Verify)

1. Upload a PDF (or multiple PDFs)
2. Pick the **Document Type** from the dropdown
3. Click **🔍 Scan Document**

The app routes to different output depending on the document type:

---

**Approval Letter, CD, LE, Credit Report, COC, Broker Package → Condition Table**

Each condition is a compact, expandable row. Sorted by priority then party:
- 🔴 Important (top)
- 🟡 Needed
- 🟠 Requested
- 🟢 Ready to Clear
- 🔵 Cleared (moved to a separate section at the bottom)

Click any condition row to expand it:
- **Status buttons** — mark as Important / Needed / Requested / Ready to Clear / Cleared
- **Party multiselect** — assign Borrower + Title + Appraiser + anyone else at the same time
- **Notes field** — add updates, summaries, or follow-up reminders
- **📂 Fetch from Folder** — search the borrower's folder for files that might satisfy this condition
- **📋 Check Guidelines** — search Fannie/Freddie for guideline sections relevant to this condition
- **🏦 Find & Analyze Bank Stmt** — appears automatically on conditions that mention "bank statement," "deposit," or "2 months." Searches the folder for bank statement PDFs and runs the full 50-rule analysis inline.

**Draft Email (always visible above the condition list):**
- Check any conditions to include them
- Pick Language: English or Spanish
- Pick who to send to: Borrower, Title, Underwriter, Insurance, Closer, Appraiser
- Click **Draft Email** → professional ready-to-copy email appears instantly
- Copy and paste into Outlook
- Works for all 6 recipient types in both languages

---

**Bank Statement → 50-Rule Analysis**

Completely separate output — no conditions, no email draft. Runs 50 specific bank statement rules:

| Icon | Meaning |
|---|---|
| ✅ Green | Item confirmed in the statement |
| 🚩 Red | Problem found — NSF fee, overdraft, returned item, gambling transaction, crypto, foreign currency, charge-off, etc. |
| ⚠️ Yellow | Required item not found — account number, statement period, account holder name, etc. |
| ℹ️ Blue | Optional item found that may need a letter — large deposit, tax refund, pension income, etc. |
| 👁 Purple | Cannot determine from text extraction — must verify manually (handwritten alterations, digital formatting) |

Summary bar at top shows total count per category.

At the bottom of bank statement results: **📂 Fetch & Analyze Bank Statements from Folder**
- Paste a folder path (auto-fills from pipeline or last search)
- Scope: "Bank statements only" (filename-filtered, fast) or "All PDFs in folder"
- Results scored by how likely each file is to be a bank statement
- **Analyze** — runs full 50-rule check on that file inline
- **Read** — opens in Document Reader

---

**1003 Application → Structured Field Extraction**

Instead of conditions, you get a two-column organized field panel:

Left column:
- Borrower name, SSN, Date of Birth, Phone, Email
- Present Address, Previous Address
- Employer, Position, Employer Phone
- Years on Job, Years in Field, Base Monthly Income

Right column:
- Co-borrower name, SSN, Co-borrower Employer
- Loan Amount, Loan Purpose, Term, Interest Rate
- Property Address, Property Use

**Missing required fields** shown in a red bar at top (Name, SSN, Present Address, Employer, Loan Amount, Property Address).

Green dot = found. Red dot = not found in this PDF.

**➕ Push to Pipeline** — one-click creates a tracked loan from the extracted data.

---

**Purchase Contract → Structured Field Extraction**

Three-column layout:

Left column (Parties):
- Buyer name, phone, email
- Seller name, phone
- Property address

Center column (Transaction + Title):
- Purchase price, Closing date, Earnest money, Down payment
- Seller concessions
- Title company name, contact, phone

Right column (Agents):
- Listing agent name, brokerage, phone, email
- Selling/buyer's agent name, brokerage, phone, email

Below that:
- Inspection contingency, Appraisal contingency, Financing contingency
- Addendums / Riders list

**Action buttons:**
- **➕ Push to Pipeline** — creates a loan pre-filled with buyer name and closing date
- **✉️ Draft Title Email** — generates a ready-to-copy email to the title company with all transaction details filled in (property address, buyer, seller, price, closing date, request for commitment/CPL/wiring instructions)

---

### 2. 🗂️ My Pipeline
Your loan tracking board. Works like an offline Arrive or LendingPad.

**Status colors:**
- 🔴 Pending — waiting on borrower or docs, nothing sent yet
- 🟠 Requested — docs requested, waiting on response
- 🟢 Cleared — all conditions met, ready to close
- ⚫ Overdue — past due date, auto-flagged on page load
- ✅ Closed — funded and done

**Each loan card shows:**
- Loan number · Borrower name · Status badge
- Who created it · Who it's assigned to
- Due date · Missing docs summary

**Per-loan actions:**
- **✅ Cleared / 📤 Requested / ⏰ Overdue** — one-click status change
- **📂 Open Folder** — opens the borrower's folder in Windows File Explorer
- **Notes** — type anything, save it
- **Assign To** — reassign to any teammate from your team list
- **🔗 Share** — share this loan with specific teammates (see Team Sharing below)
- **📤 Send Update** — push your latest changes back to the loan owner and everyone shared on it
- **🗑️ Remove** — permanently deletes from pipeline

**Filtering:**
- Filter by status dropdown
- Search by loan number or borrower name
- ☑ My Loans — show only loans you created or are assigned to

**📬 Inbox:** When a teammate shares a loan with you, a banner appears at the top of the Pipeline page showing how many loans are waiting. Each card shows the loan details, who shared it, and gives you Accept or Dismiss.

**Auto-overdue:** Any loan whose due date has passed and isn't Cleared or Closed gets automatically flagged Overdue every time the page loads.

---

### 3. 👥 My Team
One-time setup for private loan sharing. No server. No hub.

**Step 1 — Set your inbox folder:**
This is the folder where teammates drop shared loans for you. Copy this path and give it to anyone who needs to share with you.
Example: `C:\Users\YourName\GopherInbox` or `\\OFFICE-SERVER\Shared\YourName`

**Step 2 — Add teammates:**
For each person on your team, add:
- Their name
- Their role (Processor / Loan Officer / Jr Underwriter / Manager)
- Their inbox folder path (they get this from their own Team page)

Green dot next to a teammate = their inbox folder is reachable right now.
Red dot = their machine is offline or the path is wrong.

**How sharing works (completely private, no central server):**
1. You click **🔗 Share** on any loan → pick teammates → **Share Now**
2. App writes a JSON file directly into each person's inbox folder
3. They open the app → **📬 Inbox** at the top of Pipeline → **✅ Accept**
4. They work on the loan, update status/notes
5. They click **📤 Send Update** → file goes back into your inbox
6. You accept the update → their changes sync into your pipeline

No one on the team has a master view of everyone's loans unless something was explicitly shared with them. Works over office WiFi (`\\JANE-PC\GopherInbox`), a mapped network drive, or shared OneDrive subfolder.

---

### 4. 📧 Email Watch
Auto-checks your inbox for new PDF attachments, verifies each one, and stages it for your review.

**One-time setup:**
1. Go to **📧 Email Watch** → expand **⚙️ Email Credentials**
2. Pick your provider (Gmail / Outlook / Yahoo / Custom)
3. Enter your email address
4. Enter your **App Password** — this is NOT your real password:
   - **Gmail:** myaccount.google.com → Security → 2-Step Verification → App Passwords → Mail → Windows Computer → Generate → copy the 16-character code
   - **Outlook:** account.microsoft.com → Security → Advanced security → App passwords
5. Pick check interval: 2 / 5 / 10 / 15 / 30 minutes
6. Click **Save Credentials**
7. Click **▶ Start Watching**

**What happens when a PDF arrives:**
1. App connects to your inbox, downloads the attachment to the `incoming/` folder, disconnects
2. Runs Quick Doc Verify: identifies doc type, counts pages, checks date freshness, matches borrower name to pipeline
3. Queues a Pending Review card — you see it in:
   - The **📬 Email Watch** page
   - The **📥 Quick Verify** section in Document Scanner (auto-opens)
   - The sidebar status indicator

**Each card shows:**
- Filename, sender, time received
- ✅ Passed checks (green list)
- ⚑ Flagged items (red list)
- Pipeline match: borrower name, loan number, confidence %

**Actions (nothing auto-saves):**
- **💾 Save to folder** — copies file to the matched borrower's pipeline folder
- **Open in Reader** — read it before deciding
- **Dismiss** — delete the card, file stays in `incoming/`

**Sidebar indicator:**
- `🟢 Watching · 2:34 PM` — running, shows last check time
- `⚫ Inbox watch off` — stopped
- Purple badge shows how many attachments are waiting for action

**Toggle:** One button starts and stops the watcher. When stopped, the background thread exits within a few seconds — no more inbox access at all.

---

### 5. 📂 Document Reader
Browse any local folder and read any PDF — without uploading it to the scanner.

**How to use:**
1. Paste folder path → **Browse Folder** → file list appears
2. Pick a file → **Open & Read**

**Read mode (no search term):** Jump to any page number, read full text of that page.
**Search mode (type a keyword):** Every matching page shown with surrounding context. Good for: `appraisal`, `HOA`, `verification of mortgage`, any condition keyword.

Can be launched directly from Quick Verify results or bank statement fetch results — click **Read** to open that specific file instantly.

---

### 6. 🕑 My History
Available when logged in (not in Sandbox). Shows all past document scans saved to the local database — date, doc type, conditions extracted, bank rules, risk flags.

---

### 7. ⚡ Sandbox Mode
No account needed. Full access to every feature except scan history. Nothing is saved between sessions. Good for demos or trying things out.

---

## TEAM SETUP — Processor + Loan Officer working together

Anyone on the team can create a loan. You choose exactly who to share each one with. No one sees what they weren't shared on.

**One-time per person:**
1. Sign Up → enter your name and role
2. Go to **👥 My Team**
3. Set your inbox folder path
4. Add each teammate: name, role, their inbox path
5. Done — sharing is now one click from any loan

**Day-to-day workflow:**

| Who | Action |
|---|---|
| LO creates a loan | Adds it in Pipeline → clicks 🔗 Share → picks their processor → Share Now |
| Processor receives it | Opens app → sees 📬 Inbox banner → Accept |
| Processor works it | Updates status, marks conditions, adds notes |
| Processor sends update | Clicks 📤 Send Update |
| LO checks progress | Opens app → 📬 Inbox → Accept update → sees exactly what changed |
| Either one adds more people | Clicks 🔗 Share again, adds manager or underwriter |

---

## COMMON TASKS — Step by step

### "I just got an approval letter"
1. **📋 Document Scanner** → upload → select **Approval Letter** → **Scan**
2. Review conditions (sorted red → yellow → orange → green)
3. Check Borrower conditions → Language: English or Spanish → **Draft Email** → copy to Outlook
4. Check Title conditions → Send to: Title → **Draft Email** → copy to Outlook
5. Add to **🗂️ My Pipeline** with a due date

### "A borrower emailed me something — what is it and does it belong to an open loan?"
1. Email Watch picks it up automatically (if toggle is on)
   OR go to **📋 Document Scanner** → **📥 Quick Verify** → drop the PDF
2. Verdict card shows: what type it is, how many pages, how old the dates are, which borrower it matches
3. Click **💾 Save to folder** to put it in the right place — or **Dismiss** if it's junk

### "The approval asks for bank statements — do I already have them?"
1. Open the condition that mentions bank statements → expand it
2. Click **🏦 Find & Analyze Bank Stmt**
3. Paste the borrower's folder path (auto-fills from last search or pipeline)
4. Click **Search** → app finds all bank statement PDFs in that folder
5. Click **Analyze** on any result → full 50-rule analysis runs right there
6. Or click **Read** to open it in Document Reader first

### "I need to scan a bank statement I received"
1. **📋 Document Scanner** → upload → select **Bank Statement** → **Scan**
2. Results show all 50 rules: ✅ Pass / 🚩 Flag / ⚠️ Missing / ℹ️ Info / 👁 Manual
3. Red flags (NSF, overdraft, crypto, gambling, returned items) are highlighted immediately

### "I got a 1003 and need to pull all the borrower info"
1. **📋 Document Scanner** → upload → select **1003 Application** → **Scan**
2. Two-column field panel shows everything extracted: name, SSN, DOB, phone, email, address, employer, income, loan amount, property
3. Red dots show what's missing from the PDF
4. Click **➕ Push to Pipeline** to create a tracked loan from the data

### "I got a purchase contract and need to email the title company"
1. **📋 Document Scanner** → upload → select **Purchase Contract** → **Scan**
2. Three-column panel shows all parties, transaction terms, title company, agents, contingencies
3. Click **✉️ Draft Title Email** → ready-to-send email pre-filled with all transaction details

### "What does Fannie Mae say about this condition?"
1. Open the condition in the scanner → expand it → click **📋 Check Guidelines**
2. Results show exact Fannie/Freddie sections with page numbers

### "I need to email conditions in Spanish"
1. Scan the approval letter → check the conditions → set Language: **Spanish** → **Draft Email**

### "I want to share this loan with my loan officer manager"
1. **🗂️ My Pipeline** → find the loan → click **🔗 Share** → pick from your team list → **Share Now**

### "My processor updated a loan — how do I see it?"
1. Open the app → **🗂️ My Pipeline** → look for the **📬 Inbox** banner at the top
2. Click **✅ Accept** on the update

---

## TROUBLESHOOTING

| Problem | Fix |
|---|---|
| **App won't start — streamlit not found** | Run `pip install streamlit` then try again. Or use `python -m streamlit run app.py` |
| **"No specific conditions found"** | PDF is a scanned image (photographed, not digital text). Open in Adobe Acrobat → Tools → Recognize Text, then re-upload. |
| **Bank statement shows conditions instead of analysis** | Make sure you selected **Bank Statement** as the document type before clicking Scan |
| **Quick Verify shows "unknown" for doc type** | The PDF may be image-only with no text layer. Try OCR in Adobe first. Or the doc type isn't in the 14-type list — use full scan instead. |
| **Email Watch says "Error: Login failed"** | You're using your real email password instead of an App Password. Follow the Gmail/Outlook App Password setup steps in the Email Watch page. |
| **Email Watch says "Error: connection refused"** | Gmail/Outlook may have IMAP disabled. Go to email settings → Enable IMAP access. |
| **Share button says "not in team list"** | Go to **👥 My Team** and add that person with their inbox folder path. |
| **Teammate's inbox shows red dot** | Their machine is offline, or the path you saved for them is wrong. Ask them for their correct inbox path from their Team page. |
| **Fetch finds nothing** | Folder may contain image PDFs with no text layer. Try switching scope to "All PDFs" or searching a parent folder. |
| **Guidelines indexing freezes** | Reopen at http://localhost:8501, click Check Guidelines again — it resumes from the cache where it left off. |
| **Port 8501 already in use** | Another Streamlit is running. Press Ctrl+C in that terminal, or run with `--server.port 8502` |
| **pipeline.json got wiped** | Run `git checkout pipeline.json` to restore the last committed version. |
| **Duplicate file key error** | You uploaded the same PDF filename twice in the same session. Remove one from the uploader. |

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
- All `.py` files (app, ai_engine, doc_verify, email_watch, crm, folder_search, guidelines, sharing, db, prompts)
- `pipeline.json` (your loan data)
- `team.json` (your team roster)
- `README.md` + `requirements.txt`

**What does NOT get saved (stays local only):**
- `email_config.json` — your email credentials (never push this)
- `processor.db` — login accounts (recreate on a new machine)
- `incoming/` — downloaded email attachments (temporary staging)
- `guidelines_index/` — Fannie/Freddie cache (too large, rebuilt automatically)

---

## WHAT'S OFFLINE vs WHAT NEEDS INTERNET

| Feature | Status |
|---|---|
| Scan any mortgage PDF | ✅ 100% offline |
| Quick Doc Verify (type, pages, dates, borrower match) | ✅ 100% offline |
| Bank statement 50-rule analysis | ✅ 100% offline |
| Draft email — English + Spanish, all 6 recipient types | ✅ 100% offline |
| Fetch from folder / Find bank statements | ✅ 100% offline |
| Check Fannie/Freddie Guidelines | ✅ 100% offline (after PDFs placed on Desktop) |
| Document Reader | ✅ 100% offline |
| My Pipeline | ✅ 100% offline |
| 1003 field extraction | ✅ 100% offline |
| Purchase Contract field extraction + title email | ✅ 100% offline |
| Team sharing (loan handoff between teammates) | ✅ 100% offline (needs same network or shared drive) |
| Login / Signup | ✅ 100% offline (local SQLite) |
| Email Watch (inbox polling) | ✅ Offline — uses your local IMAP connection, no cloud |
| Push to GitHub | ❌ Needs internet (backup only — your choice) |

---

## PRIVACY

- PDFs you upload for scanning are **read in memory only** — never written to disk by this app.
- Email Watch downloads PDFs to your local `incoming/` folder — nothing goes to any cloud.
- Your email credentials are saved in `email_config.json` on your machine — never transmitted.
- Shared loans travel as JSON files directly between personal inbox folders — no central server.
- Your pipeline, history, and team list are stored locally only.
- Nothing leaves your computer except when you push to GitHub (your choice, your repo).
