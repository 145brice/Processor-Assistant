# Processor Assistant: Next.js rebuild

This folder is the complete brief for rebuilding Processor Assistant's user interface in
Next.js + React, while keeping the existing Python engine. It is written so a coding model
can do the work one task at a time without needing to understand the whole app first.

## What the app is

Processor Assistant helps mortgage loan processors. A processor uploads loan PDFs (approval
letters, purchase contracts, bank statements, pay stubs and so on). The app:

1. detects each document's type,
2. extracts the conditions, contacts and key numbers from it,
3. optionally improves the extracted conditions with AI (the user's own Gemini key, and only
   after personal details are removed),
4. matches the document to a loan in the user's pipeline, and
5. produces borrower emails, loan-officer updates, a PDF/CSV export and a tracked list of
   conditions per loan.

Production today is a Streamlit app (`app.py`, about 14,700 lines) on Railway at
processor.edgelandings.com. The engine code (document reading, OCR, redaction, AI calls,
parsing) lives in other Python modules and is well tested.

## The plan in one paragraph

Keep every Python engine module. Put a FastAPI server in front of it (`backend/pa_api/`).
Build a new Next.js app (`web/`) that talks only to that API. Rebuild the core screens first
(login, scanner, pipeline, loan detail, history, AI key setup, usage and pricing), then the
"More Tools" pages. The Streamlit app keeps running in production until the new app matches
it; the new app gets its own Railway service and is switched over at the end.

## Files in this folder

| File | What it is for |
|---|---|
| `README.md` | This overview and the working method. Read first. |
| `RULES.md` | Rules that must never be broken (privacy, AI keys, deploys, data files). Read before every task. |
| `APP_INVENTORY.md` | Every page and feature of the current app, where its code lives, and what it does. |
| `ARCHITECTURE.md` | Stack, folder layout, login, how the API reaches the engine, data storage, environment variables, deployment. |
| `API_CONTRACT.md` | Every API endpoint with request and response shapes. Frontend and backend must both match it exactly. |
| `TASKS.md` | The build, split into small numbered tasks with "done when" checks. Do them in order. |

## Skeleton already in the repo

- `backend/pa_api/`: FastAPI app with `/api/health` working, the request-context module,
  the data models from `API_CONTRACT.md`, and every endpoint stubbed to return HTTP 501
  with the task number that implements it. Tests: `backend/tests/`.
- `web/`: Next.js (App Router, TypeScript, Tailwind) with the sidebar layout, every core
  route as a placeholder page naming its task, `src/lib/types.ts` mirroring the API models
  and `src/lib/api.ts` with one typed function per endpoint.

Both build and pass their checks as delivered. Keep them that way after every task.

## How to delegate a task (for the person running the build)

1. Give the model: `RULES.md`, `ARCHITECTURE.md`, `API_CONTRACT.md`, and the single task card
   from `TASKS.md`. Add the source files the card lists under "Read".
2. Ask for the change plus the output of the card's "Check" commands.
3. Before merging, rerun the checks yourself and skim the diff for anything in `RULES.md`
   (search the diff for `GEMINI_API_KEY`, `inline_data`, `application/pdf`, `os.getenv(`).
4. One task per branch, named `rebuild/T-xx-short-name`. Never push to `main` (pushing
   `main` deploys production).
5. Tick the task in `TASKS.md` when merged.

## How to work (for the model doing a task)

- Do only the task you were given. If something outside it looks wrong, write it in your
  reply under "Noticed"; do not fix it.
- Do not rename, move or reformat existing Python modules. Small, targeted edits only, and
  only where the task says so.
- Match the API contract exactly. If the contract seems wrong, stop and say so.
- Run the task's checks and include their output. A task is not done until they pass.
- If you cannot finish, say exactly what is left. Never leave a stub that pretends to work.

## Glossary

| Term | Meaning |
|---|---|
| Processor | The user: a mortgage loan processor. |
| Loan officer (LO) | Sells the loan; receives status updates from the processor. |
| Underwriter (UW) | Approves the loan and issues conditions. |
| Condition | Something required before the loan can close ("Provide 2 months bank statements"). Each has a responsible party and a status. |
| Approval letter | Lender document listing conditions, grouped in sections such as PTD (prior to docs), PTF (prior to funding), AC (at closing). |
| Pipeline | The processor's list of loans. |
| Scan | Uploading one PDF and extracting its data. |
| Batch | One scanned file's result in the scanner (`{file, type, result, loan_match}`). |
| Sandbox | Demo mode with sample loans and no account; nothing is saved to the cloud. |
| Redaction | Replacing personal details with placeholders like `[BORROWER_1]` before any AI call. |
