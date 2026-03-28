"""
Cloud AI Integration — Pipeline Manager
Optional cloud AI backend. Supports Anthropic Claude and OpenAI.
Requires an internet connection and a valid API key.

Providers:
  claude  → Anthropic Claude API  (claude-sonnet-4-6, claude-haiku-4-5, etc.)
  openai  → OpenAI API            (gpt-4o, gpt-4o-mini, etc.)

Falls back silently to script-only if unavailable or key is missing.
Logs every call mode to cloud_log.txt alongside the Ollama log.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime

_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
_CFG_FILE = os.path.join(_APP_DIR, "cloud_config.json")
_LOG_FILE = os.path.join(_APP_DIR, "cloud_log.txt")

DEFAULT_PROVIDER = "claude"
DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
}

CLAUDE_ENDPOINT = "https://api.anthropic.com/v1/messages"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

def get_config() -> dict:
    if not os.path.exists(_CFG_FILE):
        return {
            "enabled":  False,
            "provider": DEFAULT_PROVIDER,
            "api_key":  "",
            "model":    DEFAULT_MODELS[DEFAULT_PROVIDER],
        }
    try:
        with open(_CFG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": False, "provider": DEFAULT_PROVIDER, "api_key": "", "model": ""}


def save_config(enabled: bool, provider: str, api_key: str, model: str) -> dict:
    cfg = {
        "enabled":  enabled,
        "provider": provider,
        "api_key":  api_key.strip(),
        "model":    model.strip(),
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
            return True, f"Connected · {provider} · {model}"
        return False, "Empty response"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "Invalid API key (401 Unauthorized)"
        if e.code == 429:
            return False, "Rate limited (429) — try again shortly"
        return False, f"HTTP {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"Cannot reach {provider} API: {e.reason}"
    except Exception as e:
        return False, str(e)[:80]


# ─────────────────────────────────────────────────────────────────────────────
# Core generate
# ─────────────────────────────────────────────────────────────────────────────

def _generate(prompt: str, system: str, provider: str, api_key: str,
              model: str, timeout: int = 60) -> str:
    if provider == "claude":
        return _generate_claude(prompt, system, model, api_key, timeout)
    elif provider == "openai":
        return _generate_openai(prompt, system, model, api_key, timeout)
    else:
        raise ValueError(f"Unknown provider: {provider}")


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

def _log(mode: str, feature: str, note: str = "") -> str:
    ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {mode.upper():14s} | {feature}"
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

    system = "You are an expert mortgage processor who reviews loan condition checklists."
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

Return ONLY the conditions — no intro text, no headers, no explanations.
Use this exact pipe-delimited format, one condition per line:
| 1 | Full description of the condition | Borrower | Needed |
| 2 | Full description of the condition | Title | Needed |

Responsible party options: Borrower, Title, Underwriter, Insurance, Closer, Appraiser
Status: always Needed"""

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
                       f"{len(valid)} conditions · {provider} · {cfg.get('model')}")
            return result, log
        else:
            existing = {ln.strip() for ln in script_conditions.split("\n") if "|" in ln}
            for ln in valid:
                existing.add(ln.strip())
            merged = "\n".join(sorted(existing))
            return merged, _log("CLOUD+SCRIPT", "condition_extraction", "merged — Cloud returned few")
    except Exception as e:
        return script_conditions, _log("SCRIPT", "condition_extraction",
                                       f"Cloud error: {str(e)[:60]}")


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
            f"\n── {chunk.get('source','?')} · page {chunk.get('page','?')} ──\n"
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
        log = _log("CLOUD", "guideline_search", f"{provider} · {cfg.get('model')}")
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

    cond_list = "\n".join(
        f"- {c.get('desc', c.get('num', 'Item'))}" for c in conditions
    )
    lang_instr = (
        "Escribe el correo en español formal y profesional."
        if language == "Spanish"
        else "Write in professional American English."
    )

    system = "You are a professional mortgage processor writing client-facing emails."
    prompt = f"""Write a document request email to a {recipient_type}.

{lang_instr}

Documents / items needed:
{cond_list}

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
                   f"{recipient_type} · {language} · {provider} · {cfg.get('model')}")
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
        log = _log("CLOUD", "doc_summary", f"{provider} · {cfg.get('model')}")
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
    For purchase contracts, important data is scattered across the document:
      - Buyer/seller/price near the top (pages 1-3)
      - Title company, closing date in the middle (pages 4-5)
      - Agent names, MLS info, signatures at the end (last 2 pages)
    Send the first third + last third so the AI sees everything.
    """
    if len(raw_text) <= max_chars:
        return raw_text
    half = max_chars // 2
    top = raw_text[:half]
    bottom = raw_text[-half:]
    return top + "\n\n[...middle of document omitted...]\n\n" + bottom


def extract_purchase_contract_ai(raw_text: str) -> tuple[dict, str]:
    """
    Use cloud AI to extract purchase contract fields from any state form.
    Returns (extracted_dict, log_line).
    """
    cfg = get_config()
    if not cfg.get("enabled") or not cfg.get("api_key"):
        return {}, _log("SCRIPT", "pc_extract", "Cloud disabled")

    sampled = _smart_sample(raw_text)

    system = (
        "You are a senior mortgage loan processor. You read residential purchase "
        "contracts every day — Ohio REALTORS, CA CAR, TX TREC, MN STAR, WI WB, "
        "FL FAR, and custom forms. You know that in digitally-signed PDFs (dotloop, "
        "DocuSign, Skyslope), the filled-in values often appear as a block at the "
        "bottom of each page, separate from the form template text. You always look "
        "at the ENTIRE document including the signature pages and MLS section to find "
        "agent names and brokerage info. Return only valid JSON — no markdown fences, "
        "no explanation, no extra text."
    )
    prompt = f"""Read this purchase contract carefully and extract every field you can find.
Return ONLY a JSON object matching this exact structure. Leave fields as empty string "" if truly not present.

{_PC_JSON_TEMPLATE}

FIELD DEFINITIONS:
- buyer.name: The person(s) purchasing the property. Look for "BUYER", "Purchaser", or the name on signature lines.
- seller.name: The person(s) selling the property. Look for "SELLER", "LANDLORD", or the counter-signature. Often appears right after the buyer name or on the acceptance/signature page.
- property.address: Full street address including city, state, zip if available.
- transaction.purchase_price: The total purchase price. Digits and commas only (e.g. "180,000"). Look for "PRICE:", "Purchase Price:", "sum of $", or a standalone large dollar amount.
- transaction.closing_date: When the deal closes. Use the format as written (e.g. "03/25/2022" or "March 25, 2022"). Look for "on or before", "title shall transfer", "Closing Date:", or date fields in the closing section.
- transaction.earnest_money: Earnest money deposit amount. Digits and commas only.
- transaction.down_payment: Down payment amount or description (e.g. "5%" or "25,000").
- transaction.seller_concessions: Any seller credits, concessions, or closing cost contributions.
- listing_agent: The SELLER's agent. Check the MLS section at the end of the document, signature blocks, or "Listing Agent:" labels.
- selling_agent: The BUYER's agent (also called "Selling Agent" or "Cooperating Agent"). Check MLS section.
- title.company: Title company, escrow company, or settlement agent handling the closing.
- contingencies: Inspection period, appraisal contingency, financing contingency — include timeframes if stated.
- addendums: List of addendum/rider names attached to the contract.

IMPORTANT:
- IGNORE blank underscore lines (________), template placeholder text ("as specified below", "will be represented by"), and page numbers.
- In dotloop/DocuSign PDFs, look for filled values at the BOTTOM of pages after the form template text.
- The MLS section near the end often has: (Listing Agent Name) then actual name, (Listing Brokerage Name) then actual brokerage, etc.
- Buyer and seller names often appear together on the Agency Disclosure page (address → buyer → seller on consecutive lines).
- Dotloop signatures show as "Name\\ndotloop verified\\ndate" — these ARE the real party names.

CONTRACT TEXT:
{sampled}"""

    try:
        provider = cfg.get("provider", DEFAULT_PROVIDER)
        response = _generate(prompt, system, provider, cfg["api_key"], cfg["model"])
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        import json as _json
        data = _json.loads(response.strip())
        log = _log("CLOUD", "pc_extract", f"{provider} · {cfg.get('model')}")
        return data, log
    except Exception as e:
        return {}, _log("SCRIPT", "pc_extract", f"Cloud error: {str(e)[:80]}")
