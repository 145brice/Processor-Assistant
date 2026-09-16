import json
import os
import unittest
from unittest.mock import patch

import email_service


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return b'{"id":"email_test"}'


class EmailServiceTests(unittest.TestCase):
    def test_resend_request_uses_edge_landings_sender_and_idempotency(self):
        env = {
            "RESEND_API_KEY": "re_test",
            "RESEND_FROM": "Edge Landings <alerts@edgelandings.com>",
        }
        with patch.dict(os.environ, env, clear=False), patch(
            "urllib.request.urlopen", return_value=_Response()
        ) as open_request:
            result = email_service.send_email(
                "customer@example.com", "Welcome", "Hello", "signup-123"
            )

        self.assertTrue(result["ok"])
        request = open_request.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(payload["from"], env["RESEND_FROM"])
        self.assertEqual(payload["to"], ["customer@example.com"])
        self.assertEqual(request.get_header("Idempotency-key"), "signup-123")

    def test_unconfigured_email_is_safely_skipped(self):
        with patch.dict(os.environ, {"RESEND_API_KEY": "", "RESEND_FROM": ""}):
            result = email_service.send_email("customer@example.com", "Hi", "Body", "key")
        self.assertFalse(result["ok"])
        self.assertTrue(result["skipped"])


if __name__ == "__main__":
    unittest.main()
