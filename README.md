# Processor Traien — Mortgage Document Processing App

**100% offline. No cloud. No API keys. No internet after setup.**
Runs on your local Windows machine using Python + Streamlit (opens in your browser).

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
6. Click **Try Sandbox** — you're in. No login required.

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
In the project folder terminal:
```
pip install streamlit pypdf thefuzz python-Levenshtein python-dotenv
```
That's it — 5 packages total. No API keys, no accounts, no .env file needed.

### Step 3 — Guideline PDFs (for the "Check Guidelines" feature)
Place these two files exactly on your Desktop:
```
C:\Users\user\OneDrive\Desktop\Fannie Mae.pdf
C:\Users\user\OneDrive\Desktop\Freddie Mac.pdf
```
- The filenames must match exactly (capital F, capital M, space between words).
- These are the full Fannie Mae Selling Guide (1,191 pages) and Freddie Mac Seller/Servicer Guide (2,882 pages).
- Download them free from FannieMae.com and FreddieMac.com.
- **If you don't have them**, the rest of the app works fine — just skip "Check Guidelines."

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
│                           Edit this to change how anything looks or routes.
│
├── ai_engine.py         ← The brain. Reads PDFs, extracts conditions, drafts emails,
│                           runs checklists, detects risk flags, pulls contacts.
│                           No AI, no internet — pure Python regex + pattern matching.
│
├── crm.py               ← Pipeline database logic. Reads/writes pipeline.json.
│                           Handles add, update, delete, status changes, overdue detection.
│
├── folder_search.py     ← Folder search engine. Given a folder path + condition keywords,
│                           walks every subfolder, fuzzy-matches filenames and PDF content.
│
├── guidelines.py        ← Fannie/Freddie search engine. Indexes the PDFs into chunks,
│                           caches the index, searches for relevant guideline sections.
│
├── db.py                ← Local SQLite user accounts + scan history.
│                           Creates processor.db automatically on first run.
│
├── prompts.py           ← Output templates (stacking order, research links, risk labels).
│
├── pipeline.json        ← Your loan pipeline data. Auto-created. Edit directly if needed.
│                           Backed up every time you push to GitHub.
│
├── processor.db         ← SQLite database. Auto-created. Stores login accounts + history.
│
├── guidelines_index/    ← Auto-created folder. Stores the Fannie/Freddie index cache.
│   ├── Fannie_Mae.json      (built on first "Check Guidelines" click — takes ~2 min)
│   ├── Freddie_Mac.json     (built on first click — Freddie is ~2,882 pages, takes ~5 min)
│   └── *.hash               (used to detect when PDFs have been updated)
│
├── requirements.txt     ← Package list. Run `pip install -r requirements.txt` to install all.
└── README.md            ← This file.
```

---

## THE FOUR PAGES — What each does

### 1. 📋 Document Scanner
The main workhorse. Upload a PDF, extract every condition, then act on them.

**How to use it:**
1. Click **📋 Document Scanner** in the left sidebar
2. Drag and drop a mortgage PDF onto the uploader (approval letter, CD, 1003, etc.)
3. Pick the **Document Type** from the dropdown
4. Click **🔍 Scan Document**
5. The condition table appears — every condition extracted from the actual PDF text

**What you see in the condition table:**
- `#` — condition number
- `Condition` — the actual text from the PDF (not guessed — literally what's written)
- Responsible Party — color-coded badge: 🔵 Borrower, 🟣 Title, 🟠 Underwriter, 🟢 Insurance, 🟡 Closer
- Status — Needed / Received / Cleared / Waived

**After scanning — three action buttons appear:**

**Draft Email**
- Check any conditions you want (you can check 1 or 20 — they all go in one email)
- Pick Language: English or Spanish
- Pick who to send to (Borrower, Title, Underwriter, etc.)
- Click **Draft Email** → ready-to-copy professional email appears below
- Copy and paste into Outlook

**Fetch from Folder**
- Check conditions you need documents for
- Click **Fetch from Folder**
- Paste the borrower's full folder path, e.g.: `C:\Users\user\Loans\FishMartha\`
- Click **Search**
- App walks every subfolder, matches filenames AND PDF content to your conditions
- Results show match score (🟢 80%+, 🟡 65-79%, 🔴 below 65%), page numbers, and a text snippet

**Check Guidelines**
- Check conditions you want to look up in Fannie/Freddie
- Click **Check Guidelines**
- First time: indexes both PDFs (progress bar shown — takes a few minutes)
- Every time after: loads from cache in seconds
- Results show: source (Fannie or Freddie), page number, section code, and the actual guideline text

---

### 2. 🗂️ My Pipeline
Your color-coded loan tracking board. Every active loan in one place.

**Color key:**
- 🔴 **Pending** — waiting on borrower or docs, nothing sent yet
- 🟠 **Requested** — docs requested, waiting on response
- 🟢 **Cleared** — all conditions met, ready to close
- ⚫ **Overdue** — past due date, auto-flagged
- ✅ **Closed** — funded and done

**How to add a loan:**
1. Click **➕ Add Loan** at the top
2. Fill in: Loan #, Borrower Name, Status, Due Date, Missing Docs, Folder Path (optional)
3. Click **Save Loan**
4. It appears in the list immediately and is saved to `pipeline.json`

**Per-loan actions (buttons on each row):**
- **✅ Cleared** — marks the loan cleared (green)
- **📤 Requested** — marks as requested (orange)
- **⏰ Overdue** — marks as overdue (gray)
- **📂 Open Folder** — opens the borrower's folder in File Explorer (Windows only)
- **Notes** — type anything, click **Save Notes**
- **🗑️ Remove** — permanently deletes the loan from pipeline

**Filtering:**
- Use the **Filter by status** dropdown to show only Pending, Requested, etc.
- Use the **Search** box to find by loan number or borrower name

**Auto-overdue:** Any loan whose due date has passed and isn't Cleared or Closed gets automatically flagged Overdue when the page loads.

**Sample pipeline** is included — 7 realistic loans showing all 5 statuses so you can see how it looks right away. Replace them with your real loans any time.

---

### 3. 📂 Document Reader
Browse any local folder and read any file — without uploading it to the scanner.

**Use this when:**
- You want to look up something in a specific document
- You want to read through a borrower's file before scanning
- You fetched a document and want to read the actual pages

**How to use it:**
1. Click **📂 Document Reader** in the sidebar
2. Paste the full folder path, e.g.: `C:\Users\user\Loans\FishMartha\`
3. Click **Browse Folder** — all PDFs, TXTs, and CSVs in that folder are listed
4. Pick a file from the dropdown
5. Click **Open & Read**

**Read mode (no search term):**
- Use the page number input to jump to any page
- Full text of that page shows in a scrollable box

**Search mode (type a keyword first):**
- Type something in the "Search inside document" box
- Every page is scanned, and every match is shown with surrounding context
- Good for: `appraisal`, `HOA`, `verification of mortgage`, `certificate of good standing`, any condition keyword

---

### 4. 🕑 My History
Only available when logged in (not sandbox). Shows all past scans saved to the local database.

---

## COMMON TASKS — Step by step

### "I just got an approval letter. What do I do?"
1. Click **📋 Document Scanner**
2. Upload the approval letter PDF
3. Select **Approval Letter** from the Document Type dropdown
4. Click **🔍 Scan Document**
5. Review the condition table
6. Check all Borrower conditions → pick **English** or **Spanish** → click **Draft Email** → copy to Outlook
7. Check all Title conditions → pick **Title** → click **Draft Email** → copy to Outlook
8. Add the loan to **My Pipeline** with a due date so you don't forget it

### "I need to find if the borrower already sent me the appraisal"
1. Go to **📋 Document Scanner**, check the Appraisal condition
2. Click **Fetch from Folder**
3. Paste the borrower's folder path
4. Click **Search** — it finds any PDF with "appraisal" in the filename or content

### "What does Fannie Mae say about LLC vesting?"
1. Go to **📋 Document Scanner**, check the LLC/entity condition
2. Click **Check Guidelines**
3. Results show the exact Fannie Mae sections about entity vesting with page numbers

### "I want to read page 3 of a doc without uploading it"
1. Go to **📂 Document Reader**
2. Browse to the folder → open the file → set page to 3

### "I need to email conditions in Spanish"
1. Scan the document
2. Check the conditions you want to include
3. Set **Language** to **Spanish**
4. Set **Send to** to **Borrower**
5. Click **Draft Email**
6. Full professional Spanish email appears — copy to Outlook

---

## TROUBLESHOOTING

| Problem | What to do |
|---|---|
| **App won't start** — `streamlit: command not found` | Run `pip install streamlit` then try again. Or use `python -m streamlit run app.py` |
| **"No specific conditions found"** | The PDF is probably a scanned image. This app needs text-based PDFs (digitally created, not photographed). Open in Adobe Acrobat → Tools → Recognize Text, then re-upload. |
| **Spanish email shows English** | Make sure you selected "Borrower" as the recipient — all party types now have Spanish templates. |
| **Duplicate key error** | You uploaded the same PDF filename twice. Remove one from the uploader. |
| **Fetch finds nothing** | The folder may only have scanned/image PDFs (no text layer). Or the condition text is too generic. Try lowering the threshold or searching a parent folder. |
| **Guidelines indexing freezes** | Close the tab, reopen at http://localhost:8501, and click Check Guidelines again — it resumes from cache. |
| **Port 8501 already in use** | Another Streamlit is running. Press Ctrl+C in that terminal first. Or run `streamlit run app.py --server.port 8502` |
| **pipeline.json got wiped** | It's saved in the project folder. If git is set up, `git checkout pipeline.json` restores the last committed version. |

---

## SAVING & PUSHING TO GITHUB

Your code is connected to GitHub at: `https://github.com/145brice/Processor-Assistant`

**To save everything and push:**
```
cd "C:\Users\user\OneDrive\Desktop\processor-traien\Processor-Assistant"
git add .
git commit -m "your note here"
git push
```

**What gets saved to GitHub:**
- All `.py` files (app, engine, crm, search, guidelines, db, prompts)
- `pipeline.json` (your loan pipeline)
- `README.md`
- `requirements.txt`

**What does NOT get saved (excluded by .gitignore or just local):**
- `processor.db` (local user accounts — you'd need to recreate logins on a new machine)
- `guidelines_index/` folder (rebuilt automatically from the PDFs — no need to push 500MB of JSON)

---

## UPDATING THE APP

When you want to add features or fix bugs:
1. Make changes in VS Code
2. Test by running `streamlit run app.py`
3. When it works, push:
   ```
   git add .
   git commit -m "describe what you changed"
   git push
   ```

---

## WHAT'S OFFLINE vs WHAT NEEDS INTERNET

| Feature | Online? |
|---|---|
| Scan document | ✅ 100% offline |
| Draft email | ✅ 100% offline |
| Fetch from folder | ✅ 100% offline |
| Check Guidelines | ✅ 100% offline (after PDFs are on Desktop) |
| Document Reader | ✅ 100% offline |
| My Pipeline | ✅ 100% offline |
| Login/Signup | ✅ 100% offline (local SQLite) |
| Push to GitHub | ❌ Needs internet (only for backup) |

---

## PRIVACY

- PDFs you upload are **read in memory only** — never written to disk by this app.
- Your pipeline and history are stored locally in `pipeline.json` and `processor.db`.
- Nothing leaves your computer except when you push to GitHub (which you control).
