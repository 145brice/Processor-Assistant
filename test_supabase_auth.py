import urllib.parse
import unittest
from unittest import mock

import supabase_auth


class SupabaseGoogleOAuthTests(unittest.TestCase):
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
        with mock.patch.dict("os.environ", env, clear=True):
            result = supabase_auth.begin_google_oauth()

        self.assertTrue(result["ok"])
        query = urllib.parse.parse_qs(urllib.parse.urlparse(result["url"]).query)
        self.assertEqual(query["provider"], ["google"])
        self.assertEqual(query["prompt"], ["select_account"])
        self.assertEqual(query["code_challenge_method"], ["S256"])


if __name__ == "__main__":
    unittest.main()
