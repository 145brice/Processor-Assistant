import unittest
from unittest.mock import patch

import cloud_client
from privacy_filter import find_sensitive_fragments, redact_for_cloud


SENSITIVE_TEXT = """
Borrower Name: Jane Marie Doe
Seller: Robert Smith
SSN: 123-45-6789
DOB: 01/02/1980
Email: jane.doe@example.com
Phone: (312) 555-0199
Account Number: 9988776655
Property Address: 123 Main Street, Chicago, IL 60601
Monthly Income: $12,500.00
Closing Date: 07/31/2026
Condition: Borrower must provide an updated homeowners insurance declaration.
"""


class PrivacyFilterTests(unittest.TestCase):
    def test_redaction_removes_sensitive_values(self):
        sanitized, replacements, leaks = redact_for_cloud(SENSITIVE_TEXT)

        self.assertFalse(leaks)
        self.assertFalse(find_sensitive_fragments(sanitized))
        self.assertNotIn("Jane Marie Doe", sanitized)
        self.assertNotIn("Robert Smith", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertNotIn("123 Main Street", sanitized)
        self.assertNotIn("12,500", sanitized)
        self.assertTrue(replacements)
        self.assertIn("homeowners insurance", sanitized)

    def test_purchase_contract_cloud_call_receives_only_sanitized_text(self):
        captured = {}

        def fake_generate(prompt, system, provider, api_key, model):
            captured["prompt"] = prompt
            return '{"contingencies":{"inspection":"10 days","appraisal":"","financing":""},"addendums":[],"special_conditions":[]}'

        with (
            patch.object(
                cloud_client,
                "get_config",
                return_value={
                    "enabled": True,
                    "provider": "gemini",
                    "api_key": "test",
                    "model": "test-model",
                },
            ),
            patch.object(cloud_client, "_generate", side_effect=fake_generate),
            patch.object(cloud_client, "_log", return_value="[TEST]"),
        ):
            data, _ = cloud_client.extract_purchase_contract_ai(SENSITIVE_TEXT)

        self.assertEqual(data["contingencies"]["inspection"], "10 days")
        prompt = captured["prompt"]
        self.assertFalse(find_sensitive_fragments(prompt))
        self.assertNotIn("Jane Marie Doe", prompt)
        self.assertNotIn("123 Main Street", prompt)

    def test_condition_enhancement_receives_sanitized_rows(self):
        captured = {}

        def fake_generate(prompt, system, provider, api_key, model):
            captured["prompt"] = prompt
            return "| 1 | Borrower must provide homeowners insurance | Borrower | Needed | High Confidence |"

        with (
            patch.object(
                cloud_client,
                "get_config",
                return_value={
                    "enabled": True,
                    "provider": "gemini",
                    "api_key": "test",
                    "model": "test-model",
                },
            ),
            patch.object(cloud_client, "_generate", side_effect=fake_generate),
            patch.object(cloud_client, "_log", return_value="[TEST]"),
        ):
            result, _ = cloud_client.enhance_conditions(
                SENSITIVE_TEXT,
                "Approval Letter",
                "| 1 | Jane Marie Doe must provide homeowners insurance | Borrower | Needed | High Confidence |",
            )

        self.assertIn("homeowners insurance", result)
        prompt = captured["prompt"]
        self.assertFalse(find_sensitive_fragments(prompt))
        self.assertNotIn("Jane Marie Doe", prompt)
        self.assertNotIn("123-45-6789", prompt)

    def test_condition_placeholders_are_restored_locally(self):
        def fake_generate(prompt, system, provider, api_key, model):
            self.assertNotIn("WEDS 517655504100", prompt)
            return "| 1 | Provide payoff for [KNOWN_VALUE_1] | Borrower | Needed | High Confidence |"

        with (
            patch.object(
                cloud_client,
                "get_config",
                return_value={
                    "enabled": True,
                    "provider": "gemini",
                    "api_key": "test",
                    "model": "test-model",
                },
            ),
            patch.object(cloud_client, "_generate", side_effect=fake_generate),
            patch.object(cloud_client, "_log", return_value="[TEST]"),
        ):
            result, _ = cloud_client.enhance_conditions(
                "| 1 | Provide payoff for WEDS 517655504100 | Borrower | Needed | High Confidence |",
                "Approval Letter",
                "| 1 | Provide payoff for WEDS 517655504100 | Borrower | Needed | High Confidence |",
                known_values=["WEDS 517655504100"],
            )

        self.assertIn("WEDS 517655504100", result)
        self.assertNotIn("[KNOWN_VALUE_", result)

    def test_pdf_compatibility_wrapper_never_uploads_pdf_bytes(self):
        local_data = {
            "transaction": {"purchase_price": "500000", "closing_date": "07/31/2026"},
            "contingencies": {"inspection": "10 days", "appraisal": "", "financing": ""},
            "addendums": [],
        }
        local_text = "readable local purchase contract text with enough content for local parsing only"
        with (
            patch("ai_engine.extract_text_from_pdf", return_value=local_text),
            patch("ai_engine.extract_purchase_contract", return_value=local_data),
            patch.object(cloud_client, "extract_purchase_contract_ai", return_value=({}, "[LOCAL]")),
            patch("urllib.request.urlopen") as urlopen,
        ):
            result, _, text = cloud_client.extract_purchase_contract_ai_from_pdf(b"%PDF-private")

        self.assertEqual(text, local_text)
        self.assertEqual(result["transaction"]["purchase_price"], "500000")
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
