import urllib.parse
import unittest
from unittest import mock

import supabase_auth


class SupabaseGoogleOAuthTests(unittest.TestCase):
    def test_auth_user_listing_uses_service_role_and_paginates(self):
        first_page = {"ok": True, "data": {"users": [{"id": str(i)} for i in range(1000)]}}
        second_page = {"ok": True, "data": {"users": [{"id": "last"}]}}
        with mock.patch.object(supabase_auth, "_service_key", return_value="service-key"), \
             mock.patch.object(supabase_auth, "_supabase_url", return_value="https://project.supabase.co"), \
             mock.patch.object(supabase_auth, "_json_request", side_effect=[first_page, second_page]) as request:
            users, result = supabase_auth._list_auth_users()

        self.assertTrue(result["ok"])
        self.assertEqual(len(users), 1001)
        self.assertIn("page=2", request.call_args_list[1].args[1])
        self.assertEqual(request.call_args_list[0].kwargs["bearer"], "service-key")

    def test_browser_pkce_state_survives_session_replacement(self):
        supabase_auth.cache_browser_oauth("browser-key", "flow-id", "verifier")
        self.assertEqual(
            supabase_auth.get_cached_browser_oauth("browser-key"),
            ("flow-id", "verifier"),
        )
        supabase_auth.clear_cached_browser_oauth("browser-key")
        self.assertEqual(supabase_auth.get_cached_browser_oauth("browser-key"), ("", ""))

    def test_flow_verifier_wins_over_stale_session_verifier(self):
        verifier = supabase_auth.select_oauth_verifier(
            flow_verifier="verifier-for-clicked-link",
            callback_verifier="verifier-from-callback",
            session_verifier="newer-rerun-verifier",
        )
        self.assertEqual(verifier, "verifier-for-clicked-link")

    def test_callback_verifier_wins_when_server_cache_is_missing(self):
        verifier = supabase_auth.select_oauth_verifier(
            callback_verifier="verifier-from-callback",
            session_verifier="newer-rerun-verifier",
        )
        self.assertEqual(verifier, "verifier-from-callback")

    def test_google_oauth_requests_account_chooser(self):
        env = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_ANON_KEY": "test-anon-key",
            "PA_APP_URL": "https://processor.example.com",
        }
        with mock.patch.dict("os.environ", env, clear=True), \
             mock.patch.object(supabase_auth, "save_pending_google_oauth", return_value={"ok": True}):
            result = supabase_auth.begin_google_oauth(flow_id="test-flow-id")

        self.assertTrue(result["ok"])
        query = urllib.parse.parse_qs(urllib.parse.urlparse(result["url"]).query)
        self.assertEqual(query["provider"], ["google"])
        self.assertEqual(query["prompt"], ["select_account"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(
            query["redirect_to"],
            ["https://processor.example.com/?pa_oauth_flow=test-flow-id"],
        )

    def test_google_oauth_can_reuse_server_side_pkce_state(self):
        env = {
            "SUPABASE_URL": "https://project.supabase.co",
            "SUPABASE_ANON_KEY": "test-anon-key",
            "PA_APP_URL": "https://processor.example.com",
        }
        with mock.patch.dict("os.environ", env, clear=True), \
             mock.patch.object(supabase_auth, "save_pending_google_oauth", return_value={"ok": True}):
            result = supabase_auth.begin_google_oauth(
                flow_id="existing-flow",
                verifier="existing-verifier",
            )

        query = urllib.parse.parse_qs(urllib.parse.urlparse(result["url"]).query)
        self.assertEqual(result["flow_id"], "existing-flow")
        self.assertEqual(result["verifier"], "existing-verifier")
        self.assertEqual(
            query["code_challenge"],
            [supabase_auth._pkce_challenge("existing-verifier")],
        )

    def test_pending_verifier_is_encrypted_and_restored_by_flow_id(self):
        with mock.patch.object(supabase_auth, "_encrypt_secret", return_value="encrypted"), \
             mock.patch.object(supabase_auth, "_save_setting_json", return_value={"ok": True}) as save:
            result = supabase_auth.save_pending_google_oauth("flow-id", "plain-verifier")
        self.assertTrue(result["ok"])
        self.assertEqual(save.call_args.args[0], "oauth_pkce:flow-id")
        self.assertEqual(save.call_args.args[1]["verifier_enc"], "encrypted")
        self.assertNotIn("plain-verifier", str(save.call_args.args[1]))

        future = (supabase_auth.datetime.now(supabase_auth.timezone.utc) + supabase_auth.timedelta(minutes=5)).isoformat()
        with mock.patch.object(
            supabase_auth,
            "_load_setting_json",
            return_value={"verifier_enc": "encrypted", "expires_at": future},
        ), mock.patch.object(supabase_auth, "_decrypt_secret", return_value="plain-verifier"):
            self.assertEqual(supabase_auth.load_pending_google_oauth("flow-id"), "plain-verifier")

    def test_pending_verifier_can_be_restored_from_browser_hint(self):
        rows = [
            {
                "key": "oauth_pkce:matching-flow",
                "value_json": {"browser_hints": ["browser-hash"], "verifier_enc": "encrypted"},
            }
        ]
        with mock.patch.object(supabase_auth, "_service_key", return_value="service-key"), \
             mock.patch.object(supabase_auth, "_supabase_url", return_value="https://project.supabase.co"), \
             mock.patch.object(supabase_auth, "_json_request", return_value={"ok": True, "data": rows}), \
             mock.patch.object(supabase_auth, "load_pending_google_oauth", return_value="verifier"):
            flow_id, verifier = supabase_auth.load_pending_google_oauth_for_browser(["browser-hash"])

        self.assertEqual(flow_id, "matching-flow")
        self.assertEqual(verifier, "verifier")


if __name__ == "__main__":
    unittest.main()
