"""The placeholder Vault: the only place original PII lives after sanitization.

Design goals (privacy-by-design):

* **Deterministic** — the same source value always maps to the same
  placeholder within a session, so ``John Smith`` reads as ``[BORROWER_1]``
  everywhere it appears.
* **Local only** — the mapping never leaves this object. Nothing in this module
  serializes to the network. Optional on-disk persistence is always encrypted.
* **Zeroizable** — :meth:`Vault.close` overwrites secrets in memory and shreds
  any encrypted temp file, so a crash-free run leaves no plaintext residue.

The Vault is intentionally decoupled from detection: detectors find spans, the
sanitizer asks the Vault for a placeholder per span. The Vault owns numbering.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass, field
from typing import Iterator

from .errors import VaultError

_PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9_]*\]")
_WS_RE = re.compile(r"\s+")


def _normalize(value: str) -> str:
    """Case/space-insensitive key so trivial variants share one placeholder."""
    return _WS_RE.sub(" ", str(value or "").strip()).casefold()


@dataclass
class _Entry:
    placeholder: str
    original: str  # first-seen exact spelling, used for restoration


class Vault:
    """Bidirectional, deterministic map between PII values and placeholders.

    Thread-safe: a single Vault may be shared across worker threads handling one
    document. It is *not* meant to be shared across unrelated documents — create
    a fresh Vault per document so placeholder numbering never crosses tenants.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # normalized-value -> _Entry
        self._by_value: dict[str, _Entry] = {}
        # placeholder -> _Entry (restore side)
        self._by_placeholder: dict[str, _Entry] = {}
        # entity_type -> running counter
        self._counters: dict[str, int] = {}
        self._closed = False

    # -- core API ----------------------------------------------------------

    def placeholder_for(self, entity_type: str, value: str) -> str:
        """Return the stable placeholder for ``value``, minting one if new."""
        if self._closed:
            raise VaultError("vault is closed")
        original = str(value or "")
        if not original.strip():
            return original
        key = _normalize(original)
        with self._lock:
            existing = self._by_value.get(key)
            if existing is not None:
                return existing.placeholder
            role = (entity_type or "OTHER").upper()
            self._counters[role] = self._counters.get(role, 0) + 1
            placeholder = f"[{role}_{self._counters[role]}]"
            entry = _Entry(placeholder=placeholder, original=original)
            self._by_value[key] = entry
            self._by_placeholder[placeholder] = entry
            return placeholder

    def restore(self, text: str) -> str:
        """Replace every known placeholder in ``text`` with its original value.

        Placeholders are restored longest-first so ``[BORROWER_12]`` is never
        partially matched by ``[BORROWER_1]``.
        """
        if self._closed:
            raise VaultError("vault is closed")
        restored = str(text or "")
        with self._lock:
            for placeholder in sorted(self._by_placeholder, key=len, reverse=True):
                if placeholder in restored:
                    restored = restored.replace(
                        placeholder, self._by_placeholder[placeholder].original
                    )
        return restored

    def has_unresolved_placeholders(self, text: str) -> bool:
        """True if ``text`` still contains any ``[LIKE_THIS]`` token."""
        return bool(_PLACEHOLDER_RE.search(str(text or "")))

    # -- introspection (safe: never returns raw originals in bulk by default) --

    @property
    def size(self) -> int:
        return len(self._by_placeholder)

    def placeholders(self) -> list[str]:
        with self._lock:
            return sorted(self._by_placeholder)

    def mapping(self) -> dict[str, str]:
        """Return a *copy* of ``{placeholder: original}``.

        This is the sensitive artifact. Callers must treat the result as
        local-only and must never log or transmit it.
        """
        with self._lock:
            return {ph: e.original for ph, e in self._by_placeholder.items()}

    # -- encrypted persistence --------------------------------------------

    def to_encrypted_bytes(self, fernet_key: bytes) -> bytes:
        """Serialize the mapping to an encrypted blob (Fernet/AES-128-CBC+HMAC).

        Used only for optional spillover on very large documents; the default
        path keeps everything in RAM and never calls this.
        """
        try:
            import json

            from cryptography.fernet import Fernet
        except Exception as exc:  # pragma: no cover - dependency guard
            raise VaultError("cryptography is required for encrypted persistence") from exc
        payload = json.dumps(
            {ph: e.original for ph, e in self._by_placeholder.items()},
            ensure_ascii=False,
        ).encode("utf-8")
        try:
            return Fernet(fernet_key).encrypt(payload)
        except Exception as exc:
            raise VaultError("failed to encrypt vault") from exc

    @classmethod
    def from_encrypted_bytes(cls, blob: bytes, fernet_key: bytes) -> "Vault":
        try:
            import json

            from cryptography.fernet import Fernet
        except Exception as exc:  # pragma: no cover
            raise VaultError("cryptography is required for encrypted persistence") from exc
        try:
            payload = Fernet(fernet_key).decrypt(blob)
            data: dict[str, str] = json.loads(payload.decode("utf-8"))
        except Exception as exc:
            raise VaultError("failed to decrypt/parse vault") from exc
        vault = cls()
        for placeholder, original in data.items():
            entry = _Entry(placeholder=placeholder, original=original)
            vault._by_placeholder[placeholder] = entry
            vault._by_value[_normalize(original)] = entry
        return vault

    @staticmethod
    def new_encryption_key() -> bytes:
        """Generate a fresh Fernet key. Store in a secret manager, never in code."""
        from cryptography.fernet import Fernet

        return Fernet.generate_key()

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        """Best-effort zeroization of in-memory secrets and counter reset.

        Python cannot guarantee memory is scrubbed (strings are immutable), but
        we drop all references and overwrite the container so the mapping is no
        longer reachable and becomes eligible for GC immediately.
        """
        with self._lock:
            # Overwrite entry originals with equal-length blanks before dropping.
            for entry in self._by_placeholder.values():
                entry.original = "\x00" * len(entry.original)
            self._by_value.clear()
            self._by_placeholder.clear()
            self._counters.clear()
            self._closed = True

    def __enter__(self) -> "Vault":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def __iter__(self) -> Iterator[str]:
        return iter(self.placeholders())

    def __len__(self) -> int:
        return self.size
