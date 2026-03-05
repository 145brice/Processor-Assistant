# Processor Assistant

AI-powered mortgage document processor that automates the tedious work of a loan processor. Upload a PDF, get conditions extracted, draft emails, and run a full 250-point compliance audit — all in-memory for maximum compliance safety.

## What It Does

A loan processor's job involves reading approval letters, CDs, LEs, credit reports, bank statements, and dozens of other documents — then manually extracting conditions, figuring out who's responsible for each one, drafting follow-up emails, and tracking everything. This app automates all of that.

### Core Features (Live Now)

- **PDF Upload & AI Extraction** — Upload any mortgage document (approval letter, CD, LE, 1003, credit report, bank statement, COC, broker package). AI reads it and extracts all conditions into a clean table with condition description, responsible party, and status (Needed/Pending/Received).
- **Per-Condition Email Drafting** — Each extracted condition has a dedicated email button. Click it, choose English or Spanish, and the AI drafts a professional email to the responsible party (borrower, title company, underwriter, etc.).
- **In-Memory Processing** — PDFs are processed entirely in memory and immediately deleted. Raw documents are never stored anywhere — not on disk, not in a database. Only structured results (conditions text, summaries) are saved if the user opts into Live Mode.
- **Sandbox Mode** — Free unlimited practice mode. No account required, no data saved. Great for testing and training.

### On-Demand Tools (Available After Upload)

- **250-Point Mega Checklist** — A massive compliance audit covering 11 categories and 250 items. The AI auto-detects the document type and checks every possible mortgage condition against the document. Categories include:
  1. Loan Type & Program (conventional, FHA, VA, USDA, ARM, jumbo, etc.)
  2. Property Type (SFR, condo, PUD, manufactured, investment, etc.)
  3. HOA & Condo Docs (dues, financials, litigation, project approval)
  4. Insurance (hazard, flood, earthquake, wind, PMI, MIP, title)
  5. Title & Legal (liens, easements, POA, trusts, divorce)
  6. Borrower Profile (credit scores, DTI, bankruptcy, housing history)
  7. Income & Employment (W-2, self-employed, VOE, pay stubs, tax returns)
  8. Assets & Reserves (accounts, gift funds, large deposits)
  9. Appraisal (form type, comps, condition ratings, zoning)
  10. Application & Disclosures (1003, LE, CD, TRID, all required notices)
  11. Closing & Funding (CTC, note, deed of trust, settlement, QC)

- **Contacts & Loan Details Extraction** — Pulls names, phone numbers, emails, loan amounts, property addresses from the document.
- **Web Research** — Identifies conditions that can be verified online and provides search links.
- **Bank Statement Rules** — 50-point compliance check specifically for bank statement analysis.
- **Risk Flags** — Scans for red flags like fraud indicators, undisclosed debts, inconsistent data.
- **Stacking Order** — Generates a loan file stacking order checklist.

### Planned Features (Phase 2)

- **Stripe Payments** — $10/file in Live Mode, 5 free files for new accounts
- **Supabase Auth** — Full user accounts with scan history
- **OCR Support** — For scanned/image-based PDFs
- **Multi-Document Workflow** — Upload entire loan files and cross-reference across documents

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| AI Engine | Google Gemini 2.5 Flash (via OpenAI-compatible SDK) |
| PDF Parsing | pypdf (in-memory only) |
| Auth & DB | Supabase (optional, graceful degradation if not configured) |
| Payments | Stripe (Phase 2) |
| Prompts | Python `string.Template` ($variable syntax) |

## Project Structure

```
processor-traien/
├── app.py              # Main Streamlit UI — upload, display, email buttons
├── ai_engine.py        # AI processing — conditions, emails, checklist, etc.
├── prompts.py          # All AI prompt templates (conditions, mega checklist, emails, etc.)
├── db.py               # Supabase helpers — auth, history, pattern logging
├── supabase_schema.sql # Database schema with RLS policies
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
└── .env                # Your actual config (not committed)
```

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/145brice/Processor-Assistant.git
cd Processor-Assistant
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
```

```env
# Required — Get a key from https://aistudio.google.com/apikey
OPENAI_API_KEY=your-gemini-api-key
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_MODEL=gemini-2.5-flash

# Optional — Supabase for user accounts & history
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Optional — Stripe for payments (Phase 2)
STRIPE_SECRET_KEY=
STRIPE_PRICE_ID_SIGNUP=
STRIPE_PRICE_ID_FILE=
```

### 3. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. Click **"Try Sandbox"** to start without an account.

## How It Works

1. **Upload** a mortgage PDF (approval letter, CD, LE, etc.)
2. **Select** the document type from the dropdown
3. **Click Scan** — AI extracts all conditions into a structured table
4. **Review** — Each condition shows what's needed, who's responsible, and current status
5. **Draft Emails** — Click the email button on any condition to generate a professional follow-up email in English or Spanish

### Compliance Architecture

- PDFs are read into `bytes` via Streamlit's file uploader
- Text is extracted in-memory using `pypdf` with `io.BytesIO`
- The `bytes` object is explicitly deleted (`del pdf_bytes`) after extraction
- Only the AI's structured output (conditions table, email drafts) is ever displayed or saved
- Raw document text is never persisted to disk or database
- Supabase stores only: doc type, conditions summary, risk flags, timestamps

## API Configuration

The app uses Google's Gemini AI through the OpenAI-compatible API endpoint. This means:
- You need a Google AI Studio API key (free tier available)
- The OpenAI Python SDK handles all API calls
- You can swap to any OpenAI-compatible provider by changing the `.env` values

## License

MIT
