# Incident Response Plan
### Processor Assistant — supports WISP §7 / Safeguards Rule §314.4(h)

**Status:** DRAFT · **Owner / Incident Lead:** Brice Leasure · **Last reviewed:** [TODO]

> Not legal advice. A security event involving consumer financial data may trigger
> **state breach-notification laws** and, for some entities, federal notification
> duties. Consult counsel promptly during any real incident.

## 1. What counts as a security event
Any actual or suspected unauthorized access to, acquisition of, loss of, or misuse
of NPI or systems that hold it — e.g., leaked API key, compromised admin account,
vendor breach (Google/Supabase/Railway/Stripe), malware, or accidental exposure.

## 2. Roles
- **Incident Lead:** Brice Leasure — coordinates response, decisions, comms.
- **Backup contact:** [TODO].
- **Outside help:** [TODO — attorney, and a security/IR contact if available].

## 3. Response steps

1. **Detect & record.** Note date/time, what was observed, and who reported it.
   Start an incident log (one per incident) in this folder.
2. **Contain.** Rotate/revoke affected credentials immediately (Google, Supabase,
   Railway, Stripe, GitHub). Disable compromised accounts. Take affected components
   offline if needed.
3. **Assess scope.** What data/systems were involved? Was NPI exposed? Whose? How
   much? Pull logs (app, Railway, provider).
4. **Eradicate & recover.** Remove the cause (patch, key rotation, config fix),
   restore from known-good state, verify integrity before resuming.
5. **Notify.**
   - Affected **service providers** (e.g., report to Google/Supabase/Stripe if theirs).
   - **Legal counsel** to determine notification obligations.
   - **Affected individuals / institutions** and regulators **as required by law**
     and your customer contracts — within applicable deadlines.
6. **Document & close.** Complete the incident log: timeline, root cause, data
   involved, actions taken, notifications made.
7. **Learn.** Update the risk assessment and WISP; implement fixes to prevent
   recurrence.

## 4. Key contacts (fill in)

| Need | Contact |
|---|---|
| Legal counsel | [TODO] |
| Cyber insurance (if any) | [TODO] |
| Google Cloud/API support | [TODO] |
| Supabase support | [TODO] |
| Railway support | [TODO] |
| Stripe support | [TODO] |

## 5. Incident log template

```
Incident ID:        IR-YYYY-NN
Detected (date/time):
Reported by:
Summary:
Systems/data involved:
NPI exposed? (Y/N, scope):
Containment actions:
Root cause:
Notifications (who/when):
Resolution:
Lessons / changes:
Closed (date):
```
