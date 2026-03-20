# Processor Traien — Mortgage Document Processing App

100% offline. No cloud, no AI API, no internet required after setup.
Runs on your local machine using Python + Streamlit.

---

## What It Does

A loan processor's job: read approval letters, extract conditions, figure out who's responsible, draft follow-up emails, find supporting documents, and verify against agency guidelines. This app automates all of that — offline, locally, lightweight enough for an HP EliteBook.

### Core Features

- **PDF Upload & Condition Extraction** — Upload a mortgage approval letter (or CD, LE, 1003, credit report, bank statement, COC, broker package). The engine reads the PDF text and extracts every condition into a clean table showing the condition description, responsible party, and status (Needed/Received/Cleared/Waived).
- **Supports Lender Condition-Code Format** — Automatically parses lender systems that output conditions with codes like `Underwriter WCR01`, `Closer WES03`, `Jr Underwriter WPR15`, `Manager WCL02`. Handles multi-line conditions, strips dates/metadata/junk, and keeps only the real actionable text.
- **Multi-Condition Email Drafting** — Check multiple conditions (as many as needed), pick a language (English or Spanish), pick a recipient (Borrower, Underwriter, Title, Closer, Insurance, Appraiser), and hit Draft Email. All selected conditions go into one combined email. Templates for every party type in both languages.
- **Fetch from Local Folder** — Select conditions, click "Fetch from Folder", paste the borrower's folder path. The app recursively searches that folder, fuzzy-matching filenames AND PDF content against your selected conditions. Returns organized results with match scores, page numbers, and text snippets.
- **Document Reader** — Browse any local folder, pick any file, and read it page by page or search inside it by keyword. Works on PDFs, TXT, and CSV files.
- **Sandbox Mode** — Free unlimited practice. No account needed, no data saved.
- **Local SQLite Database** — User accounts and scan history stored in a local `processor.db` file. No cloud database.
- **In-Memory Processing** — PDFs are processed in memory and never saved to disk. Only structured results are stored.

### On-Demand Analysis Tools

These run only when you trigger them (a la carte — no constant scanning, no CPU spikes):

- **250-Point Mega Checklist** — Compliance audit across 11 categories: loan type, property, HOA, insurance, title, borrower profile, income, assets, appraisal, disclosures, closing.
- **50-Rule Bank Statement Analysis** — Checks for overdrafts, NSF fees, large deposits, gambling transactions, crypto, foreign currency, dormant periods, and 44 more rules.
- **Risk Flags** — Scans for DTI over limits, low credit scores, high LTV, employment gaps, title issues, compliance problems. Severity rated HIGH/MEDIUM/LOW.
- **Contacts Extraction** — Pulls borrower names, phone numbers, emails, loan numbers, property addresses, loan type, interest rate from the document.
- **Stacking Order** — Generates a full loan file checklist (application, disclosures, credit, income, assets, property, government program docs, closing docs) with checkmarks for items found in the document.
- **Email Auto-Drafting** — Groups all conditions by responsible party and drafts separate emails for each.
- **Web Research Links** — Identifies conditions needing online verification and provides the specific URLs (FEMA flood lookup, FHA case number, NMLS, state SOS, county assessor, etc.). No web calls made — just gives you the links.
- **Check Guidelines (Fannie Mae / Freddie Mac)** — Select conditions, click "Check Guidelines." The engine searches through the full Fannie Mae Selling Guide (1,191 pages) and Freddie Mac Seller/Servicer Guide (2,882 pages) for sections relevant to each condition. Returns actual guideline text with page numbers, section references, and relevance scores. First run indexes the PDFs (~2-3 minutes), then loads from cache instantly.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit (Python web UI) |
| Processing Engine | Pure Python regex + pattern matching (no AI, no API) |
| PDF Parsing | pypdf (in-memory only) |
| Fuzzy Matching | thefuzz (pure Python, no C dependencies) |
| Database | SQLite (local file, no cloud) |
| Email Templates | Python string formatting (English + Spanish) |

**No API keys. No cloud accounts. No internet connection needed.**

---

## Project Structure

```
Processor-Assistant/
├── app.py              # Main Streamlit UI — upload, scan, conditions, emails,
│                       #   fetch, reader, guidelines, routing, sidebar
├── ai_engine.py        # Offline processing engine — condition extraction, risk flags,
│                       #   bank rules, contacts, stacking order, mega checklist, emails
├── folder_search.py    # Local folder search — fuzzy matches files to conditions
├── guidelines.py       # Fannie Mae / Freddie Mac guideline index + search engine
├── prompts.py          # Document type context (reference only)
├── db.py               # Local SQLite database — user accounts, scan history
├── requirements.txt    # Python dependencies (4 packages)
├── processor.db        # Created automatically on first run (SQLite database)
├── guidelines_index/   # Created automatically — cached guideline indexes (JSON)
└── README.md           # This file
```

---

## Setup — Step by Step

### Prerequisites

- **Python 3.10+** installed (check with `python --version`)
- **pip** package manager (comes with Python)
- **VS Code** (recommended) or any text editor
- **A web browser** (Chrome, Edge, Firefox)

### Step 1: Clone the Repository

Open a terminal (VS Code: press `` Ctrl+` ``) and run:

```bash
git clone https://github.com/145brice/Processor-Assistant.git
cd Processor-Assistant
```

Or if you already have the folder, just `cd` into it:

```bash
cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs 4 packages:
- `streamlit` — the web UI framework
- `pypdf` — reads PDF files
- `python-dotenv` — loads environment config (optional, kept for compatibility)
- `thefuzz` — fuzzy string matching for the folder search feature

That's it. No API keys, no `.env` file, no cloud setup.

### Step 3: Add Guideline PDFs (Optional but Recommended)

Place these files on your Desktop to enable the "Check Guidelines" feature:

- `Fannie Mae.pdf` — Fannie Mae Selling Guide (download from Fannie Mae's website)
- `Freddie Mac.pdf` — Freddie Mac Seller/Servicer Guide (download from Freddie Mac's website)

The app looks for them at:
```
C:\Users\<your-username>\OneDrive\Desktop\Fannie Mae.pdf
C:\Users\<your-username>\OneDrive\Desktop\Freddie Mac.pdf
```

On first click of "Check Guidelines", the app indexes both PDFs (takes 2-3 minutes for ~4,000 pages). After that, the index is cached in `guidelines_index/` and loads instantly on every future use.

### Step 4: Run the App

```bash
streamlit run app.py
```

The app opens automatically in your browser at **http://localhost:8501**.

If it doesn't open automatically, copy that URL and paste it into your browser.

### Step 4: Start Using It

1. Click **"Try Sandbox"** on the login page (no account needed)
2. Upload a mortgage PDF using the file uploader
3. Select the document type from the dropdown (e.g., "Approval Letter")
4. Click **"Scan Document"**
5. Review the extracted conditions table
6. Check conditions you want to act on
7. Click **"Draft Email"**, **"Fetch from Folder"**, or **"Check Guidelines"**

---

## How Each Feature Works

### Condition Extraction

When you upload a PDF and click Scan:

1. The PDF is read into memory using `pypdf` (never saved to disk)
2. Text is extracted page-by-page with gentle pauses between pages
3. The engine detects the format:
   - **Lender condition-code format**: Lines starting with `Underwriter WCR01`, `Closer WES03`, etc. are recognized as condition headers. Multi-line descriptions are assembled. Dates, status codes, and metadata are stripped. Only the actionable condition text is kept.
   - **Traditional format**: Numbered/bulleted lists under section headers like "Prior to Closing Conditions:" are captured line by line.
   - **Loan-number format**: Lines prefixed with long loan numbers (`5000002228902-`) are split and cleaned.
4. Junk is aggressively filtered: addresses, dollar amounts, email addresses, phone numbers, closing cost summaries, timestamps, company names, boilerplate footer text.
5. Each condition gets a responsible party assignment based on keywords (title, insurance, appraisal, underwriter, or defaults to Borrower).
6. Results display as a markdown table with checkboxes.

### Email Drafting

1. Check one or more conditions using the checkboxes
2. Pick a language (English or Spanish)
3. Pick a recipient from the dropdown (auto-populated from the selected conditions' parties)
4. Click **Draft Email**
5. A professional email is generated from templates with all selected conditions listed
6. Copy and paste into your email client

Templates exist for: Borrower, Title, Underwriter, Closer, Insurance, Appraiser — in both English and Spanish.

### Fetch from Folder

1. Check the conditions you need documents for
2. Click **"Fetch from Folder"**
3. Paste the full path to the borrower's folder (e.g., `C:\Loans\SmithJohn\`)
4. Click **Search**
5. The engine:
   - Walks the entire folder tree recursively
   - Checks every PDF and text file (skips executables, zips, etc.)
   - Fuzzy-matches each file's **name** against condition keywords
   - Opens each PDF and fuzzy-matches **page content** against condition keywords
   - Scores each match 0-100% using token-based and partial string matching
   - Pauses between files to stay gentle on CPU
6. Results show:
   - Green badge (80%+), Yellow (65-79%), Red (<65%) match confidence
   - File name and full path
   - Match type (filename, content, or both)
   - Matched page numbers within PDFs
   - Text snippet showing the matching content

Limits: 500 files max, skips files over 50MB, supports PDF and TXT content search.

### Document Reader

A separate tool (sidebar: **Document Reader**) for browsing and reading local files directly — no upload required.

1. Click **Document Reader** in the left sidebar
2. Paste the full path to any folder (borrower folder, shared drive, USB, wherever):
   ```
   C:\Users\YourName\Loans\Smith John\
   ```
3. Click **Browse Folder** — the app lists every readable file (.pdf, .txt, .csv) in that folder and all subfolders
4. Pick a file from the dropdown
5. Click **Open & Read**

**Page-by-page reading mode:**
- Use the page number input to jump to any page in a PDF
- Full extracted text appears in a scrollable text box

**Search mode (keyword search inside a document):**
- Type a keyword in the "Search inside document" box before clicking Open & Read (or while the file is open)
- The app scans every page and returns snippets with context around every match
- Example keywords: `appraisal`, `HOA`, `verification of mortgage`, `certificate of good standing`

Use the Reader to manually verify a document found by the Fetch tool, look up a specific detail in any file, or just read through a borrower document without leaving the app.

---

### Check Guidelines (Fannie Mae / Freddie Mac)

1. Check the conditions you want to look up
2. Click **"Check Guidelines"**
3. First time: the engine indexes both PDFs (~2-3 minutes for 4,000+ pages). Shows a progress bar. After indexing, the cache is saved to `guidelines_index/` and loads instantly on future runs.
4. The engine searches all 7,900+ indexed sections for content relevant to each selected condition
5. Results show per condition:
   - Source (Fannie Mae or Freddie Mac)
   - Page number and section reference (e.g., "Chapter 5202", "B3-5.3-09")
   - Relevance score with color badge
   - Actual guideline text excerpt (up to 500 chars)
6. Expand any condition to see up to 5 matching guideline references

How it works under the hood:
- PDFs are split into ~1,500-character overlapping chunks
- Each chunk is tagged with page number, source, and section ID
- Table-of-contents and boilerplate pages are filtered out
- Search uses topic detection (maps "hazard insurance" to insurance-related terms, "LLC" to entity terms, etc.)
- Fuzzy matching scores each chunk against condition keywords + related topic terms
- Results are deduplicated by page and sorted by relevance

### User Accounts

- **Sandbox mode**: Click "Try Sandbox" — unlimited free use, nothing saved
- **Create account**: Sign up with email + password. Stored locally in SQLite (hashed password). Scan history is saved.
- **Login**: Returns you to your saved history
- **Live mode**: Toggle in sidebar. Tracks file count and saves results to local database.

---

## Stopping the App

Press `Ctrl+C` in the terminal where Streamlit is running. Or just close the terminal.

To restart: `streamlit run app.py`

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `streamlit: command not found` | Run `pip install streamlit` again, or use `python -m streamlit run app.py` |
| PDF shows "could not extract enough text" | The PDF is likely a scanned image (picture of a document). This app needs text-based PDFs. OCR support is planned. |
| "No specific conditions found" | The PDF format may not match the expected patterns. The raw text preview at the bottom shows what was extracted — check if conditions are visible there. |
| App is slow on large PDFs | Normal — the engine pauses between pages to stay light on CPU. A 50-page PDF takes ~25 seconds. |
| Fetch results show low scores | Try a lower threshold or check that the folder actually contains the expected documents. Scanned/image PDFs won't have searchable text. |
| Duplicate key error | Don't upload the same filename twice in one session. Rename one copy first. |
| Port 8501 already in use | Another Streamlit instance is running. Kill it with `Ctrl+C` in that terminal, or use `streamlit run app.py --server.port 8502` |

---

## License

MIT
