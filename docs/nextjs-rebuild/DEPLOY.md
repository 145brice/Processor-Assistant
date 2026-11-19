# Deploying the new app (tasks T-40 and T-41)

Two new Railway services, `pa-api` and `pa-web`, deploy from the `rebuild` branch. The production
`Processor-Assistant` service (Streamlit) is **never touched** until the owner switches the domain.

## Before anything is created: read this

- **Money.** Two always-on services add to the project's spend. In November the Railway spend limit
  was reached and Railway removed every deployment of `Processor-Assistant`, which took the live
  site down until the limit was raised. New services share that limit, so raise it first or watch it.
- **Shared data.** `pa-api` uses the **same Supabase project** as the live app. Anything it saves
  is real. Test with the sample-loan mode first, and only then with a real account.
- **Sign-in.** Supabase only returns people to addresses on its Redirect URLs list. The first real
  Google sign-in on the new app therefore happens at the switch-over, on `processor.edgelandings.com`
  (already allowed), unless the owner adds the `pa-web` address to that list.

## What the repo provides

| File | Purpose |
|---|---|
| `backend/Dockerfile` | `pa-api` image: Python 3.13, Tesseract, spaCy name model, `PII_NER_MODEL=en_core_web_md`, uvicorn |
| `backend/Dockerfile.dockerignore` | Keeps `.env`, real data files and `web/` out of the API image (production build unaffected) |
| `backend/railway.json` | Tells Railway to use that Dockerfile and `/api/health` |
| `web/railway.json`, `web/.nvmrc` | `pa-web`: Nixpacks build, `npm start`, Node 20 |
| `scripts/check_deployment.py` | 12 checks to run against the deployed pair |

## T-40: create the services (owner approves first)

1. In the Railway project, create service **pa-api** from this repo, branch `rebuild`, root directory
   `/`, config file `/backend/railway.json`.
2. Set its variables (names only here; copy the values from the production service, never from chat):
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_KEY`,
   `PA_SETTINGS_ENCRYPTION_KEY`, `RESEND_API_KEY`, `RESEND_FROM`, `ADMIN_NOTIFICATION_EMAIL`,
   `STRIPE_WEBHOOK_SECRET`, `TIER_*_PAYMENT_LINK`, `TIER_*_PRICE_ID`, `PA_ENABLE_ADVANCED_TOOLS`,
   `PA_OWNER_ADMIN_EMAILS` (owner accounts skip the scan limit), plus
   `PA_WEB_ORIGIN=<the pa-web address, no trailing slash>`.
   **Never set on pa-api:** `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`,
   `CLAUDE_API_KEY`, `OPENAI_API_KEY`, `PA_PDF_VISION` (RULES.md section 2).
3. Generate a public address for `pa-api`. Create **pa-web** from the same repo and branch, root
   directory `/web`, config file `/web/railway.json`, with
   `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (public key only) and
   `NEXT_PUBLIC_API_URL=<the pa-api address>`. These are baked in at build time, so set them first.
4. Put the `pa-web` address into `PA_WEB_ORIGIN` on `pa-api` and redeploy it.
5. Run `python scripts/check_deployment.py <pa-api address> <pa-web address>`. All 12 must pass.
6. In a browser, open `pa-web`, choose "Try with a sample loan" and click through the scanner,
   pipeline, a loan, and a few More Tools.

## T-41: the switch (owner only)

1. Pick a quiet time. Note the current Streamlit deployment id so it can be restored.
2. Move `processor.edgelandings.com` from `Processor-Assistant` to `pa-web` (Railway custom domain,
   plus the DNS record Railway shows if it changes).
3. Immediately run the check script with `https://processor.edgelandings.com` as the web address and
   sign in with Google. Open the scanner, a loan, and AI Settings.
4. If anything is wrong: move the domain back to `Processor-Assistant`. Users are back on the old app
   within minutes; nothing was changed in it.
5. Keep `Processor-Assistant` running on its own `*.up.railway.app` address for two weeks, then
   merge `rebuild` into `main` and retire it.

## Things to know

- **Judge the route guard on a production build.** `next dev` did not enforce the sign-in redirect in
  the test setup; `next build` + `next start` (what Railway runs) did, and the check script verifies it.
- **No files are kept.** The API stores no uploaded documents and the More Tools never write folders.
  The container can be restarted or redeployed at any time without losing user data (it is in Supabase).
- **Concurrent users.** The engine's loan cache is kept per user while serving API requests
  (`crm._api_bucket`), so users cannot see each other's loans. `backend/tests/test_crm_isolation.py`
  covers this and must stay green.
- **Not in the new app:** Team, Income Verifier, Auto Data Entry, Fraud Detector and Underwriting Tracker (parked in
  `parked/`, see `parked/README.md`), plus merging
  the pages of one bank statement, the usage history list, and a Cloud AI on/off switch (AI is on
  whenever a key is saved).
