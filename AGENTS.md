# Agent instructions: Proc React (Next.js rebuild of Processor Assistant)

You are rebuilding Processor Assistant's UI in Next.js + React, with a FastAPI layer over the
existing Python engine. You work one task card at a time.

## Read before every task

1. `docs/nextjs-rebuild/RULES.md`: rules that must never be broken. Borrower privacy comes first.
2. `docs/nextjs-rebuild/ARCHITECTURE.md`: stack, layout, login, how the API reaches the engine.
3. `docs/nextjs-rebuild/API_CONTRACT.md`: exact request and response shapes.
4. Your task card in `docs/nextjs-rebuild/TASKS.md`, and every file it lists under "Read".

`docs/nextjs-rebuild/APP_INVENTORY.md` describes what the current Streamlit app does, page by
page. Use it when a card refers to the current app's behaviour.

## Environment (Windows)

- The repo is at `C:\Dev\Proc React`. **Write `C:\Dev` with a capital D.** If a path's case
  does not match the real folder name, Node loads React twice. The build then fails with
  "Cannot read properties of null (reading 'useContext')" and ESLint fails with "Failed to
  patch ESLint". If you see either error, check the path case before anything else.
- Python: use the virtualenv `.venv-api` (`.venv-api\Scripts\python`). It already has both
  `requirements.txt` and `backend/requirements.txt` installed. Python 3.11 works locally,
  even though ARCHITECTURE.md says 3.13.
- Web: `cd web`, then `npm ci` the first time.

## Standard checks (run from the repo root, all must pass)

```bash
.venv-api/Scripts/python -m pytest -q backend/tests pii_sanitizer/tests test_privacy_filter.py test_product_updates.py
cd web && npm run lint && npm run build
```

Then run the privacy scan from the top of `TASKS.md` against the `rebuild` branch (use
`git diff rebuild` where it says `git diff main`). It must print nothing.

## Git

- Base branch: `rebuild`. Create `rebuild/T-xx-short-name` for each task.
- **Never commit to or push `main`.** Pushing `main` deploys the live production app.
- Never commit `.env`, `pipeline.json`, `cloud_log.txt`, `scan_history.json`, `loan_docs/`,
  `loan_activity/`, `processor.db` or anything else that may hold real borrower data.
- Commit your work on the task branch. Do not merge it; the owner reviews first.

## How to work

- Do only your task. If something outside it looks wrong, list it under "Noticed" in your
  report. Do not fix it.
- Do not rewrite engine modules. Make small edits only where the card names them.
- Match `API_CONTRACT.md` exactly. If the contract looks wrong, stop and say so.
- Never skip, delete or weaken a test to make a check pass.
- Test data must be invented: obviously fake names, numbers and addresses.
- If you cannot finish, say exactly what is left. Never leave code that pretends to work.

## Report when you finish

1. **Done:** what you changed, file by file, one line each.
2. **Checks:** the last lines of the pytest, lint and build output, and the privacy scan
   output (which should be empty).
3. **Manual checks:** anything on the card marked "manual" that you could not run yourself.
4. **Noticed:** problems outside the task.
5. **Left:** anything unfinished.
