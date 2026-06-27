# Processor Assistant — Compliance & Security Documentation

This folder is the **audit binder** for Processor Assistant's information-security
and GLBA Safeguards Rule readiness. Keep it current; an examiner or a customer's
vendor-risk team will ask for most of these.

> **IMPORTANT — read first.** These documents are working drafts prepared to get
> you organized and audit-ready. They are **not legal advice** and have **not**
> been reviewed by an attorney or a qualified compliance professional. Before you
> rely on them or publish compliance claims, have a GLBA/privacy professional
> review them against your actual operations. Fill in every `TODO` / `[BRACKET]`
> placeholder.

## Contents

| File | Purpose | Safeguards Rule § |
|---|---|---|
| [WISP.md](WISP.md) | Written Information Security Program — the master document | 314.4 (whole rule) |
| [data_inventory_and_vendors.md](data_inventory_and_vendors.md) | What data we hold, where it flows, and our service providers | 314.4(c)(2), 314.4(f) |
| [incident_response_plan.md](incident_response_plan.md) | What we do if there's a breach | 314.4(h) |
| [audit_checklist.md](audit_checklist.md) | One-page readiness checklist + open items | — |

## What GLBA's Safeguards Rule actually requires (plain English)

The Rule does **not** require zero data retention. It requires a financial
institution to maintain a written program with reasonable administrative,
technical, and physical safeguards. The nine core elements:

1. Designate a **Qualified Individual** to run the program.
2. Conduct a **written risk assessment**.
3. **Design and implement safeguards** (access control, encryption, MFA, data
   inventory, secure disposal, change management, monitoring).
4. **Regularly test or monitor** the effectiveness of those safeguards.
5. **Train** staff on security.
6. **Oversee service providers** (contracts requiring safeguards + periodic review).
7. Maintain a written **incident response plan**.
8. Have the Qualified Individual **report periodically** to ownership/board.
9. **Evaluate and adjust** the program as the business changes.

Each is addressed in [WISP.md](WISP.md).

**Last updated:** [TODO: date] · **Owner:** Brice Leasure
