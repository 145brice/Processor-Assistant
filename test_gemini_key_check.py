"""check_gemini_key turns Google's replies into plain reasons. No real API calls."""
import io
import unittest
import urllib.error
from unittest.mock import patch

import cloud_client

FAKE_KEY = "AIzaFAKE-test-key-not-real"


def _http_error(code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid", code, "error", {}, io.BytesIO(body.encode()))


class CheckGeminiKeyTests(unittest.TestCase):
    def check(self, side_effect=None, return_value="OK", key=FAKE_KEY):
        with patch.object(cloud_client, "_generate_gemini", side_effect=side_effect, return_value=return_value) as gen:
            result = cloud_client.check_gemini_key(key)
        return result, gen

    def test_working_key(self):
        (ok, msg), gen = self.check()
        self.assertTrue(ok)
        self.assertIn("works", msg)
        gen.assert_called_once()

    def test_empty_and_wrong_format_never_call_google(self):
        for key in ("", "   ", "sk-not-a-gemini-key"):
            (ok, _), gen = self.check(key=key)
            self.assertFalse(ok)
            gen.assert_not_called()

    def test_invalid_key(self):
        (ok, msg), _ = self.check(side_effect=_http_error(400, '{"error":{"message":"API key not valid. Please pass a valid API key."}}'))
        self.assertFalse(ok)
        self.assertIn("isn't valid", msg)

    def test_permission_or_api_disabled(self):
        (ok, msg), _ = self.check(side_effect=_http_error(403, '{"error":{"status":"PERMISSION_DENIED"}}'))
        self.assertFalse(ok)
        self.assertIn("billing turned on", msg)

    def test_no_paid_usage(self):
        (ok, msg), _ = self.check(side_effect=_http_error(429, '{"error":{"message":"Quota exceeded. Check your plan and billing details."}}'))
        self.assertFalse(ok)
        self.assertIn("no paid usage", msg)

    def test_plain_rate_limit(self):
        (ok, msg), _ = self.check(side_effect=_http_error(429, '{"error":{"message":"Too many requests"}}'))
        self.assertFalse(ok)
        self.assertIn("Wait a minute", msg)

    def test_network_problem(self):
        (ok, msg), _ = self.check(side_effect=urllib.error.URLError("no route"))
        self.assertFalse(ok)
        self.assertIn("Couldn't reach Google", msg)

    def test_message_never_contains_the_key(self):
        for effect in (None, _http_error(400, "API key not valid " + FAKE_KEY), urllib.error.URLError("x")):
            (_, msg), _ = self.check(side_effect=effect)
            self.assertNotIn(FAKE_KEY, msg)


if __name__ == "__main__":
    unittest.main()
