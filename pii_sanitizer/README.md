# pii_sanitizer

Production-grade PII/NPI sanitization for documents on their way to an LLM.
Extract → OCR (if scanned) → detect → replace with deterministic placeholders →
send **only placeholders** to Gemini → restore the originals locally before the
user sees the result. The reverse map never leaves the machine.

Built to slot into this project's existing privacy layer (`privacy_filter.py` /
`cloud_client.py`) and to support future **GLBA / privacy-by-design** work.

---

## Why this exists

The existing `privacy_filter.py` is solid but regex-only. It catches structured
identifiers and *labeled* names (`Borrower: John Smith`) but not a bare
`John Smith`, and its scanned-PDF path just blocks. This package keeps the same
call surface while adding:

| Capability | `privacy_filter.py` | `pii_sanitizer` |
|---|---|---|
| Structured IDs (SSN, email, phone, loan/acct/routing) | ✅ | ✅ |
| Labeled names | ✅ generic `[PERSON]` | ✅ **typed** `[BORROWER_1]`, `[COBORROWER_1]` |
| Unlabeled names / orgs / places | ❌ | ✅ (NER: Presidio/spaCy) |
| Scanned/image PDFs | ⚠️ blocked | ✅ local OCR |
| QR / barcode payloads | ❌ | ✅ decoded + redacted |
| Deterministic per-value placeholders | partial | ✅ Vault |
| Encrypted mapping persistence + zeroization | ❌ | ✅ |
| PII-safe logging filter | ❌ | ✅ |
| Fail-closed cloud gate | ✅ | ✅ (categories-only errors) |

---

## Architecture

```
pii_sanitizer/
├── __init__.py          Public API (sanitize_pdf, sanitize_text, restore, Vault, ...)
├── config.py            SanitizerConfig: defaults ← file ← PII_* env vars
├── config.default.yaml  Documented default configuration
├── extraction.py        PDF → text; image/text detection; local OCR
├── detectors/
│   ├── regex_detector.py    Structured IDs + role-typed labeled names (no deps)
│   ├── ner_detector.py      Unlabeled names/orgs/places (Presidio → spaCy → noop)
│   └── barcode_detector.py  QR/barcode decode on rendered pages (pyzbar)
├── spans.py             Span model + priority-based overlap resolution
├── vault.py             Deterministic placeholder map; encrypt/zeroize
├── gate.py              Fail-closed residual-PII scan (categories-only errors)
├── sanitizer.py         Orchestrator: extract → detect → replace → gate
├── integration.py       Drop-in shim matching privacy_filter's signatures
├── logging_utils.py     RedactingFilter — scrubs PII from every log record
├── errors.py            Exception hierarchy
├── tests/               36 unit tests (run on the dependency-light core)
└── example/demo.py      Runnable original → sanitized → LLM → restored demo
```

**Data-flow guarantee:** the only string that crosses the network boundary is
`SanitizationResult.sanitized_text`. The `Vault` (reverse map) is never
serialized to any network call anywhere in this package.

---

## Install

Core (works today with what the app already has — `pypdf`, `cryptography`):

```bash
pip install -r pii_sanitizer/requirements-sanitizer.txt
python -m spacy download en_core_web_lg   # enables unlabeled-name NER
```

Every heavy dependency is **optional** and degrades gracefully:
- No OCR libs → scanned pages fail closed (strict) or are skipped (non-strict).
- No NER libs → regex-only detection, logged once as a warning.
- No `pyzbar` → visual-code scan skipped (visual codes never leak via text anyway).

---

## Usage

```python
from pii_sanitizer import sanitize_pdf, restore

result = sanitize_pdf(pdf_bytes)                 # local: extract, OCR, redact
assert result.is_cloud_safe                      # gate passed

response = call_gemini(result.sanitized_text)    # ONLY placeholders leave
final = restore(response, result.vault)          # originals restored locally
show_to_user(final)

result.vault.close()                             # zeroize the mapping
```

Feed known values from your DB (most reliable signal — exact, typed):

```python
result = sanitize_pdf(
    pdf_bytes,
    known_values={"John Smith": "BORROWER", "Wells Fargo": "LENDER"},
)
```

### Drop-in for `cloud_client.py`

Your client already does `redact_for_cloud(...)` / `restore_local_placeholders(...)`.
Change one import to get NER + OCR + typed placeholders with zero call-site edits:

```python
# from privacy_filter import redact_for_cloud, restore_local_placeholders, require_cloud_safe
from pii_sanitizer.integration import redact_for_cloud, restore_local_placeholders, require_cloud_safe
```

`redact_for_cloud` returns the same `(sanitized_text, {placeholder: original}, leaks)`
tuple, so the surrounding code (which passes the dict to
`restore_local_placeholders` after the response) keeps working unchanged.

---

## Configuration

Precedence: **built-in defaults → config file → `PII_*` env vars.**

```bash
export PII_CONFIG_FILE=pii_sanitizer/config.default.yaml
export PII_ENABLE_NER=false          # e.g. disable NER on a small Railway box
export PII_OCR_DPI_SCALE=2.5
export PII_ENABLED_ENTITIES=EMAIL,PHONE,SSN,BORROWER
```

Key fields (see `config.default.yaml` for all): `ocr_enabled`, `enable_ner`,
`enable_barcode`, `ner_model`, `strict_gate`, `redact_money`, `redact_logs`,
`tesseract_cmd`, `encrypted_spill_dir`.

---

## Security properties

- **Nothing sensitive is sent to the LLM.** Enforced by the fail-closed gate,
  which re-scans the sanitized text and raises `LeakDetectedError` on any
  residual structured PII (`strict_gate=True`).
- **Mapping stays local.** The `Vault` is in-memory by default; optional
  persistence is Fernet-encrypted (AES-128-CBC + HMAC) with a key from your
  secret manager, never from code.
- **No PII in logs.** `RedactingFilter` scrubs every log record (message + args),
  including debug logs. Gate/exception messages carry **category names only**
  (`ssn`, `email`) — never the offending value.
- **Zeroization.** `Vault.close()` overwrites in-memory originals and drops all
  references; use it (or the context manager) per document.
- **Per-document isolation.** Create a fresh `Vault` per document so placeholder
  numbering never crosses customers/tenants.

> Scope note: the gate reliably catches *structured* identifiers. Free-text
> names rely on the detection layers (regex roles + NER); there is no
> general-purpose "name gate" because it cannot be done without unacceptable
> false positives. Feed `known_values` from your LOS/DB for guaranteed name
> coverage.

---

## Testing

```bash
python -m pytest pii_sanitizer/tests -q      # 36 tests, no heavy deps required
python -m pii_sanitizer.example.demo         # see the full round-trip
```

The core (vault, regex, gate, sanitize/restore round-trip, config, logging) is
covered without OCR/NER installed, so CI stays fast and hermetic.
```
