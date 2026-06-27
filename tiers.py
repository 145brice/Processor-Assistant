"""Subscription tiers and monthly scan limits — Processor Assistant.

App-side tier logic. The Stripe products/prices are wired later; each tier's
Stripe price ID is read from an env var (``TIER_<KEY>_PRICE_ID``) so it can be
filled in without code changes once the products exist in Stripe.

Year-one pricing:
    Free        $0       — 20 scans / month
    Starter     $9.99    — 75 scans / month
    Pro         $29.99   — 250 scans / month
    Unlimited   $49      — unlimited scans + priority support
"""

from __future__ import annotations

import os

# tier_key -> config. ``scan_limit`` of None means unlimited.
TIERS: dict[str, dict] = {
    "free":      {"name": "Free",      "price": 0.00,  "scan_limit": 20,   "priority": False},
    "starter":   {"name": "Starter",   "price": 9.99,  "scan_limit": 75,   "priority": False},
    "pro":       {"name": "Pro",       "price": 29.99, "scan_limit": 250,  "priority": False},
    "unlimited": {"name": "Unlimited", "price": 49.99, "scan_limit": None, "priority": True},
}

# Low → high, used for "upgrade to the next tier" suggestions.
TIER_ORDER = ["free", "starter", "pro", "unlimited"]


def stripe_price_id(tier_key: str) -> str:
    """Stripe price ID for a tier, read from env (placeholder until wired)."""
    return os.getenv(f"TIER_{tier_key.upper()}_PRICE_ID", "").strip()


def stripe_payment_link(tier_key: str) -> str:
    """Stripe Payment Link URL for a tier, read from env after Stripe setup."""
    return os.getenv(f"TIER_{tier_key.upper()}_PAYMENT_LINK", "").strip()


def tier_for_price_id(price_id: str) -> str:
    """Map a Stripe price ID back to a tier key (for the webhook). '' if unknown."""
    price_id = (price_id or "").strip()
    if not price_id:
        return ""
    for key in TIER_ORDER:
        if stripe_price_id(key) and stripe_price_id(key) == price_id:
            return key
    return ""


def tier_for_amount_cents(amount_cents: int | str | None) -> str:
    """Map a Stripe checkout/invoice amount to a tier key.

    This is a fallback for static Payment Links when Stripe events do not
    include expanded price IDs. Configured Price IDs still win.
    """
    try:
        cents = int(amount_cents or 0)
    except (TypeError, ValueError):
        return ""
    for key in ("starter", "pro", "unlimited"):
        expected = int(round(float(TIERS[key]["price"]) * 100))
        if cents == expected:
            return key
    return ""


def tier_for_profile(profile: dict | None) -> str:
    """Determine a user's tier from their app profile.

    Priority: explicit ``tier`` field → mapped Stripe price ID → legacy
    paid/beta status (treated as unlimited) → free.
    """
    p = profile or {}
    explicit = str(p.get("tier") or "").lower()
    if explicit in TIERS:
        return explicit
    mapped = tier_for_price_id(str(p.get("stripe_price_id") or ""))
    if mapped:
        return mapped
    status = str(p.get("subscription_status") or "").lower()
    plan = str(p.get("plan") or "").lower()
    if status in {"active", "paid", "beta_active"} or plan == "beta":
        # Paid but no tier mapped yet (owner/legacy beta) → full access.
        return "unlimited"
    return "free"


def scan_limit(tier_key: str) -> int | None:
    return TIERS.get(tier_key, TIERS["free"])["scan_limit"]


def next_tier(tier_key: str) -> str | None:
    """The tier above this one, or None if already top."""
    try:
        i = TIER_ORDER.index(tier_key)
    except ValueError:
        return "starter"
    return TIER_ORDER[i + 1] if i + 1 < len(TIER_ORDER) else None


def check_scan_quota(uid: str, profile: dict | None) -> dict:
    """Return this month's scan-quota status for a user.

    Keys: tier, tier_name, limit (None=unlimited), used, remaining
    (None=unlimited), allowed (bool), next_tier, next_tier_name.
    """
    tier_key = tier_for_profile(profile)
    limit = scan_limit(tier_key)

    used = 0
    if uid:
        try:
            import billing
            used = int(billing.get_usage(uid).get("scans", 0))
        except Exception:
            used = 0

    if limit is None:
        remaining: int | None = None
        allowed = True
    else:
        remaining = max(0, limit - used)
        allowed = used < limit

    nxt = next_tier(tier_key)
    return {
        "tier": tier_key,
        "tier_name": TIERS.get(tier_key, TIERS["free"])["name"],
        "limit": limit,
        "used": used,
        "remaining": remaining,
        "allowed": allowed,
        "next_tier": nxt,
        "next_tier_name": TIERS[nxt]["name"] if nxt else "",
    }
