from pii_sanitizer.integration import (
    redact_for_cloud_resilient,
    require_cloud_safe,
    restore_local_placeholders,
    secure_approval_system_prompt,
)


def test_resilient_redaction_combines_typed_and_legacy_rules():
    text = (
        "Borrower: Jane Example\n"
        "Monthly income: $8,500\n"
        "Routing number: 021000021"
    )

    sanitized, replacements, forced, remaining = redact_for_cloud_resilient(text)

    assert "Jane Example" not in sanitized
    assert "$8,500" not in sanitized
    assert "021000021" not in sanitized
    assert any(key.startswith("[BORROWER_") for key in replacements)
    assert remaining == []
    require_cloud_safe(sanitized)


def test_restore_is_case_insensitive_for_model_echoes():
    assert restore_local_placeholders(
        "Contact [borrower_1]",
        {"[BORROWER_1]": "Jane Example"},
    ) == "Contact Jane Example"


def test_secure_prompt_remains_available_through_integration():
    prompt = secure_approval_system_prompt("Extract conditions.")
    assert "Extract conditions." in prompt
    assert "privacy" in prompt.lower() or "sensitive" in prompt.lower()
