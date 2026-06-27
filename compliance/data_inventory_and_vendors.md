# Data Inventory & Service Providers
### Processor Assistant — supports WISP §4.2 and §6

**Status:** DRAFT · **Last updated:** [TODO] · **Owner:** Brice Leasure

> Not legal advice. Confirm each row against current configuration.

## 1. Data we handle

| Data | Classification | Where it lives | Retention | Notes |
|---|---|---|---|---|
| Uploaded loan PDFs | **NPI (high)** | In memory during scan only | **Not stored by us** | Transmitted to Google Gemini only when cloud AI is used (see §3). |
| Extracted conditions / loan metadata | NPI (medium) | Local `processor.db` (host) | Until deleted / trashed | Non-document fields used for the pipeline. |
| Borrower contact info | NPI (medium) | Local `processor.db` | Until deleted | Names, emails, phones parsed from docs. |
| Recent scan history | NPI (low–medium) | Supabase settings / local | ~7 days (recent scans) | Tied to signed-in account. |
| User account/profile | Account data | Supabase (`settings`) | Life of account | Email, display name, role, subscription/tier. |
| Auth identity | Account data | Google OAuth (delegated) | N/A | We store no passwords. |
| Billing/subscription | Account data | Stripe + Supabase profile | Life of account | We never see/store card numbers. |
| Secrets (API keys, tokens) | Secret | Host env vars / gitignored config | Rotated as needed | Never in source control. |

## 2. Service providers (sub-processors)

| Provider | Role | NPI handled? | Safeguards / terms | Review |
|---|---|---|---|---|
| **Google** (OAuth + Gemini API, paid tier) | Sign-in + AI document reading | **Yes** (during cloud scans) | No training on data; no human review; brief retention (~up to 55 days) for abuse/security monitoring only. DPA: [TODO link]. | Annual |
| **Supabase** | Auth-linked profile/settings storage | Yes (metadata) | Encryption at rest & in transit; access via scoped keys. DPA: [TODO]. | Annual |
| **Railway** | Application hosting | Yes (in transit / runtime) | TLS; isolated service. DPA: [TODO]. Confirm volume/encryption for `processor.db`. | Annual |
| **Stripe** | Payments/subscriptions | Card data (not seen by us) | PCI-DSS Level 1. We store no PAN. DPA: [TODO]. | Annual |
| **GitHub** | Source control | No NPI (secrets excluded) | MFA; private repo [TODO confirm]. | Annual |

## 3. Data-flow summary

```
User browser ──HTTPS──> Processor Assistant (Railway)
   │                         │
   │ Google OAuth            ├── Supabase (profiles/settings)  [HTTPS, encrypted at rest]
   │                         ├── Stripe (billing)              [HTTPS, PCI-DSS]
   │                         └── local processor.db            [host; confirm encryption/volume]
   │
   └── Uploaded PDF ── processed locally (OCR + rules) ── NOT stored
            │
            └── IF cloud AI used (Approval Letter / Purchase Contract, user opt-in):
                 full PDF ──HTTPS──> Google Gemini API
                 (no training, no human review; brief security-monitoring retention)
```

## 4. Known gap

Default cloud-scan mode (`PA_PDF_VISION=true`) sends the **full unredacted PDF** to
Google. The local redaction filter exists but only runs on the privacy-safe text
fallback. See WISP Open Item #1.
