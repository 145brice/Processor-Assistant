# Written Information Security Program (WISP)
### Processor Assistant

**Status:** DRAFT — pending review by a qualified compliance professional / attorney.
**Owner / Qualified Individual:** Brice Leasure
**Effective date:** [TODO]
**Last reviewed:** [TODO] · **Next review due:** [TODO — at least annually]

> Not legal advice. This program documents reasonable safeguards for a small
> business handling consumer financial information, aligned to the FTC Safeguards
> Rule (16 CFR Part 314). Replace every `[BRACKET]`/`TODO` with your real facts.

---

## 1. Purpose & Scope

Processor Assistant ("the Service") helps mortgage processors read loan documents,
extract conditions, and track a loan pipeline. In doing so it may handle
**nonpublic personal information (NPI)** about borrowers, including names, contact
details, loan numbers, and — when documents are scanned — Social Security numbers
and financial data.

This WISP covers all systems, vendors, and people involved in operating the
Service. It applies to the sole operator today and to any future employees or
contractors.

## 2. Qualified Individual (§314.4(a))

| | |
|---|---|
| **Name** | Brice Leasure |
| **Role** | Owner / Operator |
| **Responsibilities** | Owns this program; performs risk assessments; selects and reviews safeguards; oversees vendors; leads incident response; reports to ownership (self) at least annually. |
| **Contact** | [TODO: email / phone] |

## 3. Risk Assessment (§314.4(b))

A written risk assessment is maintained and refreshed at least annually or after
any material change. Summary of current assessment:

| Asset / data | Threat | Likelihood | Impact | Current safeguard | Residual risk |
|---|---|---|---|---|---|
| Borrower NPI in uploaded PDFs | Interception in transit | Low | High | TLS/HTTPS everywhere | Low |
| Borrower NPI in uploaded PDFs | Over-exposure to AI vendor | **Medium** | High | Paid Gemini tier (no training, no human review); see §6 and Data Inventory | **Medium — see Open Items** |
| Stored loan metadata / scan history | Unauthorized access | Low | Medium | Google OAuth auth; per-account scoping | Low |
| Account/profile data (Supabase) | Provider breach | Low | Medium | Reputable provider; encrypted at rest/in transit; least-privilege keys | Low |
| Billing data (Stripe) | Card data exposure | Low | High | Stripe is PCI-DSS Level 1; we never see/store card numbers | Low |
| Secrets (API keys, tokens) | Leakage | Low | High | Stored in host env vars; `.env`/config gitignored; not in source | Low |
| Local SQLite (`processor.db`) on host | Loss / unauthorized access | [TODO] | Medium | [TODO: confirm volume + encryption] | **See Open Items** |

Full assessment worksheet: [TODO: link or appendix].

## 4. Safeguards Implemented (§314.4(c))

### 4.1 Access controls & identity
- End-user authentication via **Google OAuth** (delegated identity; no passwords stored by us).
- Administrative access to hosting (Railway), database (Supabase), AI (Google), and
  billing (Stripe) consoles is restricted to the Qualified Individual.
- **MFA is enabled** on all administrative accounts (Google, Railway, Supabase,
  Stripe, GitHub). [TODO: confirm each is on.]
- Access is least-privilege; service keys are scoped where the provider allows.

### 4.2 Data inventory & classification
- Maintained in [data_inventory_and_vendors.md](data_inventory_and_vendors.md).
- Data classes: **NPI** (borrower PII/financial), **account data**, **operational
  metadata**, **secrets**.

### 4.3 Encryption (§314.4(c)(3))
- **In transit:** All traffic is HTTPS/TLS (web app, Supabase, Google APIs, Stripe).
- **At rest:** Supabase (Postgres) encrypts data at rest. [TODO: confirm
  at-rest encryption / volume encryption for the host's local `processor.db`.]

### 4.4 Document handling (data minimization)
- Uploaded PDFs are processed **transiently for the scan only** and are **not
  persisted** by the Service.
- The Service stores only non-sensitive extracted fields, loan metadata, and recent
  scan history tied to the signed-in account.
- A local redaction filter (`privacy_filter.py`) can strip SSNs, account numbers,
  and similar values before any text is sent to the cloud. **NOTE:** the redaction
  path is **not** active in the default PDF-vision mode — see Open Items #1.

### 4.5 Secure development & change management
- Source controlled in Git/GitHub; changes reviewed before deploy.
- Secrets are never committed (`.env`, `cloud_config.json` are gitignored).
- Dependencies are pinned in `requirements.txt`. [TODO: periodic dependency review.]

### 4.6 Logging & monitoring (§314.4(c)(8))
- Application logs scan activity and billing events.
- Host (Railway) provides deploy and runtime logs.
- [TODO: define a monthly log-review cadence and who performs it.]

### 4.7 Secure disposal (§314.4(c)(6))
- NPI no longer needed is deleted; "Removed Loans" trash supports retention limits.
- [TODO: document a data-retention schedule and a deletion procedure for
  account-closure / customer requests.]

## 5. Testing & Monitoring (§314.4(d))
- [TODO] At least annual review of access lists, vendor security posture, and this
  WISP.
- [TODO] Periodic vulnerability check of the deployed app (e.g., dependency scan,
  basic security review). Continuous monitoring or annual pen test as the user base
  grows.

## 6. Service Provider Oversight (§314.4(f))
Each provider that touches NPI is selected for adequate safeguards and bound by its
terms/DPA. See [data_inventory_and_vendors.md](data_inventory_and_vendors.md) for
the list, what each handles, and links to their security/DPA documentation. Reviewed
at least annually.

## 7. Incident Response (§314.4(h))
Maintained separately in [incident_response_plan.md](incident_response_plan.md).

## 8. Reporting (§314.4(i))
The Qualified Individual prepares a written report at least annually covering the
program's status, risk-assessment results, incidents, and recommended changes.
Because the business is currently a sole operator, the report is self-directed and
retained in this folder. Latest report: [TODO].

## 9. Program Evaluation & Adjustment (§314.4(g))
This WISP is reviewed and updated at least annually and upon any material change
(new vendor, new data type, security incident, significant feature change).

---

## Open Items (must resolve for full accuracy)

1. **AI data exposure vs. UI claim.** In default PDF-vision mode the full,
   unredacted PDF is sent to Google Gemini, while a scanner checkbox label says
   "only redacted condition text is sent." Resolve by (a) correcting the label to
   reflect reality, and/or (b) routing cloud scans through the redaction filter.
   Until resolved, do not claim "redacted before AI."
2. **Local `processor.db` durability & encryption.** Confirm whether loan/CRM data
   lives on an encrypted, persistent volume vs. ephemeral container storage.
3. **MFA confirmation** on every admin account (Google, Railway, Supabase, Stripe, GitHub).
4. **DPAs / data-processing terms** executed and filed for Google, Supabase, Railway, Stripe.
5. **Retention & deletion schedule** documented, including customer-offboarding deletion.
6. **Annual report + risk-assessment worksheet** completed and dated.
