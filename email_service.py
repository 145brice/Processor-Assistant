"""Transactional email helpers backed by Resend.

Email is deliberately best-effort: account creation and Stripe entitlement
updates must still succeed if the email provider is temporarily unavailable.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


RESEND_URL = "https://api.resend.com/emails"


def is_configured() -> bool:
    return bool(os.getenv("RESEND_API_KEY", "").strip() and os.getenv("RESEND_FROM", "").strip())


def send_email(to: str, subject: str, text_body: str, idempotency_key: str) -> dict:
    """Send one plain-text transactional email through Resend."""
    recipient = (to or "").strip()
    if not recipient:
        return {"ok": False, "skipped": True, "error": "Missing recipient."}
    if not is_configured():
        return {"ok": False, "skipped": True, "error": "Resend is not configured."}

    payload = {
        "from": os.environ["RESEND_FROM"].strip(),
        "to": [recipient],
        "subject": subject,
        "text": text_body,
    }
    request = urllib.request.Request(
        RESEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + os.environ["RESEND_API_KEY"].strip(),
            "Content-Type": "application/json",
            "User-Agent": "EdgeLandings-ProcessorAssistant/1.0",
            "Idempotency-Key": idempotency_key[:256],
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            return {"ok": 200 <= response.status < 300, "id": data.get("id", "")}
    except urllib.error.HTTPError as exc:
        detail = exc.read(2048).decode("utf-8", errors="replace")
        try:
            parsed = json.loads(detail)
            detail = str(parsed.get("message") or parsed.get("error") or detail)
        except (json.JSONDecodeError, AttributeError):
            pass
        return {"ok": False, "error": f"Resend returned HTTP {exc.code}: {detail[:500]}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _admin_email() -> str:
    return os.getenv("ADMIN_NOTIFICATION_EMAIL", "").strip()


def send_signup_emails(email: str, display_name: str, role: str, user_id: str) -> list[dict]:
    """Welcome the new user and optionally notify the site owner."""
    first_name = (display_name or "").strip().split(" ", 1)[0] or "there"
    app_url = (
        os.getenv("PA_APP_URL", "").strip()
        or os.getenv("PUBLIC_APP_URL", "").strip()
        or os.getenv("APP_BASE_URL", "").strip()
        or "https://edgelandings.com"
    ).rstrip("/")
    results = [
        send_email(
            email,
            "Welcome to Processor Assistant",
            (
                f"Hi {first_name},\n\n"
                "Your Processor Assistant account is ready. You can sign in and start "
                "organizing your pipeline and reviewing loan documents.\n\n"
                f"Open Processor Assistant: {app_url}\n\n"
                "- Edge Landings"
            ),
            f"processor-signup-welcome-{user_id}",
        )
    ]
    admin = _admin_email()
    if admin:
        results.append(
            send_email(
                admin,
                "New Processor Assistant account",
                f"A new account was created.\n\nName: {display_name}\nEmail: {email}\nRole: {role}",
                f"processor-signup-admin-{user_id}",
            )
        )
    return results


def send_purchase_emails(
    email: str,
    tier_name: str,
    amount_cents: int,
    event_id: str,
) -> list[dict]:
    """Confirm a new checkout and optionally notify the site owner."""
    amount = f"${amount_cents / 100:,.2f}" if amount_cents else "your subscription payment"
    results = [
        send_email(
            email,
            f"Your {tier_name} plan is active",
            (
                "Thank you for your purchase.\n\n"
                f"Plan: {tier_name}\nPayment: {amount}\n\n"
                "Your paid Processor Assistant access is now active. Stripe will send "
                "your official payment receipt separately.\n\n"
                "- Edge Landings"
            ),
            f"processor-purchase-customer-{event_id}",
        )
    ]
    admin = _admin_email()
    if admin:
        results.append(
            send_email(
                admin,
                "New Processor Assistant purchase",
                f"A purchase completed.\n\nCustomer: {email}\nPlan: {tier_name}\nPayment: {amount}",
                f"processor-purchase-admin-{event_id}",
            )
        )
    return results
