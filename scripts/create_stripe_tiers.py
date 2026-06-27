"""Create Processor Assistant Stripe tiers.

Usage:
    $env:STRIPE_SECRET_KEY="<your Stripe secret key>"   # PowerShell; do not commit this
    python scripts/create_stripe_tiers.py

The script creates/reuses monthly recurring Stripe Prices for the app tiers and
prints the environment variables Processor Assistant needs. It does not store
or print your Stripe secret key.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tiers  # noqa: E402


API_BASE = "https://api.stripe.com/v1"
CURRENCY = "usd"


DESCRIPTIONS = {
    "starter": "75 document scans per month.",
    "pro": "250 document scans per month.",
    "unlimited": "Unlimited document scans plus priority support.",
}


def _secret_key() -> str:
    key = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not key:
        raise SystemExit("STRIPE_SECRET_KEY is not set. Set it locally, then run this script again.")
    if not key.startswith(("sk_test_", "sk_live_")):
        raise SystemExit("STRIPE_SECRET_KEY does not look like a Stripe secret key.")
    return key


def _request(method: str, path: str, data: dict[str, object] | None = None) -> dict:
    key = _secret_key()
    url = f"{API_BASE}{path}"
    body = None
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{key}:".encode("utf-8")).decode("ascii"),
        "Stripe-Version": "2025-05-28.basil",
    }
    if data is not None:
        body = urllib.parse.urlencode(data, doseq=True).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Stripe API error {exc.code} for {path}:\n{detail}") from exc


def _get_price_by_lookup_key(lookup_key: str) -> dict | None:
    query = urllib.parse.urlencode({"lookup_keys[]": lookup_key, "active": "true", "limit": 1})
    result = _request("GET", f"/prices?{query}")
    rows = result.get("data") or []
    return rows[0] if rows else None


def _create_product(tier_key: str, tier: dict) -> dict:
    limit = tier["scan_limit"]
    limit_label = "Unlimited scans" if limit is None else f"{limit} scans/month"
    return _request(
        "POST",
        "/products",
        {
            "name": f"Processor Assistant {tier['name']}",
            "description": DESCRIPTIONS.get(tier_key, limit_label),
            "metadata[app]": "processor_assistant",
            "metadata[tier]": tier_key,
            "metadata[scan_limit]": "unlimited" if limit is None else str(limit),
        },
    )


def _create_or_reuse_price(tier_key: str, tier: dict) -> dict:
    lookup_key = f"processor_assistant_{tier_key}_monthly"
    existing = _get_price_by_lookup_key(lookup_key)
    if existing:
        return existing

    product = _create_product(tier_key, tier)
    unit_amount = int(round(float(tier["price"]) * 100))
    return _request(
        "POST",
        "/prices",
        {
            "product": product["id"],
            "currency": CURRENCY,
            "unit_amount": unit_amount,
            "recurring[interval]": "month",
            "lookup_key": lookup_key,
            "nickname": f"{tier['name']} monthly",
            "metadata[app]": "processor_assistant",
            "metadata[tier]": tier_key,
        },
    )


def _create_payment_link(tier_key: str, price_id: str) -> dict:
    return _request(
        "POST",
        "/payment_links",
        {
            "line_items[0][price]": price_id,
            "line_items[0][quantity]": 1,
            "metadata[app]": "processor_assistant",
            "metadata[tier]": tier_key,
            "subscription_data[metadata][app]": "processor_assistant",
            "subscription_data[metadata][tier]": tier_key,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Stripe Products/Prices/Payment Links for Processor Assistant tiers.")
    parser.add_argument("--no-payment-links", action="store_true", help="Only create/reuse Products and Prices.")
    parser.add_argument("--write-env", metavar="PATH", help="Also write the resulting non-secret env vars to this file.")
    args = parser.parse_args()

    output: dict[str, str] = {}
    for tier_key in ("starter", "pro", "unlimited"):
        tier = tiers.TIERS[tier_key]
        price = _create_or_reuse_price(tier_key, tier)
        price_id = str(price["id"])
        output[f"TIER_{tier_key.upper()}_PRICE_ID"] = price_id
        if not args.no_payment_links:
            link = _create_payment_link(tier_key, price_id)
            output[f"TIER_{tier_key.upper()}_PAYMENT_LINK"] = str(link["url"])

    lines = [f"{key}={value}" for key, value in output.items()]
    print("\n".join(lines))
    if args.write_env:
        Path(args.write_env).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote non-secret env vars to {args.write_env}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
