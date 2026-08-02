"""Vault: determinism, restoration, and lifecycle."""

from __future__ import annotations

import pytest

from pii_sanitizer.errors import VaultError
from pii_sanitizer.vault import Vault


def test_same_value_same_placeholder():
    v = Vault()
    a = v.placeholder_for("BORROWER", "John Smith")
    b = v.placeholder_for("BORROWER", "John Smith")
    assert a == b == "[BORROWER_1]"


def test_case_and_space_insensitive_key():
    v = Vault()
    a = v.placeholder_for("BORROWER", "John Smith")
    b = v.placeholder_for("BORROWER", "  john   smith ")
    assert a == b


def test_distinct_values_distinct_placeholders_and_numbering():
    v = Vault()
    assert v.placeholder_for("BORROWER", "John Smith") == "[BORROWER_1]"
    assert v.placeholder_for("COBORROWER", "Jane Smith") == "[COBORROWER_1]"
    assert v.placeholder_for("BORROWER", "Bob Jones") == "[BORROWER_2]"


def test_restore_roundtrip():
    v = Vault()
    ph = v.placeholder_for("EMAIL", "a@b.com")
    text = f"Contact them at {ph} today."
    assert v.restore(text) == "Contact them at a@b.com today."


def test_restore_longest_first_no_partial_collision():
    v = Vault()
    for i in range(12):
        v.placeholder_for("BORROWER", f"Person {i}")
    # [BORROWER_12] must not be corrupted by [BORROWER_1] restoration.
    text = "[BORROWER_12] and [BORROWER_1]"
    restored = v.restore(text)
    assert "Person 11" in restored  # 0-indexed source -> 12th is "Person 11"
    assert "Person 0" in restored
    assert "[BORROWER" not in restored


def test_empty_value_returns_unchanged():
    v = Vault()
    assert v.placeholder_for("BORROWER", "   ") == "   "


def test_encrypted_roundtrip():
    v = Vault()
    v.placeholder_for("SSN", "123-45-6789")
    key = Vault.new_encryption_key()
    blob = v.to_encrypted_bytes(key)
    assert b"123-45-6789" not in blob  # ciphertext must not contain plaintext
    v2 = Vault.from_encrypted_bytes(blob, key)
    assert v2.restore("[SSN_1]") == "123-45-6789"


def test_close_zeroizes_and_blocks_use():
    v = Vault()
    v.placeholder_for("BORROWER", "John Smith")
    v.close()
    with pytest.raises(VaultError):
        v.placeholder_for("BORROWER", "Jane Smith")


def test_context_manager_closes():
    with Vault() as v:
        v.placeholder_for("EMAIL", "a@b.com")
        assert v.size == 1
    assert v._closed is True
