"""
Email Inbox Watcher — Processor Traien
Checks your inbox every N minutes for new PDF attachments,
extracts borrower names from the text, and matches them to your pipeline.
100% local — IMAP only, no cloud, no third-party servers.

Gmail setup (one-time):
  myaccount.google.com → Security → 2-Step Verification → App Passwords
  → Select app: Mail → Select device: Windows Computer → Generate
  Use the 16-character code as your password here (not your real password).

Outlook setup:
  Account → Security → Advanced security options → App passwords
"""

import imaplib
import email as email_lib
import threading
import time
import os
import json
import io
from datetime import datetime
from email.header import decode_header as _dh

try:
    from pypdf import PdfReader
    _PYPDF = True
except ImportError:
    _PYPDF = False

_APP_DIR  = os.path.dirname(os.path.abspath(__file__))
_CFG_FILE = os.path.join(_APP_DIR, "email_config.json")
_INBOX_DIR = os.path.join(_APP_DIR, "incoming")

# ── Module-level state (persists across Streamlit reruns in same process) ─────
_thread: threading.Thread | None = None
_running = False
_last_time: str | None = None
_last_status = "Never checked"
_matches: list[dict] = []          # pending borrower-match cards
_lock = threading.Lock()


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

PROVIDERS = {
    "Gmail":   {"host": "imap.gmail.com",         "port": 993},
    "Outlook": {"host": "imap-mail.outlook.com",  "port": 993},
    "Yahoo":   {"host": "imap.mail.yahoo.com",    "port": 993},
    "Custom":  {"host": "",                       "port": 993},
}


def get_config() -> dict:
    if not os.path.exists(_CFG_FILE):
        return {}
    try:
        with open(_CFG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(email_addr: str, password: str, provider: str,
                custom_host: str = "", interval: int = 5,
                since_hours: int = 0) -> dict:
    host = PROVIDERS.get(provider, {}).get("host") or custom_host
    port = PROVIDERS.get(provider, {}).get("port", 993)
    cfg = {
        "email":            email_addr,
        "password":         password,
        "provider":         provider,
        "host":             host,
        "port":             port,
        "interval_minutes": interval,
        "since_hours":      since_hours,   # 0 = all unseen, N = only last N hours
    }
    with open(_CFG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg


# ─────────────────────────────────────────────────────────────────────────────
# Start / Stop
# ─────────────────────────────────────────────────────────────────────────────

def start(config: dict | None = None):
    global _thread, _running
    if is_running():
        return
    if config is None:
        config = get_config()
    if not config.get("host") or not config.get("email"):
        raise ValueError("Email not configured — set up credentials first.")
    _running = True
    _thread = threading.Thread(target=_loop, args=(config,), daemon=True, name="EmailWatcher")
    _thread.start()


def stop():
    global _running
    _running = False


def is_running() -> bool:
    return _running and _thread is not None and _thread.is_alive()


def get_status() -> dict:
    return {
        "running":       is_running(),
        "last_time":     _last_time,
        "last_status":   _last_status,
        "pending_count": len(_matches),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Pending matches API
# ─────────────────────────────────────────────────────────────────────────────

def get_matches() -> list[dict]:
    with _lock:
        return list(_matches)


def dismiss(idx: int):
    with _lock:
        if 0 <= idx < len(_matches):
            _matches.pop(idx)


def clear_all():
    with _lock:
        _matches.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Background loop
# ─────────────────────────────────────────────────────────────────────────────

def _loop(config: dict):
    global _last_time, _last_status
    interval_secs = config.get("interval_minutes", 5) * 60

    while _running:
        try:
            found = _check(config)
            _last_time   = datetime.now().strftime("%I:%M %p")
            _last_status = f"✓ {found} new PDF(s)" if found else "✓ No new attachments"
        except Exception as exc:
            _last_time   = datetime.now().strftime("%I:%M %p")
            _last_status = f"Error: {str(exc)[:100]}"

        # Sleep in 3-second chunks so stop() is responsive
        elapsed = 0
        while _running and elapsed < interval_secs:
            time.sleep(3)
            elapsed += 3


# ─────────────────────────────────────────────────────────────────────────────
# IMAP check
# ─────────────────────────────────────────────────────────────────────────────

def _check(config: dict) -> int:
    mail = imaplib.IMAP4_SSL(config["host"], int(config.get("port", 993)))
    mail.login(config["email"], config["password"])
    mail.select("inbox")

    since_hours = int(config.get("since_hours", 0))
    if since_hours > 0:
        from datetime import datetime as _dt, timedelta as _td
        since_date = (_dt.now() - _td(hours=since_hours)).strftime("%d-%b-%Y")
        _, data = mail.search(None, f'UNSEEN SINCE {since_date}')
    else:
        _, data = mail.search(None, "UNSEEN")
    eids = data[0].split()

    found = 0
    for eid in eids:
        try:
            _, msg_data = mail.fetch(eid, "(RFC822)")
            raw_email   = msg_data[0][1]
            msg         = email_lib.message_from_bytes(raw_email)
            sender      = _hval(msg.get("From",    ""))
            subject     = _hval(msg.get("Subject", ""))

            for part in msg.walk():
                ctype = part.get_content_type()
                disp  = str(part.get("Content-Disposition", ""))
                if "attachment" not in disp and ctype != "application/pdf":
                    continue
                fname = _hval(part.get_filename() or "")
                if not fname.lower().endswith(".pdf"):
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue

                found += 1
                os.makedirs(_INBOX_DIR, exist_ok=True)
                save_path = os.path.join(_INBOX_DIR, fname)
                with open(save_path, "wb") as f:
                    f.write(payload)

                from doc_verify import verify as _verify
                v = _verify(payload, fname, borrower_hint=f"{sender} {subject}")
                with _lock:
                    _matches.append({
                        "filename":  fname,
                        "file_path": save_path,
                        "sender":    sender,
                        "subject":   subject,
                        "received":  datetime.now().strftime("%I:%M %p"),
                        **v,
                    })
        except Exception:
            continue

    mail.logout()
    return found


def _hval(raw: str) -> str:
    """Decode an email header value to plain string."""
    parts = _dh(raw)
    out   = []
    for bval, charset in parts:
        if isinstance(bval, bytes):
            out.append(bval.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(str(bval))
    return "".join(out)


# ─────────────────────────────────────────────────────────────────────────────
# PDF → pipeline borrower matching
# ─────────────────────────────────────────────────────────────────────────────

def _match(pdf_bytes: bytes, filename: str, sender: str, subject: str) -> dict:
    """
    Read up to 3 pages of the PDF, search for pipeline borrower names,
    return the best match with a confidence score.
    """
    text = ""
    if _PYPDF:
        try:
            rdr = PdfReader(io.BytesIO(pdf_bytes))
            for page in rdr.pages[:3]:
                text += (page.extract_text() or "") + " "
        except Exception:
            pass

    search_blob = f"{text} {sender} {subject}".lower()

    try:
        from crm import get_all_loans
        loans = get_all_loans()
    except Exception:
        loans = []

    if not loans:
        return _no_match()

    try:
        from thefuzz import fuzz
        _fuzzy = True
    except ImportError:
        _fuzzy = False

    best_loan  = None
    best_score = 0

    for loan in loans:
        bname = loan.get("borrower", "").strip()
        if not bname:
            continue

        # Exact substring → highest confidence
        if bname.lower() in search_blob:
            score = 95
        elif _fuzzy:
            words = [w for w in bname.lower().split() if len(w) > 2]
            scores = [fuzz.partial_ratio(w, search_blob) for w in words]
            score  = max(scores) if scores else 0
        else:
            score = 0

        if score > best_score:
            best_score = score
            best_loan  = loan

    if best_score >= 80 and best_loan:
        return {
            "loan_id":          best_loan.get("id"),
            "loan_num":         best_loan.get("loan_num", ""),
            "borrower":         best_loan.get("borrower", ""),
            "confidence":       best_score,
            "suggestion":       "match",
            "suggested_folder": best_loan.get("folder_path", ""),
        }
    if best_score >= 50 and best_loan:
        return {
            "loan_id":          best_loan.get("id"),
            "loan_num":         best_loan.get("loan_num", ""),
            "borrower":         best_loan.get("borrower", ""),
            "confidence":       best_score,
            "suggestion":       "possible",
            "suggested_folder": best_loan.get("folder_path", ""),
        }
    return _no_match()


def _no_match() -> dict:
    return {
        "loan_id": None, "loan_num": "", "borrower": None,
        "confidence": 0, "suggestion": "unknown", "suggested_folder": "",
    }
