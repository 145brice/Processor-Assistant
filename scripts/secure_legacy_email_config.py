"""Archive the unassigned legacy config encrypted; never assign it to a client."""
import json
import os
from pathlib import Path
import secrets
import sys

from dotenv import load_dotenv, set_key

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
import email_store


def main():
    load_dotenv(root / ".env", override=False)
    legacy = root / "email_config.json"
    if not legacy.exists():
        print("No legacy email configuration to archive.")
        return
    if not os.getenv("PA_SETTINGS_ENCRYPTION_KEY", "").strip():
        secret = secrets.token_urlsafe(48)
        set_key(str(root / ".env"), "PA_SETTINGS_ENCRYPTION_KEY", secret)
        os.environ["PA_SETTINGS_ENCRYPTION_KEY"] = secret
    raw = legacy.read_bytes()
    json.loads(raw)
    token = email_store.cipher().encrypt(raw).decode()
    archive = email_store.data_dir() / "legacy-unassigned.json"
    if archive.exists():
        raise RuntimeError("Legacy archive already exists; refusing to overwrite it.")
    email_store.atomic_json(archive, {"version": 1, "encrypted": token})
    saved = json.loads(archive.read_text(encoding="utf-8"))
    if email_store.cipher().decrypt(saved["encrypted"].encode()) != raw:
        raise RuntimeError("Archive verification failed; original file preserved.")
    legacy.unlink()
    print("Legacy credentials archived encrypted; plaintext file removed.")
    print("Keep the encryption key in .env private and backed up. Revoke the old app password.")


if __name__ == "__main__":
    main()
