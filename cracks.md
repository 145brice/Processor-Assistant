# CRACKS.md - Processor Traien Audit Report

**Auditor:** Senior Dev Mode  
**Date:** 2026-03-31  
**Last Re-Check:** 2026-03-31  

---

## ✅ FIXED CRACKS (Previously Critical)

### 1. `ai_engine.py:acknowledge_document()` - PDF Parse Crash
**Status:** ✅ FIXED  
**Fix applied:** Empty bytes check, try/except around PdfReader, encryption check, returns error dict

---

### 2. `ai_engine.py:process_document()` - No PDF Validation
**Status:** ✅ FIXED  
**Fix applied:** Doc type whitelist validation added, empty text check improved

---

### 4. `db.py:save_result()` - No Payload Size Limit
**Status:** ✅ FIXED  
**Fix applied:** `MAX_FIELD_SIZE = 500_000` truncation on conditions, risks, bank_rules

---

### 5. `db.py:log_pattern()` - Silent Failure
**Status:** ✅ FIXED  
**Fix applied:** Now logs with `logging.warning(f"log_pattern failed for {doc_type}: {e}")`

---

### 6. `db.py:get_history()` - No Input Validation on Limit
**Status:** ✅ FIXED  
**Fix applied:** `limit = max(1, min(limit, 1000))`

---

### 7. `app.py:show_dashboard()` - Condition Parsing Fragile
**Status:** ✅ FIXED  
**Fix applied:** Added `skipped_rows` counter with warning display

---

### 8. `app.py` - No Server-Side File Type Validation
**Status:** ✅ FIXED  
**Fix applied:** `if not pdf_bytes or not pdf_bytes[:5].startswith(b'%PDF-')` validation

---

### 9. `ai_engine.py` - Sensitive Doc Type Bypass
**Status:** ✅ FIXED  
**Fix applied:** Whitelist validation: `if doc_type not in SENSITIVE_DOC_TYPES and doc_type not in NON_SENSITIVE_DOC_TYPES`

---

### 10. `prompts.py` - Template Substitution Missing Key
**Status:** ✅ FIXED  
**Fix applied:** All calls now use `safe_substitute()` instead of `substitute()`

---

### 11. `db.py:signup()` - No Client-Side Password Validation
**Status:** ✅ FIXED  
**Fix applied:** `if len(password) < 6: return {"error": "Password must be at least 6 characters"}`

---

### 12. `ai_engine.py:extract_text_from_pdf()` - No Encryption Handling
**Status:** ✅ FIXED  
**Fix applied:** `if reader.is_encrypted: return ""`

---

## REMAINING CRACKS

### 1. `app.py:show_sidebar()` - Sandbox Mode Client-Side Only
**Line:** ~175-185  
**Test:** Modify `st.session_state.sandbox_mode` via browser dev tools  
**Result:** PASSES - Sandbox doesn't grant privileges, cosmetic only  
**Risk:** LOW - Confusing but not exploitable for privilege escalation  
**Status:** ⚠️ ACCEPTABLE - Not critical for current design

---

### 2. `db.py:login()` - No Rate Limiting
**Line:** ~48-58  
**Test:** Rapid repeated login attempts  
**Result:** FAILS - Supabase may rate limit, but app doesn't  
**Risk:** MEDIUM - Brute force possible at app level  
**Fix needed:** Add rate limiting middleware (e.g., `slowapi` or Redis-based)

---

### 3. `ai_engine.py:_call_ai()` - No Timeout on AI Calls
**Line:** ~60-68  
**Test:** AI API hangs indefinitely  
**Result:** FAILS - No timeout specified in `client.chat.completions.create()`  
**Risk:** MEDIUM - Request hangs, user sees infinite loading  
**Fix needed:** Add `timeout=30.0` to OpenAI client or call

---

### 4. `ai_engine.py:process_document()` - Redundant Condition Check
**Line:** ~237-245  
**Test:**
```python
# After empty text check at line 237, line 244 checks again
if not text or len(text.strip()) < 50:  # Redundant - text already checked
```
**Result:** PASSES - Works correctly, just redundant code  
**Risk:** LOW - Dead code, minor confusion  
**Fix needed:** Remove redundant `if not text` check on line 244

---

### 5. `app.py:show_dashboard()` - `del pdf_bytes` Doesn't Guarantee Memory Clear
**Line:** ~250, ~258  
**Test:** Upload massive PDF (500MB+)  
**Result:** PASSES - Python GC eventually clears, but no immediate guarantee  
**Risk:** LOW - Memory spike possible with large files  
**Fix needed:** Consider streaming processing or explicit file size limits

---

### 6. `db.py:get_supabase()` - Singleton Not Thread-Safe
**Line:** ~14-23  
**Test:** Concurrent requests in multi-threaded deployment  
**Result:** FAILS - Race condition on `_client` initialization  
**Risk:** LOW - Streamlit runs single-threaded per session, but would fail in FastAPI/Flask  
**Fix needed:** Use threading.Lock or lazy instantiation per-request

---

### 7. `app.py` - No File Size Limit on Upload
**Line:** ~215-220  
**Test:** Upload 1GB PDF  
**Result:** FAILS - Streamlit default limit may be too high or unlimited  
**Risk:** MEDIUM - Memory exhaustion, DoS  
**Fix needed:** Add `st.config` file size limit or check `len(pdf_bytes)` before processing

---

### 8. `ai_engine.py` - API Key Not Validated Before Use
**Line:** ~30-35  
**Test:** Empty or malformed API key  
**Result:** FAILS - Error only occurs at first AI call, not at startup  
**Risk:** LOW - Delayed error, confusing UX  
**Fix needed:** Validate API key format on module load

---

## CLEAN (No Cracks Found)

### 9. `ai_engine.py` - Sensitive vs Non-Sensitive Doc Type Separation
**Result:** ✅ PASSES - No overlap between sets

---

### 10. `prompts.py` - PII Protection Instructions
**Result:** ✅ PASSES - Prompts explicitly forbid PII output

---

### 11. `db.py` - Row Level Security
**Result:** ✅ PASSES - RLS policies in schema

---

### 12. `app.py` - Password Validation on Signup
**Result:** ✅ PASSES - ToS checkbox, password match, min length all checked

---

## SUMMARY

| Status | Count |
|--------|-------|
| ✅ FIXED | 12 |
| ⚠️ REMAINING | 8 |
| ✅ CLEAN | 4 |

**Remaining by severity:**
| Severity | Count |
|----------|-------|
| MEDIUM | 3 |
| LOW | 5 |

**Top 3 remaining to fix:**
1. **#7** - File size limit (DoS prevention)
2. **#2** - Rate limiting on login (brute force)
3. **#3** - AI call timeout (UX/reliability)

---

*End of Report*
