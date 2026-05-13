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


def _filter_invoice_conditions(conditions: list[dict]) -> list[dict]:
    """Remove invoice items from client-facing condition lists."""
    filtered = [
        cond for cond in conditions
        if not re.search(r"\binvoice\b", str(cond.get("desc", "")).lower())
    ]
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
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    # If the system prompt asks for JSON, force JSON mode so Gemini doesn't wrap output
    _gen_cfg = {"maxOutputTokens": 8192, "temperature": 0.15}
    if system and "json" in system.lower():
        _gen_cfg["responseMimeType"] = "application/json"
    payload = json.dumps({
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": _gen_cfg,
    }).encode("utf-8")
    url = GEMINI_ENDPOINT.format(model=model, key=api_key)
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()


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
                       script_conditions: str) -> tuple[str, str]:
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return script_conditions, _log("SCRIPT", "condition_extraction", "Cloud disabled")

    system = (
        "You are an expert mortgage condition parser. Extract only real lender "
        "conditions from approval documents. If the lender/format is familiar from "
        "the document patterns, label the row High Confidence. If you are making an "
        "educated inference from a new or unclear format, label it Best Guess. Never "
        "invent conditions that are not present in the document."
    )
    prompt = f"""Review this {doc_type} and the conditions a script already extracted.

DOCUMENT (first 5000 chars):
{text[:5000]}

SCRIPT-EXTRACTED CONDITIONS:
{script_conditions[:3000]}

Your job:
1. Keep all valid conditions from the script list
2. Add any conditions the script missed
3. Fix any descriptions that are vague or truncated
4. Assign the correct responsible party for each
5. For approval letters, keep each chronological numbered condition as ONE row.
   If item 1 has wrapped/detail lines under it, combine those lines into item 1.
   Do not split wrapped details into extra conditions or extra checkboxes.
6. Preserve the whole condition text. Do not shorten it.
7. Mark confidence as High Confidence for clear lender condition rows, or Best Guess when the format is unclear.

Return ONLY the conditions - no intro text, no headers, no explanations.
Use this exact pipe-delimited format, one condition per line:
| 1 | Full description of the condition | Borrower | Needed | High Confidence |
| 2 | Full description of the condition | Title | Needed | Best Guess |

Responsible party options: Borrower, Title, Underwriter, Insurance, Closer, Appraiser
Status: always Needed
Confidence options: High Confidence, Best Guess"""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        valid = [
            ln.strip() for ln in response.split("\n")
            if ln.strip().startswith("|") and ln.count("|") >= 4
        ]
        script_count = sum(
            1 for ln in script_conditions.split("\n")
            if ln.strip().startswith("|") and ln.count("|") >= 4
        )
        if len(valid) >= max(1, script_count // 2):
            renumbered = []
            for i, ln in enumerate(valid, 1):
                parts = [p.strip() for p in ln.split("|")]
                if len(parts) >= 5:
                    parts[1] = str(i)
                    renumbered.append("| " + " | ".join(parts[1:]) + " |")
                else:
                    renumbered.append(ln)
            result = "\n".join(renumbered)
            log = _log("CLOUD", "condition_extraction",
                       f"{len(valid)} conditions  {provider}  {cfg.get('model')}")
            return result, log
        else:
            existing = {ln.strip() for ln in script_conditions.split("\n") if "|" in ln}
            for ln in valid:
                existing.add(ln.strip())
            merged = "\n".join(sorted(existing))
            return merged, _log("CLOUD+SCRIPT", "condition_extraction", "merged — Cloud returned few")
    except Exception as e:
        return script_conditions, _log("SCRIPT", "condition_extraction",
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
            if i == 0 and system:
                text = f"{system}\n\n{text}"
            _gem_contents.append({"role": role, "parts": [{"text": text}]})
        payload = json.dumps({
            "contents": _gem_contents,
            "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.3},
        }).encode("utf-8")
        url = GEMINI_ENDPOINT.format(model=model, key=api_key)
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()

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
    Use cloud AI to extract purchase contract fields from any state form.
    Returns (extracted_dict, log_line).
    """
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return {}, _log("SCRIPT", "pc_extract", "Cloud disabled")

    # Send the full document — modern Claude handles 100k+ tokens easily.
    # Truncate only if absurdly large (> 80k chars ≈ 20k tokens).
    full_text = raw_text if len(raw_text) <= 80000 else raw_text[:80000]

    system = (
        "You analyze residential purchase contracts and return a structured JSON "
        "object. Output only valid JSON — no markdown fences, no commentary."
    )
    # User's chat prompt that worked perfectly, wrapped to return JSON instead of prose.
    prompt = f"""Please analyze this purchase contract and extract the following information:

- Purchase Price
- Property Address
- Closing Date
- Listing Agent Name (separate the name, brokerage, phone, email)
- Selling Agent Name (separate the name, brokerage, phone, email)
- Title Company
- Buyer Name(s)
- Seller Name(s)
- Earnest Money Deposit
- Down Payment Amount
- Loan Amount
- Any special conditions or contingencies

Return the results as valid JSON in EXACTLY this shape (use empty string "" for any
field genuinely not present in the document):

{_PC_JSON_TEMPLATE}

For amounts use digits only ("474500"). For dates keep the format you find ("MM/DD/YYYY"
or "Month DD, YYYY"). Never put a phone number or email in a name field.

CONTRACT TEXT:
{full_text}"""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        import json as _json
        data = _parse_ai_json(response)

        # Post-process: filter out obvious boilerplate in extracted values
        data = _clean_extracted_contract_data(data)

        log = _log("CLOUD", "pc_extract", f"{provider}  {cfg.get('model')}")
        return data, log
    except Exception as e:
        return {}, _log("SCRIPT", "pc_extract", f"Cloud error: {str(e)[:80]}")


def extract_purchase_contract_ai_from_pdf(pdf_bytes: bytes) -> tuple[dict, str, str]:
    """
    OCR + extraction path for scanned/image-only Purchase Contracts.
    Uses Gemini inline PDF understanding to return structured JSON directly.
    Returns: (extracted_dict, log_line, ocr_text_hint)
    """
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
                "parts": [{"text": system}]
            },
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("utf-8")}},
                    {"text": prompt},
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
            },
        }).encode("utf-8")
        url = GEMINI_ENDPOINT.format(model=model, key=api_key)
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        parsed = _clean_extracted_contract_data(_parse_ai_json(txt))
        _note = f"gemini  {model}" if provider == "gemini" else f"gemini_fallback  {model}"
        return parsed, _log("CLOUD", "pc_pdf_extract", _note), ""
    except Exception as e:
        return {}, _log("SCRIPT", "pc_pdf_extract", f"Cloud error: {str(e)[:120]}"), ""


def extract_approval_conditions_ai_from_pdf(pdf_bytes: bytes, api_key_override: str = "") -> tuple[str, str, str]:
    """
    OCR + extraction path for Approval Letters via Gemini inline PDF understanding.
    Returns: (pipe_delimited_conditions, log_line, text_hint)

    api_key_override: if provided, uses this key directly (bypasses cloud_config).
    Caller passes the user's onboarding Gemini API key.
    """
    if api_key_override:
        provider = "gemini"
    else:
        cfg = get_config()
        if not cfg.get("enabled") or not cfg.get("api_key"):
            return "", _log("SCRIPT", "approval_pdf_extract", "No Gemini key available"), ""
        provider = cfg.get("provider", DEFAULT_PROVIDER)
    system = (
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

Extract EVERY numbered condition from EVERY section. Do not skip any condition, even
if a section header is on a separate page. Do not merge separate numbered items into
one row. Do not summarize — copy the wording as written, including any "Updated" notes,
asterisks, and stamped comments.

OUTPUT FORMAT — one condition per line, exactly five pipe-delimited fields:
| GLOBAL# | [SECTION-LOCAL#] Full condition text as written | Responsible | Needed | Confidence |

Where:
  GLOBAL# = sequential number across the whole letter (1, 2, 3, ...)
  SECTION-LOCAL# = bracketed prefix on the description: section tag + the number in the
                   PDF for that section. e.g. [PTD-1], [PTD-2], [AC-1], [PTF-1]
  Responsible = which party gets the request: Borrower, Title, Underwriter, Insurance,
                Closer, Appraiser, Employer, Realtor, Seller
  Status = always "Needed"
  Confidence = "High Confidence" if you copied wording verbatim, "Best Guess" if OCR was unclear

Example output (study this carefully — the prefix in brackets is part of the description):
| 1 | [PTD-1] Appraisal - 1004D with final photos - 1004-D TO SUPPORT ALL REPAIRS LISTED ON PAGE 1 OF 6 | Appraiser | Needed | High Confidence |
| 2 | [PTD-2] Document Expirations - Credit expiration 4/1; Income expiration 3/25; Asset expiration 3/9 | Borrower | Needed | High Confidence |
| 9 | [AC-1] Internal - Lock Desk to confirm pricing prior to CTC | Underwriter | Needed | High Confidence |
| 11 | [PTF-1] Funding - LQI Report - If loan has not funded by ____ date, loan file to be returned to Underwriting for an updated LQI Report | Underwriter | Needed | High Confidence |

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
            return "", _log("SCRIPT", "approval_pdf_extract", "Gemini key missing for PDF OCR fallback"), ""

        payload = json.dumps({
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{
                "parts": [
                    {"inline_data": {"mime_type": "application/pdf", "data": base64.b64encode(pdf_bytes).decode("utf-8")}},
                    {"text": prompt},
                ]
            }],
            "generationConfig": {
                "temperature": 0.0,
                "maxOutputTokens": 8192,
            },
        }).encode("utf-8")
        url = GEMINI_ENDPOINT.format(model=model, key=api_key)
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=75) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        valid = [
            ln.strip() for ln in txt.splitlines()
            if ln.strip().startswith("|") and ln.count("|") >= 4
        ]
        conditions = "\n".join(valid)
        _note = f"gemini - {model}" if provider == "gemini" else f"gemini_fallback - {model}"
        return conditions, _log("CLOUD", "approval_pdf_extract", f"{len(valid)} conditions - {_note}"), txt[:12000]
    except Exception as e:
        return "", _log("SCRIPT", "approval_pdf_extract", _friendly_cloud_error(e)), ""


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
        "plain-English requests for homebuyers. You preserve every fact, dollar "
        "amount, date, address, and document name. You drop industry jargon and "
        "acronyms but keep the request specific and actionable."
    )
    # Number each condition and request a JSON array back, preserving order.
    numbered_input = "\n".join(f"{i+1}. {d}" for i, d in enumerate(descriptions))
    prompt = (
        "Rewrite each mortgage approval condition as a short, polite request a "
        "homebuyer can act on. RULES:\n\n"
        "1. Keep every fact: dollar amounts, dates, addresses, document names, "
        "counts, percentages. Never omit specifics.\n"
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
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 8192},
        }).encode("utf-8")
        url = GEMINI_ENDPOINT.format(model=model, key=api_key)
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        txt = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # Strip ```json fences if present
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt).strip()
        out = json.loads(txt)
        if not isinstance(out, list) or len(out) != len(descriptions):
            # Length mismatch — fall back to originals to keep UI consistent
            return list(descriptions), _log("CLOUD", "translate_plain",
                                            f"Length mismatch: got {len(out) if isinstance(out, list) else '?'} expected {len(descriptions)}")
        cleaned = [str(s).strip() or descriptions[i] for i, s in enumerate(out)]
        return cleaned, _log("CLOUD", "translate_plain", f"{len(cleaned)} translated - gemini - {model}")
    except Exception as e:
        return list(descriptions), _log("SCRIPT", "translate_plain", _friendly_cloud_error(e))
