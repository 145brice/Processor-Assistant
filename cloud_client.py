"""
Cloud AI Integration — Processor Assistant
Optional cloud AI backend. Supports Anthropic Claude, Google Gemini, and OpenAI.
Requires an internet connection and a valid API key.

Providers:
  claude  → Anthropic Claude API  (claude-sonnet-4-6, claude-haiku-4-5, etc.)
  gemini  → Google Gemini API     (gemini-1.5-flash — free tier available)
  openai  → OpenAI API            (gpt-4o, gpt-4o-mini, etc.)

Falls back silently to script-only if unavailable or key is missing.
Logs every call mode to cloud_log.txt alongside the Ollama log.
"""

import json
import os
import re
import base64
import urllib.request
import urllib.error
import time
from datetime import datetime

from privacy_filter import (
    has_unresolved_placeholders,
    redact_for_cloud,
    redact_for_cloud_resilient,
    redact_gemini_output,
    require_cloud_safe,
    restore_local_placeholders,
    secure_approval_system_prompt,
)

_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
_CFG_FILE = os.path.join(_APP_DIR, "cloud_config.json")
_LOG_FILE = os.path.join(_APP_DIR, "cloud_log.txt")

DEFAULT_PROVIDER = "claude"
DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-6",
    "gemini": "gemini-2.5-flash",
    "openai": "gpt-4o-mini",
}

CLAUDE_ENDPOINT  = "https://api.anthropic.com/v1/messages"
OPENAI_ENDPOINT  = "https://api.openai.com/v1/chat/completions"
GEMINI_ENDPOINT  = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

GEMINI_RESPONSE_PRIVACY_INSTRUCTION = (
    "MANDATORY RESPONSE PRIVACY RULE: Before returning your answer, redact all "
    "Social Security numbers (SSNs), personal names, street or property addresses, "
    "phone numbers, email addresses, account and routing numbers, dates of birth, "
    "income figures, and any other personally identifiable information. Perform "
    "this redaction in your RESPONSE even if the input is not redacted. Return only "
    "the cleaned loan conditions, rewritten text, or requested structured output. "
    "Never repeat sensitive values from the input."
)


def _gemini_system(system: str) -> str:
    return f"{str(system or '').strip()}\n\n{GEMINI_RESPONSE_PRIVACY_INSTRUCTION}".strip()


def _gemini_prompt(prompt: str) -> str:
    return f"{str(prompt or '').strip()}\n\n{GEMINI_RESPONSE_PRIVACY_INSTRUCTION}".strip()

# ─────────────────────────────────────────────────────────────────────────────
# Vertex AI routing (optional, for Zero Data Retention / enterprise data terms)
#
# When VERTEX_PROJECT is set AND GEMINI_USE_VERTEX is truthy, every Gemini-format
# request is sent to Vertex AI (service-account auth) instead of the public
# Developer API (?key=). The request/response bodies are identical, so only the
# URL and auth header change. With ZDR approved on the project, this path retains
# no prompt/response data. If the env vars are unset, behavior is unchanged.
# ─────────────────────────────────────────────────────────────────────────────
VERTEX_PROJECT  = (os.getenv("VERTEX_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT") or "").strip()
VERTEX_LOCATION = (os.getenv("VERTEX_LOCATION") or "us-central1").strip()
_USE_VERTEX     = bool(VERTEX_PROJECT and (os.getenv("GEMINI_USE_VERTEX") or "").strip().lower()
                       in ("1", "true", "yes", "on"))
VERTEX_ENDPOINT = ("https://{loc}-aiplatform.googleapis.com/v1/projects/{proj}"
                   "/locations/{loc}/publishers/google/models/{model}:generateContent")

_vertex_token_cache = {"token": "", "exp": 0.0}


def _vertex_access_token() -> str:
    """Return a cached OAuth access token for Vertex from Application Default
    Credentials (service account JSON via GOOGLE_APPLICATION_CREDENTIALS, or the
    attached service account on GCP/Railway). Cached until ~1 min before expiry."""
    if _vertex_token_cache["token"] and _vertex_token_cache["exp"] - 60 > time.time():
        return _vertex_token_cache["token"]
    import google.auth  # lazy import; only needed on the Vertex path
    from google.auth.transport.requests import Request as _GoogleAuthRequest
    creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(_GoogleAuthRequest())
    _vertex_token_cache["token"] = creds.token
    _vertex_token_cache["exp"] = creds.expiry.timestamp() if creds.expiry else time.time() + 3000
    return creds.token


def _gemini_target(model: str, api_key: str) -> tuple[str, dict]:
    """Return (url, headers) for a Gemini-format request, routed to Vertex AI
    when configured, otherwise the public Developer API. Bodies are identical."""
    if _USE_VERTEX:
        url = VERTEX_ENDPOINT.format(loc=VERTEX_LOCATION, proj=VERTEX_PROJECT, model=model)
        return url, {"Content-Type": "application/json",
                     "Authorization": f"Bearer {_vertex_access_token()}"}
    return GEMINI_ENDPOINT.format(model=model, key=api_key), {"Content-Type": "application/json"}


def _parse_ai_json(text: str) -> dict:
    """Strip markdown fences / prose and extract the first valid JSON object.
    Gemini in particular often wraps responses in ```json ... ``` or adds preamble."""
    s = (text or "").strip()
    # Remove markdown code fences
    if s.startswith("```"):
        s = re.sub(r'^```(?:json|JSON)?\s*\n?', '', s)
        s = re.sub(r'\n?```\s*$', '', s)
        s = s.strip()
    # Try direct parse first
    try:
        return json.loads(s)
    except Exception:
        pass

    def _clean_json_candidate(candidate: str) -> str:
        candidate = candidate.strip()
        candidate = re.sub(r',\s*([}\]])', r'\1', candidate)
        return candidate

    def _repair_json_candidate(candidate: str) -> str:
        candidate = _clean_json_candidate(candidate)
        stack = []
        in_str = False
        esc = False
        for c in candidate:
            if esc:
                esc = False
                continue
            if c == '\\' and in_str:
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == '{':
                stack.append('}')
            elif c == '[':
                stack.append(']')
            elif c in ('}', ']') and stack and stack[-1] == c:
                stack.pop()
        if in_str:
            candidate += '"'
        candidate = _clean_json_candidate(candidate)
        return candidate + ''.join(reversed(stack))

    # Fallback: find the largest balanced {...} block
    start = s.find('{')
    if start == -1:
        raise ValueError("No JSON object found in AI response")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        c = s[i]
        if esc:
            esc = False
            continue
        if c == '\\' and in_str:
            esc = True
            continue
        if c == '"':
            in_str = not in_str
            continue
        if in_str:
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return json.loads(_clean_json_candidate(s[start:i+1]))

    repaired = _repair_json_candidate(s[start:])
    try:
        return json.loads(repaired)
    except Exception as e:
        raise ValueError(f"Unbalanced JSON in AI response: {str(e)[:80]}")


_LEFTOVER_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]*\]")
_PLACEHOLDER_LABELS = {
    "AMOUNT": "the amount",
    "PERSON": "the named party",
    "EMAIL": "the email",
    "PHONE": "the phone number",
    "SSN": "the SSN",
    "ACCOUNT_NUMBER": "the account number",
    "DATE_OF_BIRTH": "the date of birth",
    "EXACT_DATE": "the date",
    "ADDRESS": "the property address",
    "KNOWN_VALUE": "the provided detail",
    "INCOME_AMOUNT": "the income amount",
    "PROPERTY_IDENTIFIER": "the property identifier",
    "INCOME_INFORMATION_REDACTED": "income information",
    "PROPERTY_IDENTIFIER_REDACTED": "the property identifier",
}


def _strip_repeated_boilerplate(text: str, min_repeats: int = 3) -> str:
    """Drop lines that repeat across pages - the loan-summary header/footer that
    prints identically on every page and buries the real conditions in noise.

    A line must appear at least ``min_repeats`` times to count as boilerplate, and
    short lines (signoff codes like 'A'/'C', bare numbers) are never stripped so
    condition markers survive. The first occurrence of each repeated line is kept
    for context; later duplicates are removed."""
    from collections import Counter
    lines = text.split("\n")

    def _norm(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip()).lower()

    counts = Counter(_norm(l) for l in lines if len(_norm(l)) >= 8)
    repeated = {k for k, c in counts.items() if c >= min_repeats}
    if not repeated:
        return text
    out, seen = [], set()
    for l in lines:
        n = _norm(l)
        if n in repeated:
            if n in seen:
                continue
            seen.add(n)
        out.append(l)
    return "\n".join(out)


def _neutralize_placeholders(text: str) -> str:
    """Replace any redaction placeholders the model didn't echo back verbatim with
    neutral wording, so one un-restored token never discards an otherwise-valid
    extraction. Privacy is unaffected: placeholders contain no real PII (the
    outbound text was already verified cloud-safe before the call)."""
    def _label(match: re.Match[str]) -> str:
        token = match.group(0)[1:-1]
        base = re.sub(r"_\d+$", "", token)
        return _PLACEHOLDER_LABELS.get(base, _PLACEHOLDER_LABELS.get(token, "the redacted detail"))
    return _LEFTOVER_PLACEHOLDER_RE.sub(_label, text)


def _filter_invoice_conditions(conditions: list[dict]) -> list[dict]:
    """Remove internal invoice items, but keep HOI/current-agent requests."""
    filtered = []
    for cond in conditions:
        desc = str(cond.get("desc", "")).lower()
        if re.search(r"\binvoice\b", desc) and not any(
            k in desc for k in ("hoi", "homeowner", "homeowners", "hazard insurance", "insurance agent", "current agent")
        ):
            continue
        filtered.append(cond)
    return filtered


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

def get_config() -> dict:
    cfg = None
    if not os.path.exists(_CFG_FILE):
        cfg = {
            "enabled":  False,
            "provider": DEFAULT_PROVIDER,
            "api_key":  "",
            "model":    DEFAULT_MODELS[DEFAULT_PROVIDER],
        }
    else:
        try:
            with open(_CFG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {"enabled": False, "provider": DEFAULT_PROVIDER, "api_key": "", "model": ""}

    # For Gemini, prefer the signed-in user's saved Supabase key over the machine-wide file.
    try:
        import streamlit as st
        session_key = str(st.session_state.get("user_gemini_api_key", "")).strip()
        if session_key:
            cfg = dict(cfg)
            current_model = str(cfg.get("model", "")).strip()
            cfg["enabled"] = True
            cfg["provider"] = "gemini"
            cfg["api_key"] = session_key
            cfg["model"] = current_model if current_model.startswith("gemini") else DEFAULT_MODELS["gemini"]
    except Exception:
        pass

    # Railway does not carry ignored local cloud_config.json, so allow env vars.
    if not cfg.get("api_key"):
        env_options = [
            ("gemini", os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            ("claude", os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")),
            ("openai", os.getenv("OPENAI_API_KEY")),
        ]
        for provider, api_key in env_options:
            if api_key:
                cfg = dict(cfg)
                cfg["enabled"] = True
                cfg["provider"] = provider
                cfg["api_key"] = api_key.strip()
                cfg["model"] = os.getenv(f"{provider.upper()}_MODEL") or DEFAULT_MODELS[provider]
                break

    return cfg


def save_config(enabled: bool, provider: str, api_key: str, model: str) -> dict:
    # Backfill blanks so saved file always has the canonical Gemini defaults
    provider = (provider or "").strip().lower() or "gemini"
    model = (model or "").strip() or DEFAULT_MODELS.get(provider, DEFAULT_MODELS["gemini"])
    cfg = {
        "enabled":  enabled,
        "provider": provider,
        "api_key":  api_key.strip(),
        "model":    model,
    }
    with open(_CFG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg


def is_enabled() -> bool:
    cfg = get_config()
    return bool(cfg.get("enabled") and cfg.get("api_key"))


# ─────────────────────────────────────────────────────────────────────────────
# Connection test
# ─────────────────────────────────────────────────────────────────────────────

def ping(provider: str | None = None, api_key: str | None = None,
         model: str | None = None) -> tuple[bool, str]:
    """
    Test the cloud API connection with a minimal prompt.
    Returns (success, message).
    NOTE: This makes a real (but tiny) API call — costs a fraction of a cent.
    """
    cfg = get_config()
    provider = provider or cfg.get("provider", DEFAULT_PROVIDER)
    api_key  = api_key  or cfg.get("api_key", "")
    model    = model    or cfg.get("model", DEFAULT_MODELS.get(provider, ""))

    if not api_key:
        return False, "No API key configured"

    try:
        response = _generate("Reply with: OK", "Reply with OK and nothing else.",
                             provider, api_key, model, timeout=15)
        if response:
            return True, f"Connected  {provider}  {model}"
        return False, "Empty response"
    except urllib.error.HTTPError as e:
        # Read Anthropic/OpenAI error body so the user sees the actual reason
        try:
            _body = e.read().decode("utf-8", errors="replace")
            _err_msg = ""
            try:
                _ej = json.loads(_body)
                _err_msg = _ej.get("error", {}).get("message", "") or _ej.get("message", "") or _body[:200]
            except Exception:
                _err_msg = _body[:200]
        except Exception:
            _err_msg = e.reason
        if e.code == 401:
            return False, f"Invalid API key (401): {_err_msg}"
        if e.code == 429:
            return False, f"Rate limited (429): {_err_msg}"
        if e.code == 400:
            return False, f"Bad request (400): {_err_msg}"
        return False, f"HTTP {e.code}: {_err_msg}"
    except urllib.error.URLError as e:
        return False, f"Cannot reach {provider} API: {e.reason}"
    except Exception as e:
        return False, str(e)[:80]


# ─────────────────────────────────────────────────────────────────────────────
# Core generate
# ─────────────────────────────────────────────────────────────────────────────

def _generate(prompt: str, system: str, provider: str, api_key: str,
              model: str, timeout: int = 60) -> str:
    last_error = None
    for attempt in range(3):
        try:
            if provider == "claude":
                return _generate_claude(prompt, system, model, api_key, timeout)
            elif provider == "gemini":
                return _generate_gemini(prompt, system, model, api_key, timeout)
            elif provider == "openai":
                return _generate_openai(prompt, system, model, api_key, timeout)
            else:
                raise ValueError(f"Unknown provider: {provider}")
        except urllib.error.HTTPError as e:
            last_error = e
            if e.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except urllib.error.URLError as e:
            last_error = e
            if attempt == 2:
                raise
        time.sleep(1.2 * (attempt + 1))
    if last_error:
        raise last_error
    return ""


def _friendly_cloud_error(e: Exception) -> str:
    if isinstance(e, urllib.error.HTTPError):
        if e.code in (500, 502, 503, 504):
            return f"temporary cloud API unavailable ({e.code}); used local fallback"
        if e.code == 429:
            return "cloud API rate limited (429); used local fallback"
        if e.code in (401, 403):
            return f"cloud API authorization failed ({e.code}); used local fallback"
        return f"cloud API HTTP {e.code}; used local fallback"
    if isinstance(e, urllib.error.URLError):
        return "cloud API unreachable; used local fallback"
    return f"cloud fallback used: {str(e)[:80]}"


def _generate_claude(prompt: str, system: str, model: str,
                     api_key: str, timeout: int) -> str:
    payload = json.dumps({
        "model":      model,
        "max_tokens": 2048,
        "system":     system,
        "messages":   [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        CLAUDE_ENDPOINT,
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"].strip()


def _generate_gemini(prompt: str, system: str, model: str,
                     api_key: str, timeout: int) -> str:
    source_text = f"{system}\n\n{prompt}" if system else prompt
    full_prompt = f"{_gemini_system(system)}\n\n{_gemini_prompt(prompt)}"
    # If the system prompt asks for JSON, force JSON mode so Gemini doesn't wrap output
    _gen_cfg = {"maxOutputTokens": 8192, "temperature": 0.15}
    if system and "json" in system.lower():
        _gen_cfg["responseMimeType"] = "application/json"
    payload = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": _gen_cfg,
    }).encode("utf-8")
    url, _gem_headers = _gemini_target(model, api_key)
    req = urllib.request.Request(
        url, data=payload,
        headers=_gem_headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return redact_gemini_output(raw, source_text=source_text)


def _generate_openai(prompt: str, system: str, model: str,
                     api_key: str, timeout: int) -> str:
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system",  "content": system},
            {"role": "user",    "content": prompt},
        ],
        "max_tokens":  2048,
        "temperature": 0.15,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENAI_ENDPOINT,
        data=payload,
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()


# ─────────────────────────────────────────────────────────────────────────────
# Processing log
# ─────────────────────────────────────────────────────────────────────────────

def _ascii_log_text(value: str) -> str:
    text = str(value or "")
    replacements = {
        "": "-",
        "": "-",
        "—": "-",
        "–": "-",
        "": "-",
        "": "-",
        "": "->",
        "": "...",
    }
    # Guard against corrupted empty-string keys that would inject separators
    # between every character (e.g., "C...L...O...U...D").
    replacements.pop("", None)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("ascii", errors="ignore").decode("ascii").strip()


def _log(mode: str, feature: str, note: str = "") -> str:
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mode = _ascii_log_text(mode).upper()
    feature = _ascii_log_text(feature)
    note = _ascii_log_text(note)
    line = f"[{ts}] {mode:14s} | {feature}"
    if note:
        line += f"  ({note})"
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
    return line


def get_recent_log(n: int = 30) -> list[str]:
    if not os.path.exists(_LOG_FILE):
        return []
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [ln.rstrip() for ln in lines[-n:]]
    except Exception:
        return []


def clear_log():
    try:
        open(_LOG_FILE, "w").close()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Enhanced condition extraction
# ─────────────────────────────────────────────────────────────────────────────

def enhance_conditions(text: str, doc_type: str,
                       script_conditions: str,
                       known_values=None) -> tuple[str, str]:
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return script_conditions, _log("SCRIPT", "condition_extraction", "Cloud disabled")

    safe_text, text_replacements, text_forced, text_leaks = redact_for_cloud_resilient(
        text,
        known_values=known_values,
    )
    safe_conditions, condition_replacements, condition_forced, condition_leaks = redact_for_cloud_resilient(
        script_conditions,
        known_values=list(known_values or []) + list(text_replacements.values()),
    )
    local_replacements = dict(text_replacements)
    local_replacements.update(condition_replacements)
    leaks = sorted(set(text_leaks + condition_leaks))
    if leaks:
        return script_conditions, _log("PRIVACY BLOCK", "condition_extraction", ", ".join(leaks))
    try:
        require_cloud_safe(safe_text)
        require_cloud_safe(safe_conditions)
    except ValueError as e:
        return script_conditions, _log("PRIVACY BLOCK", "condition_extraction", str(e))

    system = secure_approval_system_prompt(
        "You are an expert mortgage condition parser. Extract only real lender "
        "conditions from approval documents. If the lender/format is familiar from "
        "the document patterns, label the row High Confidence. If you are making an "
        "educated inference from a new or unclear format, label it Best Guess. Never "
        "invent conditions that are not present in the document."
    )
    prompt = f"""Extract EVERY underwriting condition from this {doc_type}.

The DOCUMENT below is the source of truth. The SCRIPT-EXTRACTED list is only a
partial hint - it routinely MISSES conditions, so never limit yourself to it.

DOCUMENT (first 24000 chars):
{safe_text[:24000]}

SCRIPT-EXTRACTED CONDITIONS (partial hint only - expect to find more):
{safe_conditions[:4000]}

How conditions appear (lenders use hundreds of different layouts):
- Rows are often tagged with a signoff/code column: S = Prior to Submission,
  A = Final Approval/Approved, C = Prior to Closing, F = Prior to Funding,
  P = Post-Close/Shipping (some lenders use PTA / PTD / PTF / PTP instead).
  EVERY row carrying such a code is a separate condition.
- Conditions may be numbered, lettered, bulleted, or written as standalone
  requirement paragraphs under a section header (Final Approval, Prior to Closing,
  Prior to Funding, etc.).
- The code/number is sometimes printed AFTER the condition text or in its own
  column - match each requirement to its text regardless of where the code sits.

Rules:
1. Read the ENTIRE document top to bottom - every section, every page. A typical
   approval letter has 10-30 conditions. If you are about to return only a few,
   you have missed many: scan again before answering.
2. Output one row per distinct requirement. Fold wrapped/detail lines (sub-items
   "1.", "2.", indented detail, and dated status notes like "01/24 - ...") INTO
   their parent condition's row - do not split them into separate conditions.
3. Include internal / underwriter / processor / funding conditions too - route
   them to the correct party rather than dropping them.
4. Preserve the full condition wording. Do not shorten or paraphrase.
5. Mark High Confidence for clear condition rows, Best Guess when the format is unclear.
6. Treat HOI / homeowner / hazard insurance items as Borrower tasks; the borrower
   provides their current insurance agent/contact.
7. Treat Real Estate Certification / FHA Amendatory Clause items as Borrower-facing.
8. Treat Final Seller/Selling Disclosure and any sale-of-current-home items as Borrower-facing.
9. Closing Disclosure routing: seller CD / sale-of-current-home CD goes to Borrower;
   subject-property CD, initial/final/preliminary CD, or full title package goes to Title.
10. Do not drop rows beginning with "Borrower to provide/must", "Buyer to provide",
    "Provide", "Please provide", or "All borrowers must".
11. Assign an ownership bucket from de-identified wording: Borrower, Lender, or
    Broker / Loan Officer. Use Best Guess whenever ownership is borderline so the
    processor can confirm it. Do not infer or reproduce redacted private content.

Return ONLY the conditions - no intro text, no headers, no explanations.
Use this exact pipe-delimited format, one condition per line:
| 1 | Full description of the condition | Borrower | Needed | High Confidence |
| 2 | Full description of the condition | Title | Needed | Best Guess |

Responsible party options: Borrower, Title, Underwriter, Insurance, Closer, Appraiser, Employer, Realtor, Seller, Processor
Status: always Needed
Confidence options: High Confidence, Best Guess"""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        if provider != "gemini":
            response = restore_local_placeholders(response, local_replacements)
        else:
            response = redact_gemini_output(
                response,
                source_text=f"{text}\n{script_conditions}",
            )
        if has_unresolved_placeholders(response):
            # A leftover placeholder is already-redacted (no real PII), so neutralize
            # it to readable wording instead of throwing away the whole extraction.
            response = _neutralize_placeholders(response)
        valid = [
            ln.strip() for ln in response.split("\n")
            if ln.strip().startswith("|") and ln.count("|") >= 4
        ]
        script_count = sum(
            1 for ln in script_conditions.split("\n")
            if re.match(r"^\|\s*\d+\s*\|", ln.strip())
        )
        if len(valid) >= max(1, script_count):
            renumbered = []
            for i, ln in enumerate(valid, 1):
                parts = [p.strip() for p in ln.split("|")]
                if len(parts) >= 5:
                    parts[1] = str(i)
                    renumbered.append("| " + " | ".join(parts[1:]) + " |")
                else:
                    renumbered.append(ln)
            result = "\n".join(renumbered)
            extra_redactions = sorted(set(text_forced + condition_forced))
            detail = f"{len(valid)} conditions  {provider}  {cfg.get('model')}"
            if extra_redactions:
                detail += "  extra local redaction: " + ", ".join(extra_redactions)
            log = _log("CLOUD-SANITIZED", "condition_extraction", detail)
            return result, log
        else:
            fallback = safe_conditions if provider == "gemini" else script_conditions
            return fallback, _log(
                "SCRIPT",
                "condition_extraction",
                "Cloud returned fewer conditions; kept local extraction",
            )
    except Exception as e:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        fallback = safe_conditions if provider == "gemini" else script_conditions
        return fallback, _log("SCRIPT", "condition_extraction",
                              _friendly_cloud_error(e))


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Guideline interpretation
# ─────────────────────────────────────────────────────────────────────────────

def interpret_guidelines(condition_text: str, chunks: list[dict]) -> tuple[str, str]:
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return "", _log("SCRIPT", "guideline_search", "Cloud disabled")

    chunk_text = ""
    for chunk in chunks[:6]:
        chunk_text += (
            f"\n── {chunk.get('source','?')}  page {chunk.get('page','?')} ──\n"
            f"{chunk.get('text','')[:600]}\n"
        )

    system = "You are a Fannie Mae and Freddie Mac guideline expert helping a mortgage processor clear a loan condition."
    prompt = f"""CONDITION FROM LENDER:
{condition_text}

RELEVANT GUIDELINE SECTIONS:
{chunk_text}

In 3–5 sentences:
1. Explain which guideline applies and what it requires
2. Tell the processor exactly what documentation satisfies this condition
3. Note any exceptions or special cases that are relevant

Be specific and actionable. Write for a working mortgage processor, not a lawyer."""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        log = _log("CLOUD", "guideline_search", f"{provider}  {cfg.get('model')}")
        return response, log
    except Exception as e:
        return "", _log("SCRIPT", "guideline_search", f"Cloud error: {str(e)[:60]}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Enhanced email drafting
# ─────────────────────────────────────────────────────────────────────────────

def draft_email_enhanced(conditions: list[dict], recipient_type: str,
                         language: str) -> tuple[str, str]:
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return "", _log("SCRIPT", "email_draft", "Cloud disabled")

    filtered_conditions = _filter_invoice_conditions(conditions)
    cond_list = "\n".join(
        f"- {c.get('desc', c.get('num', 'Item'))}" for c in filtered_conditions
    )
    rewrite_templates = {
        "borrower": (
            "Rewrite each mortgage condition in simple, friendly language a homebuyer "
            "without financial background would understand. Focus on what they need to do and why. "
            "Use conversational tone."
        ),
        "appraiser": (
            "Rewrite each condition clearly for a professional appraiser. Include the technical "
            "requirement but keep it concise and action-oriented."
        ),
        "realtor": (
            "Rewrite each condition briefly for a real estate agent. Make it clear and actionable "
            "in one or two sentences."
        ),
    }
    _rtype = str(recipient_type or "").strip().lower()
    if "borrower" in _rtype or "buyer" in _rtype:
        _prompt_role = "borrower"
    elif "appraiser" in _rtype:
        _prompt_role = "appraiser"
    elif "realtor" in _rtype or "agent" in _rtype:
        _prompt_role = "realtor"
    else:
        _prompt_role = "realtor"
    rewrite_instruction = rewrite_templates[_prompt_role]
    lang_instr = (
        "Escribe el correo en espaol formal y profesional."
        if language == "Spanish"
        else "Write in professional American English."
    )

    system = "You are a professional mortgage processor writing client-facing emails."
    prompt = f"""Write a document request email to a {recipient_type}.

{lang_instr}

Documents / items needed:
{cond_list}

Condition rewrite instruction:
{rewrite_instruction}

Write a complete, professional email body (no subject line needed). Include:
- A brief, warm opening explaining these items are needed to move the loan forward
- A clearly numbered list of exactly what is needed
- A polite note about timing/urgency if there are many items
- A professional closing

Do not use placeholder text like [NAME] or [DATE]. Just write the body as-is.
Keep it concise — under 300 words."""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        log = _log("CLOUD", "email_draft",
                   f"{recipient_type}  {language}  {provider}  {cfg.get('model')}")
        return response, log
    except Exception as e:
        return "", _log("SCRIPT", "email_draft", f"Cloud error: {str(e)[:60]}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Document summary
# ─────────────────────────────────────────────────────────────────────────────

def summarize_document(text: str, doc_type: str) -> tuple[str, str]:
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return "", _log("SCRIPT", "doc_summary", "Cloud disabled")

    system = "You are a mortgage expert who gives clear, actionable document summaries."
    prompt = f"""Summarize this {doc_type} for a processor who needs a quick overview.

DOCUMENT:
{text[:5000]}

In 5–8 bullet points, cover:
- What this document is and its purpose
- Key dates, dollar amounts, and parties involved
- Any conditions or requirements the borrower must meet
- Any red flags or items that need attention
- What action the processor should take next

Be concise. Each bullet should be one sentence."""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        log = _log("CLOUD", "doc_summary", f"{provider}  {cfg.get('model')}")
        return response, log
    except Exception as e:
        return "", _log("SCRIPT", "doc_summary", f"Cloud error: {str(e)[:60]}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Purchase contract AI extraction (handles any state form)
# ─────────────────────────────────────────────────────────────────────────────

_PC_JSON_TEMPLATE = """{
  "buyer": {"name": "", "phone": "", "email": ""},
  "seller": {"name": "", "phone": "", "email": ""},
  "property": {"address": ""},
  "transaction": {"purchase_price": "", "closing_date": "", "earnest_money": "", "down_payment": "", "seller_concessions": ""},
  "listing_agent": {"name": "", "brokerage": "", "phone": "", "email": ""},
  "selling_agent": {"name": "", "brokerage": "", "phone": "", "email": ""},
  "title": {"company": "", "contact": "", "phone": ""},
  "contingencies": {"inspection": "", "appraisal": "", "financing": ""},
  "addendums": []
}"""


def _smart_sample(raw_text: str, max_chars: int = 12000) -> str:
    """
    For purchase contracts, important data is scattered:
      - Buyer/seller/price/property at top (pages 1-3)
      - Title company, closing date in middle-late (pages 4-7)
      - Agent names, MLS, signatures at end (last 3 pages)
    For long documents, take top 30% + middle section with "Title" + bottom 40%.
    For short documents, return as-is.
    """
    if len(raw_text) <= max_chars:
        return raw_text

    # Strategy: top 30% + middle section with title company + bottom 40%
    third = len(raw_text) // 3
    top = raw_text[:third]

    # Find title company section in middle
    middle = raw_text[third : 2 * third]
    title_match = re.search(
        r"(title\s+(?:company|agent)|escrow|settlement|closing\s+agent).*?(?=\n\n|\Z)",
        middle,
        re.IGNORECASE | re.DOTALL
    )
    title_section = title_match.group(0) if title_match else ""

    bottom = raw_text[-int(len(raw_text) * 0.4) :]

    sampled = top + "\n\n[...document excerpt...]\n\n" + title_section + "\n\n[...document excerpt...]\n\n" + bottom
    if len(sampled) > max_chars:
        # Still too long, trim from middle
        sampled = sampled[:max_chars]
    return sampled


def _clean_extracted_contract_data(data: dict) -> dict:
    """
    Post-process extracted data to remove boilerplate and template text that made it through.
    """
    boilerplate_patterns = [
        r"^(REAL ESTATE )?PURCHASE.*CONTRACT",
        r"^paragraph\s+\d",
        r"^\d+\.\d+(\s|$)",  # section numbers like "3.1"
        r"^(as|will|shall|does)\s+(be\s+)?(specified|described|determined|represented)",
        r"insert.*herein?",
        r"^\[.*\]$",  # bracketed placeholders
        r"^__+$",  # blank lines
        r"^($|\s+)$",  # empty/whitespace only
        r"(?i)^set$",  # "set" or "Set" placeholder
        r"earnest.*money.*deposit",  # form label only
        r"REAL ESTATE PURCHASE CONTRACT",  # form title
        r"^endorsement as of",  # closing protection letter text
        r"^made by the lender",  # more boilerplate
        r"seller\s*signature",  # just a label
        r"closing\s+protection\s+letter",  # form header
    ]

    def is_boilerplate(text: str) -> bool:
        if not text or not text.strip():
            return True
        t = text.strip().lower()
        return any(re.match(pat, t, re.IGNORECASE) for pat in boilerplate_patterns)

    def clean_field(val):
        if isinstance(val, str):
            if is_boilerplate(val):
                return ""
            return val.strip()
        return val

    def clean_dict(d: dict) -> dict:
        if not isinstance(d, dict):
            return d
        return {k: clean_dict(v) if isinstance(v, dict) else clean_field(v) for k, v in d.items()}

    return clean_dict(data)


def chat(messages: list[dict], system: str = "") -> str:
    """
    Multi-turn chat call. `messages` is a list of {"role": "user"/"assistant", "content": "..."}.
    Returns the assistant reply as a string, or raises on error.
    """
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        raise RuntimeError("Cloud AI not enabled — add your API key in AI Settings")

    provider = cfg.get("provider", DEFAULT_PROVIDER)
    api_key  = cfg["api_key"]
    model    = cfg.get("model", DEFAULT_MODELS.get(provider, ""))

    if provider == "claude":
        payload = json.dumps({
            "model":      model,
            "max_tokens": 1024,
            "system":     system,
            "messages":   messages,
        }).encode("utf-8")
        req = urllib.request.Request(
            CLAUDE_ENDPOINT,
            data=payload,
            headers={
                "Content-Type":      "application/json",
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"].strip()

    elif provider == "gemini":
        # Gemini doesn't have a system role — prepend to first user message
        _gem_contents = []
        for i, m in enumerate(messages):
            role = "user" if m["role"] == "user" else "model"
            text = m["content"]
            if i == 0:
                text = f"{_gemini_system(system)}\n\n{_gemini_prompt(text)}"
            _gem_contents.append({"role": role, "parts": [{"text": text}]})
        payload = json.dumps({
            "contents": _gem_contents,
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.3},
        }).encode("utf-8")
        url, _gem_headers = _gemini_target(model, api_key)
        req = urllib.request.Request(
            url, data=payload,
            headers=_gem_headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            source_text = "\n".join(str(m.get("content", "")) for m in messages)
            return redact_gemini_output(raw, source_text=f"{system}\n{source_text}")

    elif provider == "openai":
        _msgs = []
        if system:
            _msgs.append({"role": "system", "content": system})
        _msgs.extend(messages)
        payload = json.dumps({
            "model":       model,
            "messages":    _msgs,
            "max_tokens":  1024,
            "temperature": 0.3,
        }).encode("utf-8")
        req = urllib.request.Request(
            OPENAI_ENDPOINT,
            data=payload,
            headers={
                "Content-Type":  "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()

    else:
        raise ValueError(f"Unknown provider: {provider}")


def extract_purchase_contract_ai(raw_text: str) -> tuple[dict, str]:
    """
    Use cloud AI only to normalize already-redacted contract terms.

    Identifying fields are removed locally before any network request.
    Returns (extracted_dict, log_line).
    """
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return {}, _log("SCRIPT", "pc_extract", "Cloud disabled")

    sanitized, _, leaks = redact_for_cloud(raw_text)
    if leaks:
        return {}, _log("PRIVACY BLOCK", "pc_extract", ", ".join(leaks))
    try:
        require_cloud_safe(sanitized)
    except ValueError as e:
        return {}, _log("PRIVACY BLOCK", "pc_extract", str(e))
    if not sanitized.strip():
        return {}, _log("SCRIPT", "pc_extract", "No safe contract terms to send")
    safe_text = sanitized[:16000]

    system = (
        "You normalize de-identified residential purchase-contract clauses. "
        "Never infer or invent identities, addresses, exact amounts, exact dates, "
        "or contact details. Preserve every bracketed redaction placeholder. "
        "Output only valid JSON with no markdown or commentary."
    )
    prompt = f"""Review only the sanitized contract language below.

Return valid JSON in exactly this shape:
{{
  "contingencies": {{"inspection": "", "appraisal": "", "financing": ""}},
  "addendums": [],
  "special_conditions": []
}}

Rules:
- Rewrite clauses clearly without changing their legal meaning.
- Keep bracketed placeholders exactly as written.
- Do not identify any person, company, property, or transaction.
- Do not reconstruct redacted amounts, dates, addresses, or identifiers.
- Use an empty value when the sanitized text does not support an answer.

SANITIZED CONTRACT LANGUAGE:
{safe_text}"""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        data = _parse_ai_json(response)
        data = {
            "contingencies": data.get("contingencies", {}),
            "addendums": data.get("addendums", []),
            "special_conditions": data.get("special_conditions", []),
        }
        log = _log("CLOUD-SANITIZED", "pc_extract", f"{provider}  {cfg.get('model')}")
        return data, log
    except Exception as e:
        return {}, _log("SCRIPT", "pc_extract", f"Cloud error: {str(e)[:80]}")


def extract_purchase_contract_ai_from_pdf(pdf_bytes: bytes) -> tuple[dict, str, str]:
    """
    Compatibility wrapper that never uploads PDF bytes.

    Text extraction is local. Image-only PDFs require a local OCR installation.
    Returns: (extracted_dict, log_line, ocr_text_hint)
    """
    try:
        import ai_engine
        text = ai_engine.extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        return {}, _log("SCRIPT", "pc_pdf_extract", f"Local PDF read failed: {str(e)[:80]}"), ""
    if len(text.strip()) < 50:
        return {}, _log("PRIVACY BLOCK", "pc_pdf_extract", "Image-only PDF; local OCR required"), ""
    local_data = ai_engine.extract_purchase_contract(text)
    safe_terms = ai_engine.build_purchase_contract_cloud_text(local_data)
    ai_terms, log = extract_purchase_contract_ai(safe_terms)
    return ai_engine._merge_pc_data(local_data, ai_terms), log, text

    # Legacy inline-PDF implementation retained below for reference only.
    # It is unreachable because document bytes must never leave the machine.
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return {}, _log("SCRIPT", "pc_pdf_extract", "Cloud disabled"), ""

    provider = cfg.get("provider", DEFAULT_PROVIDER)

    system = (
        "You analyze residential purchase contracts from PDF documents and return a structured JSON object. "
        "Output only valid JSON with no markdown and no commentary."
    )
    prompt = f"""Read this purchase contract PDF (including scanned/image pages) and extract:

- Purchase Price
- Property Address
- Closing Date
- Listing Agent Name (name, brokerage, phone, email)
- Selling Agent Name (name, brokerage, phone, email)
- Title Company
- Buyer Name(s)
- Seller Name(s)
- Earnest Money Deposit
- Down Payment Amount
- Loan Amount
- Any special conditions or contingencies

Return valid JSON in EXACTLY this shape (empty string "" if not present):

{_PC_JSON_TEMPLATE}

For amounts use digits only ("474500"). Never place a phone/email inside a name field.
"""
    try:
        # OCR PDF understanding path is Gemini-native in this client.
        # If active provider isn't Gemini, attempt GEMINI_API_KEY fallback.
        if provider == "gemini":
            api_key = cfg.get("api_key", "")
            model = cfg.get("model") or DEFAULT_MODELS["gemini"]
        else:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            model = DEFAULT_MODELS["gemini"]
        if not api_key:
            return {}, _log("SCRIPT", "pc_pdf_extract", "Gemini key missing for PDF OCR fallback"), ""

        payload = json.dumps({
            "system_instruction": {
                "parts": [{"text": _gemini_system(system)}]
            },
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("utf-8")}},
                    {"text": _gemini_prompt(prompt)},
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
            },
        }).encode("utf-8")
        url, _gem_headers = _gemini_target(model, api_key)
        req = urllib.request.Request(
            url, data=payload,
            headers=_gem_headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = redact_gemini_output(
            data["candidates"][0]["content"]["parts"][0]["text"].strip(),
            source_text=prompt,
        )
        parsed = _clean_extracted_contract_data(_parse_ai_json(txt))
        _note = f"gemini  {model}" if provider == "gemini" else f"gemini_fallback  {model}"
        return parsed, _log("CLOUD", "pc_pdf_extract", _note), ""
    except Exception as e:
        return {}, _log("SCRIPT", "pc_pdf_extract", f"Cloud error: {str(e)[:120]}"), ""


def extract_approval_conditions_ai_from_pdf(pdf_bytes: bytes, api_key_override: str = "") -> tuple[str, str, str]:
    """
    Extract approval-letter conditions.

    The default path is privacy-safe: local extraction -> redact -> sanitized text.
    Raw PDF vision is available only through the explicit PA_PDF_VISION opt-in.
    Returns: (pipe_delimited_conditions, log_line, text_hint)

    api_key_override: if provided, uses this key directly (bypasses cloud_config).
    Caller passes the user's onboarding Gemini API key.
    """
    try:
        import ai_engine
        text = ai_engine.extract_text_from_pdf(pdf_bytes)
    except Exception:
        text = ""

    def _local_text_path() -> tuple[str, str, str]:
        # Privacy-safe path: redact locally and send only sanitized text. Used as
        # the fallback whenever PDF vision is disabled or unavailable.
        if len(text.strip()) < 50:
            return "", _log("PRIVACY BLOCK", "approval_pdf_extract", "Image-only PDF; local OCR required"), ""
        clean_text = _strip_repeated_boilerplate(text)
        local_conditions = ai_engine.extract_conditions(clean_text, "Approval Letter")
        if not local_conditions.strip():
            return "", _log("SCRIPT", "approval_pdf_extract", "No local condition rows found"), text[:12000]
        _, repl, _ = redact_for_cloud(clean_text)
        conds, lg = enhance_conditions(
            clean_text, "Approval Letter", local_conditions, known_values=repl.values())
        return conds, lg, text[:12000]

    # PDF vision sends original document bytes to the cloud and therefore must
    # never be the implicit path. Only an explicit deployment-level opt-in can
    # enable it; otherwise all approval analysis starts after local redaction.
    _pdf_vision_on = (os.getenv("PA_PDF_VISION", "false").strip().lower() in ("1", "true", "yes", "on"))
    if api_key_override:
        provider = "gemini"
    else:
        cfg = get_config()
        provider = cfg.get("provider", DEFAULT_PROVIDER)
    if not _pdf_vision_on:
        return _local_text_path()
    system = secure_approval_system_prompt(
        "You are a precise mortgage processor reading underwriting approval letters. "
        "You extract every single numbered condition exactly as written in the PDF — "
        "no paraphrasing, no merging, no inventing. You preserve the original numbering "
        "within each section and tag every condition with its section code. You output "
        "only pipe-delimited rows. No markdown headers, no commentary, no preamble."
    )
    prompt = """Read this approval letter PDF carefully, including scanned/image pages.

Approval letters are typically organized into sections. Look for these section headers:
  - "Prior to Approval" or PTA
  - "Prior to Docs" or PTD
  - "Internal and At Closing" or AC
  - "Prior to Funding" or PTF
  - "Prior to Purchase" or PTP
  - "Loan Approval Conditions" or generic numbered lists
  - "Borrower Conditions", "Client Conditions", "Borrower Requirements",
    "Borrower to Provide", or any table/list of borrower-facing requirements

Extract EVERY condition from EVERY section. Do not skip any condition, even if:
  - it is in a Borrower/Client section
  - it is unnumbered but listed as a borrower requirement
  - it begins with "Borrower to provide", "Borrower must", "Buyer to provide",
    "All borrowers must", or similar borrower-facing wording
  - the section header is on a separate page

Do not merge separate numbered items into one row. Do not summarize - copy the wording
as written, including any "Updated" notes, asterisks, and stamped comments.

Borrower-facing conditions that must never be omitted:
  - HOI, homeowner's insurance, homeowners insurance, hazard insurance, insurance agent/contact, or HOI invoice
  - Real Estate Certification, Real Estate Cert, FHA Amendatory Clause, or Amendatory Clause
  - Final Seller Disclosure, Final Selling Disclosure, Final Sales Disclosure, Seller CD, or seller Closing Disclosure from the sale of the borrower's current home
  - Any other row under Borrower Conditions / Client Conditions / Borrower Requirements

Closing Disclosure routing:
  - Subject-property closing disclosure, initial CD, final CD, preliminary CD, or full title package request = Title
  - Seller closing disclosure / seller CD / CD from sale of current or departing home = Borrower

OUTPUT FORMAT — one condition per line, exactly five pipe-delimited fields:
| GLOBAL# | [SECTION-LOCAL#] Full condition text as written | Responsible | Needed | Confidence |

Where:
  GLOBAL# = sequential number across the whole letter (1, 2, 3, ...)
  SECTION-LOCAL# = bracketed prefix on the description: section tag + the number in the
                   PDF for that section. e.g. [PTD-1], [PTD-2], [AC-1], [PTF-1]
                   If the condition is unnumbered in a borrower/client section, use
                   [BOR-1], [BOR-2], etc. in its original order.
  Responsible = which party gets the request: Borrower, Title, Underwriter, Insurance,
                Closer, Appraiser, Employer, Realtor, Seller
  Status = always "Needed"
  Confidence = "High Confidence" if you copied wording verbatim, "Best Guess" if OCR was unclear

Example output (study this carefully — the prefix in brackets is part of the description):
| 1 | [PTD-1] Appraisal - 1004D with final photos - 1004-D TO SUPPORT ALL REPAIRS LISTED ON PAGE 1 OF 6 | Appraiser | Needed | High Confidence |
| 2 | [PTD-2] Document Expirations - Credit expiration 4/1; Income expiration 3/25; Asset expiration 3/9 | Borrower | Needed | High Confidence |
| 9 | [AC-1] Internal - Lock Desk to confirm pricing prior to CTC | Underwriter | Needed | High Confidence |
| 11 | [PTF-1] Funding - LQI Report - If loan has not funded by ____ date, loan file to be returned to Underwriting for an updated LQI Report | Underwriter | Needed | High Confidence |
| 12 | [BOR-1] HOI invoice / homeowner's insurance - borrower to provide current insurance agent name, phone, and email | Borrower | Needed | Best Guess |
| 13 | [BOR-2] Real Estate Certification / FHA Amendatory Clause to be signed by buyers, sellers, and agents | Borrower | Needed | Best Guess |
| 14 | [BOR-3] Final Seller Closing Disclosure from sale of current home | Borrower | Needed | Best Guess |

Skip these (do NOT output rows for them):
  - Borrower summary, loan terms, rates, property info on page 1
  - Underwriter name/signature blocks
  - Empty section headers (e.g. an empty PTA section)
  - Date stamps, page numbers, footers
"""
    try:
        # Gemini is the only inline PDF understanding path this client supports.
        if api_key_override:
            api_key = api_key_override
            model = DEFAULT_MODELS["gemini"]
        elif provider == "gemini":
            api_key = cfg.get("api_key", "")
            model = cfg.get("model") or DEFAULT_MODELS["gemini"]
        else:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            model = DEFAULT_MODELS["gemini"]
        if not api_key:
            return _local_text_path()

        payload = json.dumps({
            "system_instruction": {"parts": [{"text": _gemini_system(system)}]},
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("utf-8")}},
                    {"text": _gemini_prompt(prompt)},
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192,
            },
        }).encode("utf-8")
        url, _gem_headers = _gemini_target(model, api_key)
        req = urllib.request.Request(
            url, data=payload,
            headers=_gem_headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=75) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = redact_gemini_output(
            data["candidates"][0]["content"]["parts"][0]["text"].strip(),
            source_text=text,
        )
        if has_unresolved_placeholders(txt):
            txt = _neutralize_placeholders(txt)
        valid = _parse_approval_condition_rows(txt)
        conditions = "\n".join(valid)
        if not valid:
            # Vision returned nothing usable - fall back to the privacy text path.
            return _local_text_path()
        _note = f"gemini - {model}" if provider == "gemini" else f"gemini_fallback - {model}"
        return conditions, _log("CLOUD", "approval_pdf_extract", f"{len(valid)} conditions - {_note}"), txt[:12000]
    except Exception:
        return _local_text_path()


def _parse_approval_condition_rows(text: str) -> list[str]:
    """Return pipe rows from Gemini output, tolerating common formatting drift."""
    rows = []
    pending = []

    def _append_pipe_row(line: str) -> bool:
        cleaned = line.strip().strip("`")
        if not cleaned or cleaned.lower().startswith(("global#", "where:", "example output")):
            return False
        if "|" not in cleaned:
            return False
        parts = [p.strip() for p in cleaned.strip("|").split("|")]
        if len(parts) < 4:
            return False
        if not re.search(r"\d", parts[0]):
            return False
        while len(parts) < 5:
            parts.append("High Confidence" if len(parts) == 4 else "")
        rows.append("| " + " | ".join(parts[:5]) + " |")
        return True

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("```"):
            continue
        if _append_pipe_row(line):
            continue
        plain = re.sub(r"^\s*(?:[-*]|\d{1,3}[\.)])\s*", "", line).strip()
        if plain:
            pending.append(plain)

    if rows:
        return rows

    for idx, desc in enumerate(pending, start=1):
        if len(desc) < 12:
            continue
        if re.match(r"(?i)^(?:here are|the following|conditions?:|section|prior to)\b", desc):
            continue
        rows.append(f"| {idx} | {desc} | Borrower | Needed | Best Guess |")
    return rows


def translate_conditions_to_plain(descriptions: list[str], api_key_override: str = "") -> tuple[list[str], str]:
    """Translate a list of mortgage condition descriptions into plain English.
    Returns (translated_list_same_length, log_line). If translation fails, falls
    back to the original list so the UI never blanks out."""
    if not descriptions:
        return [], _log("SCRIPT", "translate_plain", "Empty input")

    if api_key_override:
        api_key = api_key_override
        model = DEFAULT_MODELS["gemini"]
    else:
        cfg = get_config()
        if cfg.get("provider") == "gemini" and cfg.get("api_key"):
            api_key = cfg["api_key"]
            model = cfg.get("model") or DEFAULT_MODELS["gemini"]
        else:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            model = DEFAULT_MODELS["gemini"]
    if not api_key:
        return list(descriptions), _log("SCRIPT", "translate_plain", "No Gemini key")

    system = (
        "You translate mortgage underwriting conditions into short, polite, "
        "plain-English requests for homebuyers. Keep the request specific and "
        "actionable while redacting all personal and identifying information."
    )
    # Number each condition and request a JSON array back, preserving order.
    numbered_input = "\n".join(f"{i+1}. {d}" for i, d in enumerate(descriptions))
    safe_fallback = [
        redact_gemini_output(item, source_text=numbered_input)
        for item in descriptions
    ]
    prompt = (
        "Rewrite each mortgage approval condition as a short, polite request a "
        "homebuyer can act on. RULES:\n\n"
        "1. Preserve non-identifying requirements, but redact names, SSNs, addresses, "
        "phone numbers, emails, account/routing numbers, birth dates, and income.\n"
        "2. Be concise. Target 1-2 short sentences per condition. Aim for fewer "
        "words than the original.\n"
        "3. Start each one with a friendly opener (vary them — don't repeat the "
        "same phrase). Examples: 'Please send', 'We need', 'Could you provide', "
        "'Quick request:', 'One more thing —', 'Almost there —', 'To wrap up,'.\n"
        "4. Drop section tags like [PTD-1], [PTF-1], [AC-1].\n"
        "5. Replace acronyms with everyday phrases: VOM = mortgage payment "
        "history, LQI = loan quality re-check, LOE = letter of explanation, "
        "SLR = second-level review, VOE/WVOE = employer verification, 4506C = "
        "IRS income verification form, HOI = homeowner's insurance, CTC = "
        "clear-to-close, CD = closing disclosure, AKA = also-known-as / former "
        "name, P&L = profit and loss statement.\n"
        "6. Drop boilerplate phrases like 'Provide updated', 'must be received', "
        "'in compliance', 'for qualifying purposes' — those are filler.\n"
        "7. Output ONLY a JSON array of strings, same order, same length as input.\n\n"
        f"Input:\n{numbered_input}\n\n"
        'Output format: ["short polite request 1", "short polite request 2", ...]'
    )

    try:
        payload = json.dumps({
            "system_instruction": {"parts": [{"text": _gemini_system(system)}]},
            "contents": [{"parts": [{"text": _gemini_prompt(prompt)}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
        }).encode("utf-8")
        url, _gem_headers = _gemini_target(model, api_key)
        req = urllib.request.Request(url, data=payload,
                                     headers=_gem_headers,
                                     method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = redact_gemini_output(
            data["candidates"][0]["content"]["parts"][0]["text"].strip(),
            source_text=numbered_input,
        )
        # Strip ```json fences if present
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt).strip()
        out = json.loads(txt)
        if not isinstance(out, list) or len(out) != len(descriptions):
            # Length mismatch — fall back to originals to keep UI consistent
            return safe_fallback, _log("CLOUD", "translate_plain",
                                            f"Length mismatch: got {len(out) if isinstance(out, list) else '?'} expected {len(descriptions)}")
        cleaned = [str(s).strip() or safe_fallback[i] for i, s in enumerate(out)]
        return cleaned, _log("CLOUD", "translate_plain", f"{len(cleaned)} translated - gemini - {model}")
    except Exception as e:
        return safe_fallback, _log("SCRIPT", "translate_plain", _friendly_cloud_error(e))


def translate_conditions_to_summarized(descriptions: list[str], api_key_override: str = "") -> tuple[list[str], str]:
    """Summarize each condition into '**Short Subject** - one short instruction'.
    Returns (summarized_list_same_length, log_line). Falls back to originals on error."""
    if not descriptions:
        return [], _log("SCRIPT", "translate_summary", "Empty input")

    if api_key_override:
        api_key = api_key_override
        model = DEFAULT_MODELS["gemini"]
    else:
        cfg = get_config()
        if cfg.get("provider") == "gemini" and cfg.get("api_key"):
            api_key = cfg["api_key"]
            model = cfg.get("model") or DEFAULT_MODELS["gemini"]
        else:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
            model = DEFAULT_MODELS["gemini"]
    if not api_key:
        return list(descriptions), _log("SCRIPT", "translate_summary", "No Gemini key")

    system = (
        "You compress mortgage underwriting conditions into the exact bullet "
        "format a senior loan processor uses when emailing clients. Each item "
        "is one line: a bold short subject (1-3 words), then ' - ', then ONE "
        "short specific instruction. Redact all personal and identifying "
        "information. Drop industry jargon and acronyms."
    )
    numbered_input = "\n".join(f"{i+1}. {d}" for i, d in enumerate(descriptions))
    safe_fallback = [
        redact_gemini_output(item, source_text=numbered_input)
        for item in descriptions
    ]
    prompt = (
        "Compress each condition into the EXACT format below. This is how a "
        "senior loan processor writes to clients.\n\n"
        "OUTPUT FORMAT (one line per item):\n"
        "  **Short Subject** - one short specific instruction\n\n"
        "Subject rules:\n"
        "  * 1-3 words, Title Case, surrounded by ** ** for bold.\n"
        "  * Use the actual topic, not the acronym. Examples:\n"
        "      Appraisal, Earnest Money, Bank Statement, SSN/W2, Employment,\n"
        "      Homeowners Insurance, Lead Based Paint, Anti Steering, Title,\n"
        "      Payoff, Tax Bill, Statement, Invoice, Funds to Close,\n"
        "      Letter of Explanation, Motivation Letter, Closing Disclosure,\n"
        "      Verification of Mortgage, Gift Funds, ID, Driver's License.\n"
        "  * Never use a street address or personal name as the subject.\n\n"
        "Body rules:\n"
        "  * ONE short sentence. No fluff. No 'In order to' / 'Please be advised'.\n"
        "  * Keep non-identifying requirements and document names; redact PII.\n"
        "  * Drop section tags like [PTD-1], [PTF-1], [AC-1].\n"
        "  * Replace acronyms: VOM = mortgage payment history, LQI = loan\n"
        "    quality re-check, LOE = letter of explanation, SLR = second-level\n"
        "    review, VOE/WVOE = employer verification, 4506C = IRS income\n"
        "    verification form, HOI = homeowner's insurance, CTC = clear-to-close,\n"
        "    CD = closing disclosure, AKA = former / also-known-as name.\n"
        "  * Use ALL CAPS sparingly for emphasis: 'ALL PAGES EVEN BLANK'.\n\n"
        "Real examples to model on:\n"
        "  **Appraisal** - Watch for a link from a third party asking for credit "
        "card payment for the appraisal.\n"
        "  **Earnest Money** - Copy of the earnest money check plus full month "
        "bank statement (ALL PAGES EVEN BLANK) showing the clearance.\n"
        "  **Bank Statement** - Re-send the Westex statement - page 2 was cut off.\n"
        "  **SSN/W2** - Copy of your Social Security Card OR most recent W2.\n"
        "  **Employment** - 2021 & 2022 year-end pay stubs plus an HR or "
        "direct-manager contact for the employment verification.\n"
        "  **Lead Based Paint** - eSign the updated disclosure - box D needs "
        "to be checked.\n\n"
        "Output ONLY a JSON array of strings, same order, same length as input.\n\n"
        f"Input:\n{numbered_input}\n\n"
        'Format: ["**Subject** - body", "**Subject** - body", ...]'
    )

    try:
        payload = json.dumps({
            "system_instruction": {"parts": [{"text": _gemini_system(system)}]},
            "contents": [{"parts": [{"text": _gemini_prompt(prompt)}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
        }).encode("utf-8")
        url, _gem_headers = _gemini_target(model, api_key)
        req = urllib.request.Request(url, data=payload,
                                     headers=_gem_headers,
                                     method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = redact_gemini_output(
            data["candidates"][0]["content"]["parts"][0]["text"].strip(),
            source_text=numbered_input,
        )
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt).strip()
        out = json.loads(txt)
        if not isinstance(out, list) or len(out) != len(descriptions):
            return safe_fallback, _log("CLOUD", "translate_summary",
                                            f"Length mismatch: got {len(out) if isinstance(out, list) else '?'} expected {len(descriptions)}")
        cleaned = [str(s).strip() or safe_fallback[i] for i, s in enumerate(out)]
        return cleaned, _log("CLOUD", "translate_summary", f"{len(cleaned)} summarized - gemini - {model}")
    except Exception as e:
        return safe_fallback, _log("SCRIPT", "translate_summary", _friendly_cloud_error(e))
