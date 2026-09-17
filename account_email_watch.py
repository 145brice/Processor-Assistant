"""Inbox workers, attachments and results scoped to authenticated accounts."""
import copy
import email
import hashlib
import imaplib
import json
import re
import threading
import uuid
from datetime import datetime, timedelta
from email.header import decode_header

import email_store

PROVIDERS = {
    "Gmail": {"host": "imap.gmail.com", "port": 993},
    "Outlook": {"host": "imap-mail.outlook.com", "port": 993},
    "Yahoo": {"host": "imap.mail.yahoo.com", "port": 993},
    "Custom": {"host": "", "port": 993},
}
_watchers = {}
_registry_lock = threading.Lock()
_ACCEPT_EXT = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff",
               ".heic", ".heif", ".webp", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".rtf")


def for_user(user_key):
    email_store.account_dir(user_key)
    with _registry_lock:
        if user_key not in _watchers:
            watcher = EmailWatcher(user_key)
            _watchers[user_key] = watcher
            if watcher._enabled:
                try:
                    watcher.start()
                except ValueError:
                    watcher._last_status = "Saved inbox could not be resumed. Check your settings."
        return _watchers[user_key]


def _hval(raw):
    return "".join(value.decode(charset or "utf-8", errors="replace")
                   if isinstance(value, bytes) else str(value)
                   for value, charset in decode_header(raw))


def _safe_filename(raw):
    name = raw.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")[-180:] or "attachment"


class EmailWatcher:
    PROVIDERS = PROVIDERS
    def __init__(self, user_key):
        self.user_key = user_key
        self.directory = email_store.account_dir(user_key)
        self.incoming_dir = self.directory / "incoming"
        self._lock = threading.RLock()
        self._check_lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._last_time = None
        self._last_status = "Never checked"
        self._loans = []
        path = self.directory / "pending.json"
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self._matches = raw.get("matches", [])
        self._seen = set(raw.get("seen", []))
        self._enabled = bool(raw.get("enabled", False))

    def get_config(self):
        """Keep saved passwords out of browser widgets."""
        cfg = email_store.load(self.user_key)
        if cfg:
            cfg = {**cfg, "password_saved": bool(cfg.get("password"))}
            cfg.pop("password", None)
        return cfg

    def save_config(self, email_addr, password, provider, custom_host="", interval=5, since_hours=0):
        if provider not in PROVIDERS or interval not in (2, 5, 10, 15, 30) or since_hours not in (0, 1, 2, 3, 6, 12, 24):
            raise ValueError("Invalid email provider or check interval.")
        host = PROVIDERS[provider]["host"] or custom_host.strip()
        email_addr = email_addr.strip()
        if not host or "@" not in email_addr:
            raise ValueError("Enter a valid email address and IMAP hostname.")
        if not password:
            previous = email_store.load(self.user_key)
            if previous.get("email") != email_addr or previous.get("host") != host:
                raise ValueError("Enter an app password for the new inbox.")
            password = previous.get("password", "")
        if not password:
            raise ValueError("Enter an app password.")
        email_store.save(self.user_key, {"email": email_addr, "password": password, "provider": provider,
                         "host": host, "port": 993, "interval_minutes": interval, "since_hours": since_hours})
        return self.get_config()

    def set_loans(self, loans):
        from crm import _loan_belongs_to_user
        with self._lock:
            self._loans = [copy.deepcopy(loan) for loan in loans if _loan_belongs_to_user(loan, self.user_key)]

    def start(self, *, loans=()):
        cfg = email_store.load(self.user_key)
        if not cfg.get("password"):
            raise ValueError("Save your email credentials first.")
        self.set_loans(loans)
        with self._lock:
            if self.is_running():
                if self._stop.is_set():
                    raise ValueError("The inbox check is stopping. Please retry shortly.")
                return
            self._stop = threading.Event()
            self._enabled = True
            self._persist()
            self._thread = threading.Thread(target=self._loop, daemon=True,
                                            name="EmailWatcher-" + self.directory.name[:12])
            self._thread.start()

    def stop(self):
        self._stop.set()
        with self._lock:
            if self._enabled:
                self._enabled = False
                self._persist()

    def disconnect(self):
        self.stop()
        email_store.delete(self.user_key)

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def get_status(self):
        with self._lock:
            return {"running": self.is_running(), "last_time": self._last_time,
                    "last_status": self._last_status, "pending_count": len(self._matches)}

    def check_now(self, *, loans=None):
        if loans is not None:
            self.set_loans(loans)
        if not self._check_lock.acquire(blocking=False):
            return 0, "An inbox check is already in progress."
        try:
            cfg = email_store.load(self.user_key)
            if not cfg:
                return 0, "Not configured"
            found = self._check(cfg)
            message = f"{found} new attachment(s)" if found else "No new attachments"
        except imaplib.IMAP4.error:
            found, message = 0, "Error: Email login or inbox access failed. Check your app password."
        except Exception:
            # Provider exceptions may include credentials or private message content.
            found, message = 0, "Error: Could not check your inbox. Check your settings and try again."
        finally:
            self._check_lock.release()
        with self._lock:
            self._last_time = datetime.now().strftime("%I:%M %p")
            self._last_status = message
        return found, message

    def _persist(self):
        email_store.atomic_json(self.directory / "pending.json",
                                {"matches": self._matches, "seen": sorted(self._seen), "enabled": self._enabled})

    def get_matches(self):
        with self._lock:
            return copy.deepcopy(self._matches)

    def dismiss(self, idx):
        with self._lock:
            if 0 <= idx < len(self._matches):
                self._matches.pop(idx)
                self._persist()

    def clear_all(self):
        with self._lock:
            self._matches.clear()
            self._persist()

    def _loop(self):
        while not self._stop.is_set():
            # Never access session state or the shared pipeline file from a worker.
            try:
                import supabase_sync
                result = supabase_sync.load_pipeline_snapshot(user_key=self.user_key)
                if result.get("ok"):
                    self.set_loans(result["loans"])
            except Exception:
                pass
            self.check_now()
            try:
                interval = email_store.load(self.user_key).get("interval_minutes", 5)
            except Exception:
                interval = 5
            self._stop.wait(interval * 60)

    def _check(self, config):
        mail = imaplib.IMAP4_SSL(config["host"], int(config.get("port", 993)), timeout=30)
        try:
            mail.login(config["email"], config["password"])
            status, _ = mail.select("inbox", readonly=True)
            if status != "OK":
                raise imaplib.IMAP4.error("Inbox unavailable")
            since = int(config.get("since_hours", 0))
            query = "UNSEEN" if not since else "SINCE " + (datetime.now() - timedelta(hours=since)).strftime("%d-%b-%Y")
            status, data = mail.uid("search", None, query)
            if status != "OK":
                raise imaplib.IMAP4.error("Search failed")
            validity = str(mail.response("UIDVALIDITY")[1])
            identity = f'{config["host"]}:{config["email"]}:{validity}'
            found = 0
            with self._lock:
                loans = copy.deepcopy(self._loans)
            for uid in (data[0] or b"").split():
                status, fetched = mail.uid("fetch", uid, "(BODY.PEEK[])")
                if status != "OK":
                    continue
                raw = next((item[1] for item in fetched if isinstance(item, tuple)), None)
                if not raw:
                    continue
                msg = email.message_from_bytes(raw)
                sender, subject = _hval(msg.get("From", "")), _hval(msg.get("Subject", ""))
                for index, part in enumerate(msg.walk()):
                    filename = _safe_filename(_hval(part.get_filename() or ""))
                    if not part.get_filename() or not filename.lower().endswith(_ACCEPT_EXT):
                        continue
                    key = hashlib.sha256(f"{identity}:{uid.decode()}:{index}".encode()).hexdigest()
                    if key in self._seen:
                        continue
                    payload = part.get_payload(decode=True)
                    if not payload:
                        continue
                    if filename.lower().endswith(".pdf"):
                        from doc_verify import verify
                        result = verify(payload, filename, borrower_hint=f"{sender} {subject}", loans=loans)
                    else:
                        from doc_verify import _match_borrower
                        result = _match_borrower("", filename, f"{sender} {subject}", loans=loans)
                    self.incoming_dir.mkdir(parents=True, exist_ok=True)
                    path = self.incoming_dir / (uuid.uuid4().hex + "_" + filename)
                    with path.open("xb") as handle:
                        handle.write(payload)
                    with self._lock:
                        self._matches.append({**result, "filename": filename, "file_path": str(path),
                                              "sender": sender, "subject": subject,
                                              "received": datetime.now().strftime("%I:%M %p")})
                        self._seen.add(key)
                        self._persist()
                    found += 1
            return found
        finally:
            try:
                mail.logout()
            except Exception:
                pass
