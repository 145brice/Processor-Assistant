"""Stripe webhook handling for Processor Assistant.

This module intentionally avoids the Stripe SDK so the webhook can run with the
existing dependency set. It verifies Stripe signatures using the documented HMAC
scheme, then updates the signed-in user's app profile in Supabase settings.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time


STRIPE_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
}


def _webhook_secret() -> str:
    return os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()


def verify_signature(payload: bytes, signature_header: str, tolerance_seconds: int = 300) -> tuple[bool, str]:
    """Validate Stripe-Signature for the raw request body."""
    secret = _webhook_secret()
    if not secret:
        return False, "STRIPE_WEBHOOK_SECRET is not set."
    if not signature_header:
        return False, "Missing Stripe-Signature header."

    parts: dict[str, list[str]] = {}
    for chunk in signature_header.split(","):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        parts.setdefault(key, []).append(value)

    timestamps = parts.get("t") or []
    signatures = parts.get("v1") or []
    if not timestamps or not signatures:
        return False, "Invalid Stripe signature header."

    timestamp = timestamps[0]
    try:
        ts_int = int(timestamp)
    except ValueError:
        return False, "Invalid Stripe timestamp."
    if abs(time.time() - ts_int) > tolerance_seconds:
        return False, "Stripe signature timestamp is too old."

    signed_payload = timestamp.encode("utf-8") + b"." + payload
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, sig) for sig in signatures):
        return False, "Stripe signature mismatch."
    return True, "ok"


def _customer_email(obj: dict) -> str:
    details = obj.get("customer_details") or {}
    if isinstance(details, dict) and details.get("email"):
        return str(details["email"]).strip().lower()
    return str(obj.get("customer_email") or obj.get("email") or "").strip().lower()


def _subscription_id(obj: dict) -> str:
    return str(obj.get("subscription") or obj.get("id") or "").strip()


def _price_id(obj: dict) -> str:
    """Best-effort extraction of the Stripe price ID from an event object.

    Subscription objects carry items.data[].price.id; checkout sessions and
    invoices may carry it on lines/line_items. Returns '' if not present
    (e.g. checkout.session.completed without expanded line items).
    """
    items = (obj.get("items") or {})
    data = items.get("data") if isinstance(items, dict) else None
    if isinstance(data, list) and data:
        price = (data[0] or {}).get("price") or {}
        if isinstance(price, dict) and price.get("id"):
            return str(price["id"]).strip()
    for key in ("lines", "line_items"):
        block = obj.get(key) or {}
        rows = block.get("data") if isinstance(block, dict) else None
        if isinstance(rows, list) and rows:
            price = (rows[0] or {}).get("price") or {}
            if isinstance(price, dict) and price.get("id"):
                return str(price["id"]).strip()
    return ""


def _customer_id(obj: dict) -> str:
    return str(obj.get("customer") or "").strip()


def _status_for_event(event_type: str, obj: dict) -> str:
    if event_type == "checkout.session.completed":
        return "active"
    if event_type == "invoice.payment_succeeded":
        return "active"
    if event_type == "invoice.payment_failed":
        return "past_due"
    if event_type == "customer.subscription.deleted":
        return "canceled"
    if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        return str(obj.get("status") or "active").strip().lower()
    return str(obj.get("status") or "active").strip().lower()


def handle_stripe_webhook(payload: bytes, signature_header: str) -> tuple[int, dict]:
    ok, message = verify_signature(payload, signature_header)
    if not ok:
        return 400, {"ok": False, "error": message}

    try:
        event = json.loads(payload.decode("utf-8"))
    except Exception as exc:
        return 400, {"ok": False, "error": f"Invalid JSON: {exc}"}

    event_type = str(event.get("type") or "")
    if event_type not in STRIPE_EVENTS:
        return 200, {"ok": True, "ignored": event_type}

    obj = ((event.get("data") or {}).get("object") or {})
    if not isinstance(obj, dict):
        return 400, {"ok": False, "error": "Missing event data object."}

    email = _customer_email(obj)
    if not email and event_type.startswith("invoice."):
        # Invoice events often put customer email directly on the invoice object.
        email = str(obj.get("customer_email") or "").strip().lower()
    if not email:
        return 202, {"ok": False, "error": "No customer email on Stripe event; cannot map to app user."}

    status = _status_for_event(event_type, obj)
    # Map the Stripe price ID to one of our app tiers (price IDs come from env).
    price_id = _price_id(obj)
    tier = ""
    try:
        import tiers as _tiers
        tier = _tiers.tier_for_price_id(price_id)
    except Exception:
        tier = ""
    try:
        import supabase_auth

        result = supabase_auth.update_subscription_by_email(
            email,
            status=status,
            stripe_customer_id=_customer_id(obj),
            stripe_subscription_id=_subscription_id(obj),
            plan=(tier or "beta"),
            tier=tier,
            stripe_price_id=price_id,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}

    if not result.get("ok"):
        return 202, {"ok": False, "email": email, "status": status, "error": result.get("error", "Profile not updated.")}
    return 200, {"ok": True, "email": email, "status": status, "updated": result.get("updated", 0)}
