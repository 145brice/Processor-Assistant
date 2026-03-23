"""
Ollama Integration — Processor Traien
Optional local LLM enhancement. Connects to a locally running Ollama instance.
All offline — no internet, no API keys, no cloud.

Install Ollama: https://ollama.com  (download runs locally on your machine)
Pull a model:   ollama pull llama3.2   (in your terminal)
Then run:       ollama serve           (starts the local API server)

Default endpoint: http://localhost:11434

Falls back silently to script-only processing if Ollama is unavailable.
Every call logs which processing mode was used (script / ollama / ollama+script).
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime

_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
_CFG_FILE = os.path.join(_APP_DIR, "ollama_config.json")
_LOG_FILE = os.path.join(_APP_DIR, "ollama_log.txt")

DEFAULT_ENDPOINT = "http://localhost:11434"
DEFAULT_MODEL    = "llama3.2"


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

def get_config() -> dict:
    if not os.path.exists(_CFG_FILE):
        return {"enabled": False, "endpoint": DEFAULT_ENDPOINT, "model": DEFAULT_MODEL}
    try:
        with open(_CFG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": False, "endpoint": DEFAULT_ENDPOINT, "model": DEFAULT_MODEL}


def save_config(enabled: bool, endpoint: str, model: str) -> dict:
    cfg = {"enabled": enabled, "endpoint": endpoint.rstrip("/"), "model": model}
    with open(_CFG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg


def is_enabled() -> bool:
    return bool(get_config().get("enabled"))


# ─────────────────────────────────────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────────────────────────────────────

def ping(endpoint: str | None = None) -> tuple[bool, str]:
    """Check if Ollama is running. Returns (success, message)."""
    if endpoint is None:
        endpoint = get_config().get("endpoint", DEFAULT_ENDPOINT)
    try:
        req = urllib.request.Request(f"{endpoint}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                return True, "Connected"
    except urllib.error.URLError as e:
        return False, f"Cannot reach Ollama: {e.reason}"
    except Exception as e:
        return False, str(e)[:80]
    return False, "No response"


def list_models(endpoint: str | None = None) -> list[str]:
    """Return list of model names available in this Ollama instance."""
    if endpoint is None:
        endpoint = get_config().get("endpoint", DEFAULT_ENDPOINT)
    try:
        req = urllib.request.Request(f"{endpoint}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Core generate call
# ─────────────────────────────────────────────────────────────────────────────

def _generate(prompt: str, model: str | None = None, endpoint: str | None = None,
              timeout: int = 90) -> str:
    """Send a prompt to Ollama and return the response text."""
    cfg = get_config()
    if endpoint is None:
        endpoint = cfg.get("endpoint", DEFAULT_ENDPOINT)
    if model is None:
        model = cfg.get("model", DEFAULT_MODEL)

    payload = json.dumps({
        "model":  model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.15,   # low = consistent, deterministic
            "num_predict": 2048,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{endpoint}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# Processing mode log
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

def enhance_conditions(text: str, doc_type: str, script_conditions: str) -> tuple[str, str]:
    """
    Use Ollama to review and improve the script-extracted conditions.
    Returns (conditions_text, log_line).
    Falls back to script_conditions on any failure.
    """
    cfg = get_config()
    if not cfg.get("enabled"):
        return script_conditions, _log("SCRIPT", "condition_extraction", "Ollama disabled")

    ok, msg = ping(cfg["endpoint"])
    if not ok:
        return script_conditions, _log("SCRIPT", "condition_extraction", f"offline — {msg}")

    prompt = f"""You are an expert mortgage processor. Review this {doc_type} and the conditions a script already extracted.

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
        response = _generate(prompt, model=cfg.get("model"))
        valid = [
            ln.strip() for ln in response.split("\n")
            if ln.strip().startswith("|") and ln.count("|") >= 4
        ]
        script_count = sum(
            1 for ln in script_conditions.split("\n")
            if ln.strip().startswith("|") and ln.count("|") >= 4
        )
        if len(valid) >= max(1, script_count // 2):
            # Re-number sequentially
            renumbered = []
            for i, ln in enumerate(valid, 1):
                parts = [p.strip() for p in ln.split("|")]
                if len(parts) >= 5:
                    parts[1] = str(i)
                    renumbered.append("| " + " | ".join(parts[1:]) + " |")
                else:
                    renumbered.append(ln)
            result = "\n".join(renumbered)
            log = _log("OLLAMA", "condition_extraction",
                       f"{len(valid)} conditions · model={cfg.get('model')}")
            return result, log
        else:
            # Ollama returned very few — merge both sets
            existing = {ln.strip() for ln in script_conditions.split("\n") if "|" in ln}
            for ln in valid:
                existing.add(ln.strip())
            merged = "\n".join(sorted(existing))
            return merged, _log("OLLAMA+SCRIPT", "condition_extraction", "merged — Ollama returned few")
    except Exception as e:
        return script_conditions, _log("SCRIPT", "condition_extraction",
                                       f"Ollama error: {str(e)[:60]}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Guideline interpretation
# ─────────────────────────────────────────────────────────────────────────────

def interpret_guidelines(condition_text: str, chunks: list[dict]) -> tuple[str, str]:
    """
    Use Ollama to summarize how the retrieved guideline chunks apply
    to a specific condition.
    chunks: list of {source, page, section, text}
    Returns (summary_text, log_line).
    """
    cfg = get_config()
    if not cfg.get("enabled"):
        return "", _log("SCRIPT", "guideline_search", "Ollama disabled")

    ok, msg = ping(cfg["endpoint"])
    if not ok:
        return "", _log("SCRIPT", "guideline_search", f"offline — {msg}")

    chunk_text = ""
    for chunk in chunks[:6]:
        chunk_text += (
            f"\n── {chunk.get('source','?')} · page {chunk.get('page','?')} ──\n"
            f"{chunk.get('text','')[:600]}\n"
        )

    prompt = f"""You are a Fannie Mae and Freddie Mac guideline expert helping a mortgage processor clear a loan condition.

CONDITION FROM LENDER:
{condition_text}

RELEVANT GUIDELINE SECTIONS:
{chunk_text}

In 3–5 sentences:
1. Explain which guideline applies and what it requires
2. Tell the processor exactly what documentation satisfies this condition
3. Note any exceptions or special cases that are relevant

Be specific and actionable. Write for a working mortgage processor, not a lawyer."""

    try:
        response = _generate(prompt, model=cfg.get("model"))
        log = _log("OLLAMA", "guideline_search", cfg.get("model", ""))
        return response, log
    except Exception as e:
        return "", _log("SCRIPT", "guideline_search", f"Ollama error: {str(e)[:60]}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Enhanced email drafting
# ─────────────────────────────────────────────────────────────────────────────

def draft_email_enhanced(conditions: list[dict], recipient_type: str,
                         language: str) -> tuple[str, str]:
    """
    Use Ollama to draft a professional, context-aware document request email.
    Returns (email_body_text, log_line).
    Falls back to empty string so caller uses script template.
    """
    cfg = get_config()
    if not cfg.get("enabled"):
        return "", _log("SCRIPT", "email_draft", "Ollama disabled")

    ok, msg = ping(cfg["endpoint"])
    if not ok:
        return "", _log("SCRIPT", "email_draft", f"offline — {msg}")

    cond_list = "\n".join(
        f"- {c.get('desc', c.get('num', 'Item'))}" for c in conditions
    )
    lang_instr = (
        "Escribe el correo en español formal y profesional."
        if language == "Spanish"
        else "Write in professional American English."
    )

    prompt = f"""You are a professional mortgage processor writing a document request email to a {recipient_type}.

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
        response = _generate(prompt, model=cfg.get("model"))
        log = _log("OLLAMA", "email_draft",
                   f"{recipient_type} · {language} · {cfg.get('model','')}")
        return response, log
    except Exception as e:
        return "", _log("SCRIPT", "email_draft", f"Ollama error: {str(e)[:60]}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature: Document summary
# ─────────────────────────────────────────────────────────────────────────────

def summarize_document(text: str, doc_type: str) -> tuple[str, str]:
    """
    Ask Ollama for a plain-English executive summary of any uploaded document.
    Returns (summary_text, log_line).
    """
    cfg = get_config()
    if not cfg.get("enabled"):
        return "", _log("SCRIPT", "doc_summary", "Ollama disabled")

    ok, msg = ping(cfg["endpoint"])
    if not ok:
        return "", _log("SCRIPT", "doc_summary", f"offline — {msg}")

    prompt = f"""You are a mortgage expert. Summarize this {doc_type} for a processor who needs a quick overview.

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
        response = _generate(prompt, model=cfg.get("model"))
        log = _log("OLLAMA", "doc_summary", cfg.get("model", ""))
        return response, log
    except Exception as e:
        return "", _log("SCRIPT", "doc_summary", f"Ollama error: {str(e)[:60]}")
