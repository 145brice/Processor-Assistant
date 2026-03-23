# Processor Traien — Setup Guide

Complete installation and configuration guide. Everything runs locally on your machine. No cloud account required.

---

## Table of Contents

1. [System Requirements](#1-system-requirements)
2. [Installation](#2-installation)
3. [First Run](#3-first-run)
4. [Optional: Cloud AI (Claude / OpenAI)](#4-optional-cloud-ai-claude--openai)
5. [Optional: Ollama (Local AI)](#5-optional-ollama-local-ai)
6. [Optional: Email Watch (IMAP)](#6-optional-email-watch-imap)
7. [Team Sharing (Offline Network)](#7-team-sharing-offline-network)
8. [Billing & Usage Tracking](#8-billing--usage-tracking)
9. [Running the Test Suite](#9-running-the-test-suite)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Requirements

| Item | Minimum |
|------|---------|
| OS | Windows 10, macOS 12, or Ubuntu 20.04 |
| Python | 3.11 or later |
| RAM | 4 GB (8 GB recommended) |
| Storage | 500 MB free (more for Ollama models: ~2–8 GB each) |
| Network | Internet only needed for Cloud AI and Email Watch features |

---

## 2. Installation

### Step 1 — Clone or download the project

```bash
git clone https://github.com/145brice/Processor-Assistant.git
cd Processor-Assistant
```

Or download the ZIP from GitHub and extract it.

### Step 2 — Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

**Core packages installed:**
- `streamlit` — the web UI framework
- `pypdf` — in-memory PDF text extraction (no OCR)
- `thefuzz` — fuzzy string matching for borrower name lookup
- `python-Levenshtein` — speeds up thefuzz

**No API keys needed for core functionality.** The app works fully offline after this step.

### Step 4 — Verify installation

```bash
python -c "import streamlit, pypdf, thefuzz; print('All packages OK')"
```

---

## 3. First Run

### Start the app

```bash
streamlit run app.py
```

Your browser opens automatically at `http://localhost:8501`.

> **Windows users:** If Streamlit doesn't open the browser automatically, go to `http://localhost:8501` manually.

### Create your account

1. Click **Sign Up** tab on the login screen
2. Enter your email, display name, and choose your role:
   - **Processor** — full access to scanner, pipeline, email watch
   - **Loan Officer** — can view pipeline and share loans
   - **Jr Underwriter** — read/review access
   - **Manager** — all access including billing admin view
3. Choose a strong password and confirm it
4. Click **Create Account**

> Your account is stored locally in `processor.db`. No data leaves your machine.

### Sandbox Mode

Click **Enter Sandbox Mode** on the login screen to explore the app with sample data — no account needed, nothing is saved.

---

## 4. Optional: Cloud AI (Claude / OpenAI)

Enables smarter document analysis, condition enhancement, and email drafting using a cloud AI provider.

**Requires:** Internet connection + API key from your chosen provider.

### Get an API key

**Anthropic Claude** (recommended — best for mortgage documents):
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account → **API Keys** → **Create Key**
3. Copy the key (starts with `sk-ant-...`)

**OpenAI (GPT)**:
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create a new key
3. Copy the key (starts with `sk-...`)

### Configure in the app

1. Click **🤖 AI Settings** in the sidebar
2. Under **Cloud AI (Claude / OpenAI)**:
   - Toggle **Enable Cloud AI** on
   - Select your provider
   - Select a model (`claude-sonnet-4-6` for Claude, `gpt-4o-mini` for OpenAI)
   - Paste your API key
3. Click **💾 Save Cloud Settings**
4. Click **🔗 Test Cloud Connection** to verify

### Set as preferred backend

Still in **AI Settings**, under **Preferred Backend**:
- Select **☁️ Cloud AI first** to use Cloud AI for all AI features
- Enable **fallback** so Ollama or script-only runs if Cloud AI is unavailable

### Estimated cost

| Model | Cost per document analysis (approx.) |
|-------|---------------------------------------|
| claude-sonnet-4-6 | ~$0.003–$0.008 |
| claude-haiku-4-5-20251001 | ~$0.0005–$0.001 |
| gpt-4o-mini | ~$0.001–$0.003 |

---

## 5. Optional: Ollama (Local AI)

Runs AI models entirely on your machine. No internet, no API key, no cost.

**Trade-off:** Slower than Cloud AI; response times depend on your hardware.

### Step 1 — Install Ollama

Download from [ollama.com](https://ollama.com) and run the installer.

- **Windows:** Installs a system tray icon; starts automatically
- **macOS:** Drag to Applications; launches from menu bar
- **Linux:** `curl -fsSL https://ollama.com/install.sh | sh`

### Step 2 — Pull a model

Open a terminal and run:

```bash
ollama pull llama3.2
```

Choose based on your hardware:

| Model | RAM needed | Speed | Quality |
|-------|------------|-------|---------|
| `llama3.2` | 4 GB | Fast | Good — recommended for most users |
| `mistral` | 5 GB | Moderate | Better reasoning |
| `llama3.1` | 6 GB | Slow | Best quality |
| `llama3.2:1b` | 1 GB | Very fast | Light tasks only |

### Step 3 — Start the Ollama server

```bash
ollama serve
```

Ollama may start automatically after installation. Check if it's running:

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response with your installed models.

### Step 4 — Configure in the app

1. Click **🤖 AI Settings** in the sidebar
2. Under **Ollama (Local — 100% Offline)**:
   - Toggle **Enable Ollama** on
   - Endpoint: `http://localhost:11434` (default — don't change unless running on a remote machine)
   - Select your model from the dropdown
3. Click **💾 Save Ollama Settings**

---

## 6. Optional: Email Watch (IMAP)

Automatically checks your inbox for PDF attachments, extracts borrower names, and matches them to your pipeline.

**Privacy:** Only your machine connects to your email server. No relay, no cloud.

### Gmail setup

Gmail requires an **App Password** (not your regular password):

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. **Security** → **2-Step Verification** (enable if not already on)
3. **Security** → **App passwords**
4. Select app: **Mail** → Device: **Windows Computer** → **Generate**
5. Copy the 16-character code — this is your app password

### Outlook / Microsoft 365 setup

1. Sign in at [account.microsoft.com](https://account.microsoft.com)
2. **Security** → **Advanced security options** → **App passwords**
3. Create a new app password → Copy it

### Configure in the app

1. Click **📧 Email Watch** in the sidebar
2. Under **Credentials**:
   - Select your provider (Gmail, Outlook, Yahoo, or Custom)
   - Enter your email address
   - Paste your app password
   - Set check interval (2–30 minutes)
   - Set "Only look back" (0 = all unread, or limit to last N hours)
3. Click **💾 Save Credentials**
4. Click **▶ Start Watching**

### How it works

- Runs in the background — you can use the rest of the app normally
- Every N minutes: connects, fetches unread PDF attachments, disconnects
- Reads first 3 pages of each PDF for borrower names
- Fuzzy-matches against your pipeline
- Shows a card in Email Watch with a confidence score and suggested folder

---

## 7. Team Sharing (Offline Network)

Share loans with team members over your office WiFi — no central server needed.

### How it works

Each team member's app has a personal **inbox folder** (a folder on a shared network drive, UNC path, or any location the other person can write to). Sharing a loan = writing a small JSON file to their inbox folder.

### Setup

1. Click **👥 My Team** in the sidebar
2. Set your own **inbox folder path** — this is where others will send you files
   - Example: `\\SERVER\Users\YourName\ProcessorInbox`
   - Or any local path if testing on one machine: `C:\Users\YourName\inbox`
3. Click **Add Team Member** for each person:
   - Enter their name, role, and their inbox folder path
4. To share a loan: open the loan in **Pipeline** → click **📤 Share**

### Receiving shared loans

The **My Team** page shows any loans others have shared with you. Accept or dismiss each one.

---

## 8. Billing & Usage Tracking

Tracks how many documents you scan each month and calculates cost.

### Pricing

| Item | Amount |
|------|--------|
| Monthly base | $49.00 |
| Included scans | 50 per month |
| Overage | $10.00 per scan over 50 |

### View your usage

Click **💳 Usage & Billing** in the sidebar to see:
- Current month scan count and quota bar
- Breakdown by document type
- Monthly history (last 6 months)
- Manager view: all users' usage (Manager role only)

> **Note:** This module tracks usage for your records only. No charges are processed automatically.

---

## 9. Running the Test Suite

Validates all document extraction functions against realistic mock documents.

```bash
python -X utf8 test_extraction.py
```

To save the report to a file:

```bash
python -X utf8 test_extraction.py > test_report.txt
```

### What is tested

| Category | Tests | What it checks |
|----------|-------|----------------|
| 1003 Application | 9 | Borrower name, SSN, DOB, email, co-borrower, employer, income, loan amount, property address |
| Purchase Contract | 8 | Buyer, seller, price, closing date, earnest money, title company, agent |
| Bank Statement | 4 | Structured output format, NSF detection, balance checking |
| Condition Extraction | 5 | Lender condition codes, document requirements extraction |
| Risk Flags | 2 | Flag assessment on bank statement and 1003 |
| Fraud Check | 5 | SSN multiplicity, balance jumps, zero withholding, full risk scan |
| Email Draft | 2 | English and Spanish draft generation |
| Contact Extraction | 1 | Names, phones, emails from purchase contract |
| Doc Verify | 3 | Type detection, date extraction |
| Billing | 5 | Usage tracking, cost calculation |

Expected result: **46+ tests passing, 0 failures.**

---

## 10. Troubleshooting

### App won't start

```
ModuleNotFoundError: No module named 'streamlit'
```
**Fix:** Run `pip install -r requirements.txt` and make sure your virtualenv is activated.

---

### PDF shows "no text extracted"

Most PDFs from lenders are text-based and work fine. Some scanned/image PDFs won't work.

**Fix:** `pypdf` does not do OCR. Ask the sender for the original digital PDF, not a scan. If you must process a scanned PDF, use a third-party OCR tool to convert it to a searchable PDF first.

---

### Ollama not connecting

```
Cannot reach Ollama: [Errno 111] Connection refused
```

**Fix:**
1. Make sure Ollama is installed
2. Run `ollama serve` in a terminal
3. Test: `curl http://localhost:11434/api/tags`
4. If still failing, check if port 11434 is blocked by your firewall

---

### Email Watch: "Invalid credentials"

**Fix:**
- Gmail: Use an App Password, not your regular password. 2-Step Verification must be on.
- Outlook: Use an App Password from account.microsoft.com/security
- Never use your actual login password — always use an app password

---

### Email Watch: "Cannot reach" server

**Fix:** Check your internet connection. If you're on a VPN, some IMAP ports (993) may be blocked — temporarily disconnect the VPN.

---

### Cloud AI: "Invalid API key (401)"

**Fix:**
- Claude: Key must start with `sk-ant-api03-...`
- OpenAI: Key must start with `sk-...`
- Check for extra spaces — paste without trailing spaces
- Ensure your account has billing set up (free tier may not have API access)

---

### Condition extraction seems wrong

The scanner works best on:
- Lender commitment letters with condition codes (e.g., `Underwriter WCR01`)
- Numbered/bulleted condition lists

It works less well on:
- Heavily formatted PDFs where column layout causes text extraction to interleave columns
- Scanned documents
- Image-based PDFs

**Tip:** Use the **🤖 Enhance conditions** button (requires Cloud AI or Ollama) to improve extraction results on tricky documents.

---

### Database errors

```
sqlite3.OperationalError: database is locked
```

**Fix:** Only run one instance of the app at a time. Close any duplicate browser tabs running the app and restart Streamlit.

---

### Windows: "cp1252" encoding error in terminal

**Fix:** Run the test suite with: `python -X utf8 test_extraction.py`

Or set your terminal to UTF-8: `chcp 65001` then run normally.

---

### App is slow on large PDFs

The scanner adds a small delay per page to avoid CPU spikes. For large documents (20+ pages), this is intentional. If you need faster processing, reduce the `time.sleep(0.5)` in `ai_engine.py:extract_text_from_pdf()` — but watch your CPU usage.

---

## File Reference

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application (all pages) |
| `ai_engine.py` | Core offline processing engine — regex, condition extraction |
| `db.py` | Local SQLite database — users, scan history |
| `billing.py` | Monthly usage tracking and cost calculation |
| `crm.py` | Pipeline loan management (CRUD) |
| `fraud_check.py` | 7-rule fraud detection — SSNs, balances, pay uniformity |
| `doc_verify.py` | Quick doc type detection and metadata extraction |
| `guidelines.py` | Fannie/Freddie guideline search (requires guideline PDFs) |
| `folder_search.py` | Fuzzy local file search for condition documents |
| `email_watch.py` | IMAP background email watcher |
| `sharing.py` | Peer-to-peer loan sharing via inbox folders |
| `ollama_client.py` | Ollama local AI integration |
| `cloud_client.py` | Claude / OpenAI cloud AI integration |
| `ai_router.py` | AI backend dispatcher — routes to cloud, Ollama, or script |
| `test_extraction.py` | Test suite with mock documents — validates all extractors |
| `SETUP.md` | This file |
| `processor.db` | SQLite database (auto-created on first run) |
| `pipeline.json` | Loan pipeline data |
| `incoming/` | PDFs downloaded by Email Watch |
| `guidelines_index/` | Cached guideline search index |

---

*Processor Traien — 100% local, no cloud required.*
