import json
import os
import unittest
from unittest import mock

import supabase_auth
import tiers


def _row(user_key, email, started_at, **extra):
    profile = {
        "user_key": user_key,
        "email": email,
        "trial_started_at": started_at,
        "subscription_status": "trialing",
        "plan": "free",
        **extra,
    }
    return {
        "key": f"user_profile:{user_key}",
        "user_key": user_key,
        "user_email": email,
        "value_json": json.dumps(profile),
        "updated_at": started_at,
    }


class BetaCohortTests(unittest.TestCase):
    def setUp(self):
        supabase_auth._free_beta_cohort_full = False

    def test_first_ten_non_owner_profiles_receive_free_beta(self):
        rows = [
            _row("owner", "145brice@gmail.com", "2025-01-01T00:00:00+00:00"),
            *[
                _row(f"user-{i}", f"user{i}@example.com", f"2025-01-{i + 1:02d}T00:00:00+00:00")
                for i in range(1, 12)
            ],
        ]
        saved = []

        def save(key, value, **kwargs):
            saved.append((key, value.copy()))
            return {"ok": True}

        with mock.patch.object(supabase_auth, "_list_user_profile_rows", return_value=(rows, {"ok": True})), \
             mock.patch.object(supabase_auth, "_save_setting_json", side_effect=save), \
             mock.patch.dict(os.environ, {"PA_OWNER_ADMIN_EMAILS": "145brice@gmail.com"}):
            result = supabase_auth.grant_free_beta_users(10)

        self.assertTrue(result["ok"])
        self.assertEqual(result["total"], 10)
        self.assertEqual(len(saved), 10)
        self.assertNotIn("user_profile:owner", {key for key, _ in saved})
        self.assertNotIn("user_profile:user-11", {key for key, _ in saved})
        self.assertEqual([profile["beta_slot"] for _, profile in saved], list(range(1, 11)))
        self.assertTrue(all(profile["tier"] == "unlimited" for _, profile in saved))

    def test_existing_beta_slots_are_preserved(self):
        rows = [
            _row("existing", "existing@example.com", "2025-01-02T00:00:00+00:00", beta_free=True, beta_slot=1),
            _row("next", "next@example.com", "2025-01-03T00:00:00+00:00"),
        ]
        saved = []
        with mock.patch.object(supabase_auth, "_list_user_profile_rows", return_value=(rows, {"ok": True})), \
             mock.patch.object(supabase_auth, "_save_setting_json", side_effect=lambda key, value, **kwargs: saved.append((key, value)) or {"ok": True}):
            result = supabase_auth.grant_free_beta_users(2)

        self.assertEqual(result["granted"], 1)
        self.assertEqual(saved[0][0], "user_profile:next")
        self.assertEqual(saved[0][1]["beta_slot"], 2)

    def test_beta_tier_is_unlimited_and_labeled_free(self):
        profile = {"beta_free": True, "subscription_status": "beta_active", "tier": "unlimited"}
        with mock.patch("billing.get_usage", return_value={"scans": 999}):
            quota = tiers.check_scan_quota("user-1", profile)
        self.assertEqual(quota["tier"], "unlimited")
        self.assertEqual(quota["tier_name"], "Beta — Free")
        self.assertIsNone(quota["limit"])
        self.assertTrue(quota["allowed"])

    def test_legacy_beta_plan_without_entitlement_is_free(self):
        self.assertEqual(tiers.tier_for_profile({"plan": "beta", "subscription_status": "trialing"}), "free")


if __name__ == "__main__":
    unittest.main()
