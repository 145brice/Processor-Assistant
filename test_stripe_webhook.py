import hashlib
import hmac
import json
import os
import sys
import time
import types
import unittest


import stripe_webhook
import tiers


class StripeWebhookTierTests(unittest.TestCase):
    def _signed_payload(self, event: dict) -> tuple[bytes, str]:
        secret = "whsec_test_secret"
        os.environ["STRIPE_WEBHOOK_SECRET"] = secret
        payload = json.dumps(event, separators=(",", ":")).encode("utf-8")
        ts = str(int(time.time()))
        sig = hmac.new(secret.encode("utf-8"), ts.encode("utf-8") + b"." + payload, hashlib.sha256).hexdigest()
        return payload, f"t={ts},v1={sig}"

    def test_amount_fallback_maps_checkout_to_pro_without_price_id(self):
        calls = []
        fake_supabase = types.SimpleNamespace(
            update_subscription_by_email=lambda *args, **kwargs: calls.append((args, kwargs)) or {"ok": True, "updated": 1}
        )
        old_supabase = sys.modules.get("supabase_auth")
        sys.modules["supabase_auth"] = fake_supabase
        try:
            payload, signature = self._signed_payload(
                {
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "customer_details": {"email": "buyer@example.com"},
                            "customer": "cus_test",
                            "subscription": "sub_test",
                            "amount_total": 2999,
                        }
                    },
                }
            )
            code, result = stripe_webhook.handle_stripe_webhook(payload, signature)
        finally:
            if old_supabase is None:
                sys.modules.pop("supabase_auth", None)
            else:
                sys.modules["supabase_auth"] = old_supabase

        self.assertEqual(code, 200)
        self.assertTrue(result["ok"])
        self.assertEqual(calls[0][1]["tier"], "pro")
        self.assertEqual(calls[0][1]["plan"], "pro")

    def test_current_tier_amounts_map_without_price_ids(self):
        self.assertEqual(tiers.tier_for_amount_cents(999), "starter")
        self.assertEqual(tiers.tier_for_amount_cents(2999), "pro")
        self.assertEqual(tiers.tier_for_amount_cents(4999), "unlimited")


if __name__ == "__main__":
    unittest.main()
