# Architecture

## Stack

| Part | Choice | Notes |
|---|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript strict, Tailwind CSS | In `web/`. Client-side data fetching from the API; no Next.js API routes for business logic. |
| Auth | Supabase Auth with Google sign-in (`@supabase/supabase-js`, `@supabase/ssr`) | Same Supabase project as production. |
| Backend | FastAPI (Python 3.13) | In `backend/pa_api/`. Imports the existing engine modules from the repo root. |
| Engine | Existing Python modules | Unchanged except the small context hooks in task T-03. |
| Hosting | Railway: two new services (`pa-web`, `pa-api`) | The production Streamlit service stays untouched until switch-over. |

## Folder layout

```
Processor-Assistant/
  app.py, ai_engine.py, cloud_client.py, crm.py, ...   existing engine + Streamlit (unchanged)
  pii_sanitizer/                                      existing redaction package
  backend/
    pa_api/
      main.py          FastAPI app, CORS, router registration, /api/health
      context.py       per-request user context (who is calling, their AI key, sandbox)
      auth.py          verifies the Supabase access token, builds the context
      models.py        Pydantic models = API_CONTRACT.md
      routers/         one file per area: me, ai_key, scan, loans, history, outputs, usage, tools
    tests/             pytest, uses fake data only
    requirements.txt   API-only extras (the engine's requirements.txt is installed too)
  web/
    src/app/           routes (see "Routes" below)
    src/components/    Sidebar, Header, ConditionTable, ...
    src/lib/types.ts   TypeScript types = API_CONTRACT.md
    src/lib/api.ts     one typed function per endpoint
    src/lib/supabase.ts  browser Supabase client
  docs/nextjs-rebuild/ this brief
```

## Routes (web)

| URL | Replaces route key | Task |
|---|---|---|
| `/login` | login page | T-12 |
| `/auth/callback` | OAuth return | T-12 |
| `/scanner` (and `/` redirects here) | `dashboard` | T-20 to T-23 |
| `/pipeline` | `pipeline` | T-24 |
| `/loans/[id]` | `loan_detail` | T-25, T-26 |
| `/history` | `history` | T-27 |
| `/overview` | `overview` | T-27 |
| `/settings/ai` | `ai_settings` | T-16 |
| `/settings/usage` | `billing` | T-27 |
| `/pricing` | `pricing` | T-27 |
| `/tools/[tool]` | every More Tools route key | T-30 to T-33 |
| `/privacy`, `/terms` | policy pages | T-11 |

All pages except `/login`, `/auth/callback`, `/privacy`, `/terms` require a session or
sandbox mode.

## Login and identity

1. The browser signs in with Supabase Google OAuth (`signInWithOAuth({provider: "google"})`)
   and returns to `/auth/callback`.
2. Every API request sends `Authorization: Bearer <Supabase access token>`.
3. `pa_api/auth.py` validates the token by calling Supabase `GET {SUPABASE_URL}/auth/v1/user`
   with the token (cache the result per token for 60 seconds) and reads the user's `id` and
   `email`.
4. **The user key is the Supabase user `id`.** This is the same value the Streamlit app stores
   as `supabase_user_id` and uses for pipelines, settings and saved scans, so existing users
   see their existing data. Do not invent a different key.
5. First sign-in calls `supabase_auth.ensure_user_profile` and `accept_terms` as the Streamlit
   app does.
6. **Sandbox mode**: "Try with a sample loan" sets a `pa_sandbox=1` cookie in the browser and
   sends header `X-PA-Sandbox: 1`. The API then uses an anonymous sandbox context: sample
   pipeline (`pipeline.sample.json`), no cloud writes, no AI calls, no quota.

## How the API reaches the engine (request context)

Several engine modules read the current user from Streamlit's `st.session_state`
(`crm._current_user_key`, `cloud_client.get_config`, `supabase_auth`, `supabase_sync`,
`scan_outputs`, `product_config`). The API has no Streamlit session. Task T-03 adds a small
hook so those modules first ask `pa_api.context` and fall back to Streamlit only if no API
context is active:

```python
# pa_api/context.py (already in the skeleton)
@dataclass(frozen=True)
class RequestContext:
    user_key: str            # Supabase user id, "" in sandbox
    email: str
    gemini_key: str          # the user's own key, "" if none
    sandbox: bool

def current() -> RequestContext | None: ...
```

Rules for the hook (T-03):

- `crm._current_user_key()`: if an API context is active, return `ctx.user_key` (or `""` in
  sandbox); otherwise the existing Streamlit lookup.
- `crm._is_sandbox()`: same idea with `ctx.sandbox`.
- `cloud_client.get_config()`: if an API context is active, use **only** `ctx.gemini_key`
  (provider `gemini`, default model). **Do not** read `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY` or `cloud_config.json` in that case. No key means AI disabled.
- The Streamlit app's behaviour must not change (its tests must still pass).

## Data storage (unchanged)

| Data | Where | Accessed through |
|---|---|---|
| Users, profiles, terms, encrypted Gemini keys, settings | Supabase `settings`/`users` tables | `supabase_auth` |
| Pipeline (loans, conditions, contacts, documents metadata) | Supabase per-user snapshot, JSON fallback | `crm`, `supabase_sync` |
| Loan activity | `loan_activity/` files and Supabase | `crm.log_activity`, `get_activity` |
| Saved scans | Supabase settings | `scan_history_store` |
| Monthly scan counts | SQLite file `processor.db` | `billing` |
| Lender statistics | Supabase settings | `approval_intelligence` + `supabase_auth` |

Known weakness to keep in mind, not to fix in the rebuild: `processor.db` and local JSON
fallbacks live on the container disk and reset on redeploy.

## Environment variables

`pa-api` needs the production Supabase and encryption variables plus the spaCy setting.
`pa-web` needs only public values.

| Variable | Service | Purpose |
|---|---|---|
| `SUPABASE_URL` | api, web (`NEXT_PUBLIC_SUPABASE_URL`) | Supabase project URL |
| `SUPABASE_ANON_KEY` | api, web (`NEXT_PUBLIC_SUPABASE_ANON_KEY`) | Public client key |
| `SUPABASE_SERVICE_ROLE_KEY` | api only | Server access to settings/pipeline tables. Never in `web/`. |
| `GEMINI_KEY_ENCRYPTION_SECRET`, `PA_SETTINGS_ENCRYPTION_KEY` | api | Decrypt saved user keys and settings |
| `PII_NER_MODEL=en_core_web_md` | api | Name detection model for redaction |
| `PA_FREE_BETA_MODE`, `PA_FREE_BETA_USER_LIMIT`, `PA_BETA_END_DATE`, `PA_FOUNDER_SPOTS`, `PA_FOUNDER_MONTHLY_PRICE` | api | Beta and pricing text |
| `TIER_*_PRICE_ID`, `TIER_*_PAYMENT_LINK`, `STRIPE_WEBHOOK_SECRET` | api | Pricing links |
| `PA_ENABLE_ADVANCED_TOOLS` | api | More Tools switch (default on) |
| `PA_OWNER_ADMIN_EMAILS`, `PA_PRIVATE_ADMIN_EMAILS` | api | Owner-only features |
| `PA_GEMINI_SETUP_VIDEO` | api | Optional setup video URL |
| `RESEND_API_KEY`, `RESEND_FROM`, `ADMIN_NOTIFICATION_EMAIL` | api | Email sending |
| `PA_WEB_ORIGIN` | api | Allowed CORS origin (the `pa-web` URL) |
| `NEXT_PUBLIC_API_URL` | web | Base URL of `pa-api` |

**Never set on `pa-api`:** `GEMINI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`,
`CLAUDE_API_KEY`, `OPENAI_API_KEY`, `PA_PDF_VISION` (see RULES.md section 2).

## Running locally

```bash
# API (from the repo root)
python -m venv .venv-api && .venv-api/Scripts/activate      # Windows; use bin/activate elsewhere
pip install -r requirements.txt -r backend/requirements.txt
uvicorn backend.pa_api.main:app --reload --port 8600
python -m pytest backend/tests pii_sanitizer/tests test_privacy_filter.py

# Web
cd web
npm install
copy .env.example .env.local        # then fill in the values
npm run dev                          # http://localhost:3000
npm run build && npm run lint
```

## Deployment (task T-40)

- `pa-api`: new Railway service, Dockerfile `backend/Dockerfile` (based on the production one:
  Python 3.13, Tesseract, the spaCy model), start command
  `uvicorn backend.pa_api.main:app --host 0.0.0.0 --port $PORT`, health check `/api/health`.
- `pa-web`: new Railway service, root `web/`, `npm run build`, `npm start`.
- Both deploy from a `rebuild` branch, not `main`, until switch-over.
- Switch-over (T-41) is done by the owner: point `processor.edgelandings.com` to `pa-web`,
  keep the Streamlit service running on its Railway URL for two weeks as a fallback.
