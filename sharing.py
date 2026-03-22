"""
Sharing Engine — Processor Traien
Private loan sharing between team members via personal inbox folders.

How it works:
  - Each user has their own "inbox folder" (a local path they configure once).
  - When you share a loan with Jane, the app writes one file directly into
    Jane's inbox folder path (network share, UNC path, or same machine).
  - Jane opens the app, sees "New shared loan from Maria", accepts it.
  - Jane makes updates, clicks "Send Update" — the file goes back to your inbox.

No central server. No hub. Just direct file drops between inboxes.
100% offline.
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path

_APP_DIR = os.path.dirname(__file__)
_TEAM_FILE = os.path.join(_APP_DIR, "team.json")

# Default local inbox if none configured
_DEFAULT_INBOX = os.path.join(_APP_DIR, "inbox")


# ── Config helpers ─────────────────────────────────────────────────────────────

def get_team_config() -> dict:
    """Load team config (my inbox path + team member list)."""
    if not os.path.exists(_TEAM_FILE):
        return {"my_name": "", "my_inbox": _DEFAULT_INBOX, "members": []}
    try:
        with open(_TEAM_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"my_name": "", "my_inbox": _DEFAULT_INBOX, "members": []}


def save_team_config(config: dict):
    with open(_TEAM_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_my_inbox() -> str:
    return get_team_config().get("my_inbox", _DEFAULT_INBOX)


def get_members() -> list:
    """Return list of team member dicts: {name, role, inbox}."""
    return get_team_config().get("members", [])


def get_member_map() -> dict:
    """Return {name: member_dict} for fast lookup."""
    return {m["name"]: m for m in get_members()}


def add_member(name: str, role: str, inbox_path: str):
    """Add or update a team member."""
    config = get_team_config()
    members = config.get("members", [])
    for m in members:
        if m["name"] == name:
            m["role"] = role
            m["inbox"] = inbox_path.strip()
            config["members"] = members
            save_team_config(config)
            return
    members.append({"name": name.strip(), "role": role, "inbox": inbox_path.strip()})
    config["members"] = members
    save_team_config(config)


def remove_member(name: str):
    config = get_team_config()
    config["members"] = [m for m in config.get("members", []) if m["name"] != name]
    save_team_config(config)


def set_my_inbox(path: str, name: str = ""):
    config = get_team_config()
    config["my_inbox"] = path.strip()
    if name:
        config["my_name"] = name.strip()
    save_team_config(config)


def test_inbox(path: str) -> tuple[bool, str]:
    """Test whether an inbox path is reachable. Returns (ok, message)."""
    if not path:
        return False, "No path configured"
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, "_gopher_test.tmp")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return True, f"Connected — {path}"
    except Exception as e:
        return False, str(e)


# ── Shared loan file helpers ───────────────────────────────────────────────────

def _make_filename(share_id: str, loan_num: str) -> str:
    safe_num = loan_num.replace(" ", "_").replace("\\", "").replace("/", "")
    return f"loan_{share_id}_{safe_num}.shared.json"


def _build_shared_payload(loan: dict, sender_name: str, sender_inbox: str,
                           recipient_names: list, version: int = 1) -> dict:
    return {
        "share_id": loan.get("share_id") or str(uuid.uuid4())[:8],
        "loan_id": loan.get("id"),
        "loan_num": loan.get("loan_num", ""),
        "borrower": loan.get("borrower", ""),
        "status": loan.get("status", "Pending"),
        "due_date": loan.get("due_date", ""),
        "missing_docs": loan.get("missing_docs", ""),
        "folder_path": loan.get("folder_path", ""),
        "notes": loan.get("notes", ""),
        "owner": loan.get("created_by") or sender_name,
        "owner_inbox": sender_inbox,
        "shared_with": recipient_names,
        "last_updated_by": sender_name,
        "last_updated": datetime.now().isoformat()[:19],
        "version": version,
    }


# ── Core sharing actions ───────────────────────────────────────────────────────

def share_loan(loan: dict, recipient_names: list, sender_name: str) -> dict:
    """
    Share a loan with a list of team members by writing a file to each
    person's configured inbox folder.

    Returns dict: {name: "ok" | error_message}
    """
    config = get_team_config()
    member_map = get_member_map()
    sender_inbox = config.get("my_inbox", _DEFAULT_INBOX)

    payload = _build_shared_payload(
        loan, sender_name, sender_inbox, recipient_names,
        version=loan.get("share_version", 0) + 1,
    )
    filename = _make_filename(payload["share_id"], loan.get("loan_num", "x"))

    results = {}
    for name in recipient_names:
        member = member_map.get(name)
        if not member:
            results[name] = "Not in team list"
            continue
        inbox = member.get("inbox", "").strip()
        if not inbox:
            results[name] = "No inbox path set for this person"
            continue
        try:
            os.makedirs(inbox, exist_ok=True)
            fpath = os.path.join(inbox, filename)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            results[name] = "ok"
        except Exception as e:
            results[name] = str(e)

    return results


def send_update(shared_loan: dict, sender_name: str, updates: dict) -> dict:
    """
    Send an updated version of a shared loan back to the owner and all
    shared_with members (except the sender).

    updates: dict of fields to merge in (status, notes, missing_docs, etc.)
    Returns dict: {name: "ok" | error_message}
    """
    config = get_team_config()
    member_map = get_member_map()

    # Merge updates into the shared loan
    merged = {**shared_loan, **updates}
    merged["last_updated_by"] = sender_name
    merged["last_updated"] = datetime.now().isoformat()[:19]
    merged["version"] = shared_loan.get("version", 1) + 1

    filename = _make_filename(merged["share_id"], merged.get("loan_num", "x"))
    results = {}

    # Recipients = owner + all shared_with, minus sender
    all_recipients = []
    owner = merged.get("owner", "")
    if owner and owner != sender_name:
        all_recipients.append(("__owner__", merged.get("owner_inbox", "")))
        results[owner] = None  # placeholder

    for name in merged.get("shared_with", []):
        if name == sender_name:
            continue
        member = member_map.get(name)
        inbox = member.get("inbox", "").strip() if member else ""
        all_recipients.append((name, inbox))
        results[name] = None

    for name, inbox in all_recipients:
        display = owner if name == "__owner__" else name
        if not inbox:
            results[display] = "No inbox path"
            continue
        try:
            os.makedirs(inbox, exist_ok=True)
            fpath = os.path.join(inbox, filename)
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            results[display] = "ok"
        except Exception as e:
            results[display] = str(e)

    return results


# ── Inbox scanning ─────────────────────────────────────────────────────────────

def scan_inbox() -> list:
    """
    Read all .shared.json files in the local inbox folder.
    Returns list of shared loan dicts, newest first.
    """
    inbox = get_my_inbox()
    if not inbox:
        return []
    # Auto-create local default inbox
    if inbox == _DEFAULT_INBOX:
        os.makedirs(inbox, exist_ok=True)
    if not os.path.isdir(inbox):
        return []

    results = []
    try:
        for fname in os.listdir(inbox):
            if not fname.endswith(".shared.json"):
                continue
            fpath = os.path.join(inbox, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["_file"] = fpath
                results.append(data)
            except Exception:
                continue
    except Exception:
        return []

    results.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
    return results


def dismiss_from_inbox(file_path: str):
    """Delete a shared loan file from the inbox after accepting it."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


def inbox_count() -> int:
    """Quick count of items in inbox (for badge display)."""
    return len(scan_inbox())
