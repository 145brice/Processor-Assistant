# Audit-Readiness Checklist
### Processor Assistant · GLBA Safeguards Rule (16 CFR Part 314)

Check each off as you complete it. Items marked **⚠** are open gaps from the WISP.

## Program documents
- [ ] WISP completed (all `[BRACKET]`/`TODO` filled) and dated
- [ ] Data inventory & vendor list current
- [ ] Incident response plan with real contacts
- [ ] Written risk-assessment worksheet on file
- [ ] Annual program report written and dated

## Technical safeguards
- [ ] HTTPS/TLS enforced everywhere (✔ in place)
- [ ] MFA enabled on **all** admin accounts (Google, Railway, Supabase, Stripe, GitHub) ⚠ confirm
- [ ] Secrets only in env vars; `.env`/config gitignored (✔ in place)
- [ ] At-rest encryption confirmed for Supabase **and** local `processor.db` ⚠
- [ ] Least-privilege keys; admin access limited to Qualified Individual
- [ ] Logging in place + a monthly review cadence defined ⚠
- [ ] Dependency/vuln review cadence defined ⚠

## Data handling
- [ ] Documents not stored by the app (✔ by design)
- [ ] Retention & deletion schedule documented (incl. customer offboarding) ⚠
- [ ] **AI exposure matches UI claim** — fix the scanner label and/or enforce
      redaction before cloud send ⚠ **(highest priority)**

## Vendor oversight
- [ ] DPA / data-processing terms on file: Google ⚠, Supabase ⚠, Railway ⚠, Stripe ⚠
- [ ] Annual vendor review scheduled

## Public claims
- [ ] Website/app says **"Built for GLBA compliance"** (✔ implemented)
- [ ] No "zero data retention" claim unless Vertex AI + approved ZDR opt-out is in hand
- [ ] Privacy statement matches actual data flows (depends on the AI-label fix above)

---
**Top 3 to do next:** (1) fix the AI redaction/label gap, (2) confirm MFA + at-rest
encryption, (3) execute & file vendor DPAs.
