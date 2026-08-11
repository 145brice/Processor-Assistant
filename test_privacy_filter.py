import unittest
from unittest.mock import patch
import json

import cloud_client
from privacy_filter import (
    find_sensitive_fragments,
    redact_for_cloud,
    redact_for_cloud_resilient,
    redact_gemini_output,
    secure_approval_system_prompt,
)


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
    def test_resilient_redaction_keeps_safe_text_and_quarantines_residual_line(self):
        with patch("privacy_filter.redact_for_cloud") as initial:
            initial.return_value = (
                "Safe approval heading\nBorrower - Jane Marie Doe\nPTF Conditions",
                {},
                ["labeled_name"],
            )
            sanitized, _, forced, remaining = redact_for_cloud_resilient("source")
        self.assertFalse(remaining)
        self.assertIn("labeled_name", forced)
        self.assertNotIn("Jane Marie Doe", sanitized)
        self.assertIn("Safe approval heading", sanitized)
        self.assertIn("PTF Conditions", sanitized)

    def test_resilient_redaction_handles_cascading_labeled_names(self):
        source = (
            "Borrower - Jane Marie Doe Please Provide Updated Statements "
            "Borrower - James Smith Please Sign Tax Returns"
        )
        sanitized, _, forced, remaining = redact_for_cloud_resilient(source)
        self.assertFalse(remaining)
        self.assertIn("labeled_name", forced)
        self.assertNotIn("Jane Marie Doe", sanitized)
        self.assertNotIn("James Smith", sanitized)

    def test_secure_approval_prompt_requires_deidentified_private_learning(self):
        prompt = secure_approval_system_prompt("Extract conditions.")
        self.assertIn("only after", prompt)
        self.assertIn("locally removed borrower-sensitive data", prompt)
        self.assertIn("private to the uploading processor", prompt)
        self.assertIn("Borrower, Lender, or Broker / Loan Officer", prompt)
        self.assertIn("never retain the original condition", prompt)

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

    def test_redaction_covers_ein_and_government_ids(self):
        source = "EIN: 12-3456789\nDriver's License Number: D123456789"
        sanitized, _, leaks = redact_for_cloud(source)
        self.assertFalse(leaks)
        self.assertNotIn("12-3456789", sanitized)
        self.assertNotIn("D123456789", sanitized)

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

    def test_gemini_condition_output_does_not_restore_sensitive_values(self):
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

        self.assertNotIn("WEDS 517655504100", result)
        self.assertFalse(find_sensitive_fragments(result))

    def test_gemini_transport_includes_instruction_and_redacts_response(self):
        captured = {}

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                body = {
                    "candidates": [{
                        "content": {
                            "parts": [{
                                "text": (
                                    "Jane Marie Doe at 123 Main Street can be reached "
                                    "at (312) 555-0199. SSN 123-45-6789."
                                )
                            }]
                        }
                    }]
                }
                return json.dumps(body).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return FakeResponse()

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            output = cloud_client._generate_gemini(
                "Borrower Name: Jane Marie Doe\nProperty Address: 123 Main Street",
                "Rewrite the loan condition.",
                "gemini-test",
                "test-key",
                30,
            )

        sent_text = captured["payload"]["contents"][0]["parts"][0]["text"]
        self.assertIn("MANDATORY RESPONSE PRIVACY RULE", sent_text)
        self.assertNotIn("Jane Marie Doe", output)
        self.assertNotIn("123 Main Street", output)
        self.assertNotIn("(312) 555-0199", output)
        self.assertNotIn("123-45-6789", output)
        self.assertFalse(find_sensitive_fragments(output))

    def test_output_redactor_removes_sensitive_values_from_response(self):
        output = redact_gemini_output(
            "Contact Jane Marie Doe at jane@example.com or (312) 555-0199. "
            "SSN: 123-45-6789. Address: 123 Main Street, Chicago, IL 60601.",
            source_text=SENSITIVE_TEXT,
        )
        for sensitive in (
            "Jane Marie Doe",
            "jane@example.com",
            "(312) 555-0199",
            "123-45-6789",
            "123 Main Street",
        ):
            self.assertNotIn(sensitive, output)
        self.assertFalse(find_sensitive_fragments(output))

    def test_gemini_translation_fallback_is_also_redacted(self):
        descriptions = [
            "Jane Marie Doe must provide documents for 123 Main Street. "
            "Call (312) 555-0199."
        ]

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps({
                    "candidates": [{"content": {"parts": [{"text": "[]"}]}}]
                }).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            output, _ = cloud_client.translate_conditions_to_plain(
                descriptions,
                api_key_override="test-key",
            )

        self.assertEqual(len(output), 1)
        self.assertNotIn("Jane Marie Doe", output[0])
        self.assertNotIn("123 Main Street", output[0])
        self.assertNotIn("(312) 555-0199", output[0])
        self.assertFalse(find_sensitive_fragments(output[0]))

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

    def test_approval_pdf_defaults_to_local_redacted_path(self):
        local_text = (
            "Borrower Name: Jane Marie Doe\nSSN: 123-45-6789\n"
            "1. Borrower must provide updated paystubs."
        )
        local_rows = "| 1 | Borrower must provide updated paystubs | Borrower | Needed |"
        with (
            patch.dict("os.environ", {}, clear=False),
            patch("ai_engine.extract_text_from_pdf", return_value=local_text),
            patch("ai_engine.extract_conditions", return_value=local_rows),
            patch.object(cloud_client, "enhance_conditions", return_value=(local_rows, "[LOCAL]")) as enhance,
            patch("urllib.request.urlopen") as urlopen,
        ):
            with patch.dict("os.environ", {"PA_PDF_VISION": ""}):
                result, _, _ = cloud_client.extract_approval_conditions_ai_from_pdf(b"%PDF-private")

        self.assertIn("updated paystubs", result)
        enhance.assert_called_once()
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
