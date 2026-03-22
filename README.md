# Processor Traien — Offline Mortgage Processing App

**100% offline. No cloud. No API keys. No internet after setup.**
Runs on your local Windows machine using Python + Streamlit (opens in your browser).
Built for mortgage processors, loan officers, and their teams.

---

## QUICK START — How to run it every time

1. Open **VS Code**
2. Open the terminal: press `` Ctrl+` ``
3. Make sure you're in the right folder:
   ```
   cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
   ```
4. Run:
   ```
   streamlit run app.py
   ```
5. Browser opens automatically at **http://localhost:8501**
6. Log in or click **⚡ Try Sandbox** to get started instantly.

To stop the app: press `Ctrl+C` in the terminal.

---

## FIRST-TIME SETUP (do this once)

### Step 1 — Make sure Python is installed
Open Command Prompt and type:
```
python --version
```
You should see `Python 3.10.x` or higher. If not, download Python from python.org.

### Step 2 — Install dependencies
```
pip install streamlit pypdf thefuzz python-Levenshtein python-dotenv
```
5 packages total. No API keys, no accounts, no .env file needed.

### Step 3 — Guideline PDFs (for "Check Guidelines")
Place these two files exactly on your Desktop:
```
C:\Users\user\OneDrive\Desktop\Fannie Mae.pdf
C:\Users\user\OneDrive\Desktop\Freddie Mac.pdf
```
- Filenames must match exactly (capital F, capital M, space between words).
- Download free from FannieMae.com and FreddieMac.com.
- If you don't have them, everything else works fine — just skip "Check Guidelines."

### Step 4 — Run it
```
streamlit run app.py
```

---

## FILE STRUCTURE — What every file does

```
Processor-Assistant/
│
├── app.py               ← MAIN FILE. All UI pages, navigation, buttons, layout.
│
├── ai_engine.py         ← The brain. Reads PDFs, extracts conditions, drafts emails,
│                           runs checklists, detects risk flags, bank statement analysis.
│                           No AI, no internet — pure Python regex + pattern matching.
│
├── crm.py               ← Pipeline database logic. Reads/writes pipeline.json.
│                           Handles add, update, delete, status changes, overdue detection.
│                           Supports created_by and assigned_to fields per loan.
│
├── folder_search.py     ← Folder search engine. Given a folder path + condition keywords,
│                           walks every subfolder, fuzzy-matches filenames and PDF content.
│                           Also includes find_bank_statements() for bank-specific searches.
│
├── guidelines.py        ← Fannie/Freddie search engine. Indexes the PDFs into chunks,
│                           caches the index, searches for relevant guideline sections.
│
├── sharing.py           ← Private loan sharing engine. Lets processors and LOs share
│                           specific loans directly via personal inbox folders — no central
│                           hub, no one sees what they weren't shared on.
│
├── db.py                ← Local SQLite user accounts + scan history.
│                           Stores name, role (Processor/LO/Manager), and login.
│                           Creates processor.db automatically on first run.
│
├── prompts.py           ← Output templates (stacking order, research links, risk labels).
│
├── team.json            ← Your personal team list. Auto-created when you add teammates.
│                           Stores each person's name, role, and inbox folder path.
│
├── pipeline.json        ← Your loan pipeline data. Auto-created. Edit directly if needed.
│                           Backed up every time you push to GitHub.
│
├── processor.db         ← SQLite database. Auto-created. Stores login accounts + history.
│
├── inbox/               ← Default local inbox folder for shared loans.
│                           Files dropped here by teammates appear in your Pipeline inbox.
│
├── guidelines_index/    ← Auto-created. Stores the Fannie/Freddie index cache.
│   ├── Fannie_Mae.json      (built on first "Check Guidelines" click — ~2 min)
│   ├── Freddie_Mac.json     (built on first click — ~5 min for 2,882 pages)
│   └── *.hash               (detects when PDFs have been updated)
│
├── requirements.txt     ← Run `pip install -r requirements.txt` to install all packages.
└── README.md            ← This file.
```

---

## THE SIX PAGES — What each does

---

### 1. 📋 Document Scanner
The main workhorse. Upload a PDF, extract every condition, act on them.

**How to use it:**
1. Click **📋 Document Scanner** in the sidebar
2. Drag and drop a mortgage PDF (approval letter, CD, 1003, bank statement, etc.)
3. Pick the **Document Type** from the dropdown
4. Click **🔍 Scan Document**

**For approval letters and most docs — Condition Table:**
- Each condition is a compact expandable row
- Click any condition to expand: status buttons, party assignment, notes, Fetch, Guidelines
- Condition status colors: 🔴 Important → 🟡 Needed → 🟠 Requested → 🟢 Ready to Clear → 🔵 Cleared
- Conditions auto-sort by status priority, then by responsible party
- Cleared conditions drop to a separate section at the bottom

**Draft Email (always visible at top):**
- Check any conditions you want included
- Pick Language (English or Spanish) and who to send to
- Click **Draft Email** → professional ready-to-copy email appears
- Works for: Borrower, Title, Underwriter, Insurance, Closer, Appraiser

**Inside each condition expander:**
- Status buttons (mark Important / Needed / Requested / Ready to Clear / Cleared)
- Party multiselect (assign Borrower + Title + Appraiser, etc. — multiple at once)
- Notes field (add any update or summary)
- **📂 Fetch from Folder** — search borrower's folder for matching documents
- **📋 Check Guidelines** — look up Fannie/Freddie guideline sections for that condition
- **🏦 Find & Analyze Bank Stmt** — appears automatically on conditions that mention bank
  statements, deposits, or "2 months." Searches the folder specifically for bank statement
  PDFs and runs the full 50-rule analysis right inside the condition.

**For Bank Statement doc type — 50-Rule Analysis:**
Selecting "Bank Statement" runs a completely separate analysis (not conditions):
- ✅ Green — item confirmed in the statement
- 🚩 Red — problem found (NSF, overdraft, returned item, crypto, gambling, etc.)
- ⚠️ Yellow — required item not found (account number, period dates, etc.)
- 🔵 Blue — optional item found that may need documentation (large deposit, tax refund, etc.)
- 👁 Purple — cannot determine from text; must verify manually

At the bottom of the bank statement results:
**📂 Fetch & Analyze Bank Statements from Folder**
- Paste borrower folder path (auto-filled from last search or pipeline)
- Scope: "Bank statements only" (fast, filename-filtered) or "All PDFs"
- Results ranked by how likely each PDF is to be a bank statement
- **Analyze** — runs full 50-rule check on that file inline
- **Read** — opens the file in Document Reader

---

### 2. 🗂️ My Pipeline
Color-coded loan tracking board. Works like an offline LendingPad or Arrive.

**Status colors:**
- 🔴 Pending — waiting on borrower or docs
- 🟠 Requested — docs requested, waiting on response
- 🟢 Cleared — all conditions met, ready to close
- ⚫ Overdue — past due date, auto-flagged
- ✅ Closed — funded and done

**Each loan shows:**
- Loan # · Borrower name · Status badge
- Who created it and who it's assigned to
- Due date · Missing docs

**Per-loan actions:**
- ✅ Cleared / 📤 Requested / ⏰ Overdue — one-click status change
- 📂 Open Folder — opens borrower's folder in File Explorer
- Notes field + Save Notes
- Assign To dropdown — reassign to any teammate
- 🔗 Share — share this loan privately with specific teammates
- 📤 Send Update — push your latest status back to the loan owner and shared team
- 🗑️ Remove — delete from pipeline

**Filtering:**
- Filter by status dropdown
- Search by loan number or borrower name
- ☑ My loans — show only loans assigned to or created by you

**📬 Inbox:**
When a teammate shares a loan with you, it appears at the top of the Pipeline page.
- ✅ Accept — adds it to your pipeline
- Dismiss — removes it from inbox without adding

**Auto-overdue:** Any loan past its due date that isn't Cleared or Closed gets flagged automatically on page load.

---

### 3. 👥 My Team
Set up private loan sharing with your teammates. One-time setup per person.

**Step 1 — Set your inbox folder:**
This is where teammates drop shared loans for you. Give this path to anyone who wants to share with you.
Example: `C:\Users\YourName\GopherInbox` or `\\OFFICE-NAS\Shared\YourName`

**Step 2 — Add teammates:**
For each person you work with, add:
- Their name
- Their role (Processor / Loan Officer / Jr Underwriter / Manager)
- Their inbox folder path (they copy this from their own Team page)

Green dot = their folder is reachable right now. Red dot = offline or wrong path.

**How sharing works (no central server, no hub):**
1. You add a loan to your pipeline → click **🔗 Share** → pick teammates → **Share Now**
2. The app writes one file directly into each person's inbox folder
3. They open their app → see "📬 Inbox — 1 loan waiting" → Accept
4. They make updates → click **📤 Send Update** → file goes back to your inbox
5. You accept the update — status syncs

Privacy: each person only sees loans shared with them specifically. No one has a view of the whole team's pipeline unless explicitly shared.

Works over office WiFi (`\\JANES-PC\GopherInbox`), a mapped network drive, or even a shared OneDrive subfolder.

---

### 4. 📂 Document Reader
Browse any local folder and read any PDF — without uploading to the scanner.

**How to use it:**
1. Paste folder path → **Browse Folder** → pick a file → **Open & Read**

**Read mode:** Jump to any page number, read full text.
**Search mode:** Type a keyword → every matching page shown with context.

You can also land here directly from a bank statement fetch result — click **Read** on any found file to open it instantly.

---

### 5. 🕑 My History
Available when logged in (not sandbox). Shows all past scans saved to the local database.

---

### 6. ⚡ Sandbox Mode
No account needed. Full access to all features except scan history. Results not saved between sessions.

---

## TEAM SETUP — For a processor + loan officer working together

This app works like an offline Arrive or LendingPad. Anyone on the team can create a loan. You share it with exactly who you want. No one else sees it.

**One-time setup (each person does this on their machine):**

1. Create an account (Sign Up → enter your name and role)
2. Go to **👥 My Team**
3. Set your inbox folder path (e.g. `C:\Users\Maria\GopherInbox`)
4. Add each teammate: their name, role, and their inbox path
5. That's it — sharing is one click from now on

**Day-to-day flow:**

| Who | Action |
|---|---|
| LO creates a loan | Adds it in Pipeline → clicks Share → picks their processor |
| Processor receives it | Opens app → sees inbox notification → accepts the loan |
| Processor works it | Updates status, marks conditions, adds notes |
| Processor sends update | Clicks "📤 Send Update" → LO sees new status in their inbox |
| LO checks progress | Opens app → accepts update → sees exactly what changed |

---

## COMMON TASKS — Step by step

### "I just got an approval letter. What do I do?"
1. **📋 Document Scanner** → upload the approval letter → select **Approval Letter** → **Scan**
2. Review the condition table (sorted by priority: red first, then yellow, orange, green)
3. Check Borrower conditions → set Language → **Draft Email** → copy to Outlook
4. Check Title conditions → set Send To: Title → **Draft Email** → copy to Outlook
5. Add the loan to **🗂️ My Pipeline** with a due date

### "The approval asks for bank statements. Do I already have them?"
1. Open the condition that mentions bank statements → expand it
2. Click **🏦 Find & Analyze Bank Stmt**
3. Paste the borrower's folder path (or it auto-fills from last search)
4. Click **Search** → app finds all bank statement PDFs in that folder
5. Click **Analyze** on any result → full 50-rule analysis runs right there
6. Or click **Read** to open the file in Document Reader

### "I need to scan a bank statement I received"
1. **📋 Document Scanner** → upload the bank statement PDF → select **Bank Statement** → **Scan**
2. Results show: ✅ Passed / 🚩 Flagged / ⚠️ Missing / ℹ️ Note / 👁 Manual review
3. Any red flags (NSF, overdraft, crypto, gambling, returned items) are highlighted immediately

### "What does Fannie Mae say about this condition?"
1. Open any condition in the scanner → expand it → click **📋 Check Guidelines**
2. Results show exact Fannie/Freddie sections with page numbers

### "I need to email conditions in Spanish"
1. Scan the document → check the conditions → set **Language: Spanish** → **Draft Email**

### "I want to share this loan with my loan officer"
1. **🗂️ My Pipeline** → find the loan → click **🔗 Share** → pick the LO from your team list → **Share Now**

### "My processor updated a loan — how do I see it?"
1. Open the app → **🗂️ My Pipeline** → look for the **📬 Inbox** banner at the top
2. Click **✅ Accept** on the update

---

## TROUBLESHOOTING

| Problem | What to do |
|---|---|
| **App won't start** | Run `pip install streamlit` then try again. Or `python -m streamlit run app.py` |
| **"No specific conditions found"** | PDF is a scanned image (photo, not digital text). Open in Adobe Acrobat → Tools → Recognize Text, then re-upload. |
| **Bank statement shows conditions instead of analysis** | Make sure you selected **Bank Statement** as the document type before clicking Scan. |
| **Spanish email shows English** | All party types support Spanish now. Make sure Language is set to Spanish before clicking Draft Email. |
| **Fetch finds nothing** | Folder may contain scanned/image PDFs with no text layer. Try switching scope to "All PDFs" or searching a parent folder. |
| **Share button says "not in team list"** | The person's inbox path isn't in your team.json yet. Go to **👥 My Team** and add them. |
| **Inbox shows a loan but Accept fails** | The shared file may be corrupted. Dismiss it and ask the sender to reshare. |
| **Guidelines indexing freezes** | Close the tab, reopen at http://localhost:8501, click Check Guidelines again — resumes from cache. |
| **Port 8501 already in use** | Another Streamlit is running. Press Ctrl+C in that terminal. Or run `streamlit run app.py --server.port 8502` |
| **pipeline.json got wiped** | Run `git checkout pipeline.json` to restore the last committed version. |

---

## SAVING & PUSHING TO GITHUB

Your code is connected to GitHub at: `https://github.com/145brice/Processor-Assistant`

```
cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
git add .
git commit -m "describe what changed"
git push
```

**What gets saved to GitHub:**
- All `.py` files (app, engine, crm, folder_search, guidelines, sharing, db, prompts)
- `pipeline.json` (your loan pipeline)
- `team.json` (your team roster)
- `README.md` + `requirements.txt`

**What does NOT get saved:**
- `processor.db` — local user accounts (recreate logins on a new machine)
- `inbox/` — shared loan files (these come from teammates, not stored in git)
- `guidelines_index/` — rebuilt automatically from the PDFs (too large for git)

---

## WHAT'S OFFLINE vs WHAT NEEDS INTERNET

| Feature | Status |
|---|---|
| Scan document (approval letter, CD, 1003, etc.) | ✅ 100% offline |
| Bank statement 50-rule analysis | ✅ 100% offline |
| Draft email (English + Spanish) | ✅ 100% offline |
| Fetch from folder / Find bank statements | ✅ 100% offline |
| Check Guidelines (Fannie/Freddie) | ✅ 100% offline (after PDFs placed on Desktop) |
| Document Reader | ✅ 100% offline |
| My Pipeline | ✅ 100% offline |
| Team sharing (via local network / inbox folders) | ✅ 100% offline (needs same network or shared drive) |
| Login / Signup | ✅ 100% offline (local SQLite) |
| Push to GitHub | ❌ Needs internet (backup only) |

---

## PRIVACY

- PDFs you upload are **read in memory only** — never written to disk.
- Shared loans travel as JSON files directly between personal inbox folders — no central server.
- Your pipeline, history, and team list are stored locally only.
- Nothing leaves your computer except when you push to GitHub (your choice).
