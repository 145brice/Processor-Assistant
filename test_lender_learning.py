import unittest

from lender_learning import build_profile_from_sanitized, empty_state, normalize_state, record_profile


class LenderLearningTests(unittest.TestCase):
    def test_profile_keeps_structure_not_sentences(self):
        text = """Approval Conditions
Condition Number | Description | Status
1. [BORROWER_1] must provide [ACCOUNT_NUMBER_1]
PTF Conditions
"""
        profile = build_profile_from_sanitized("UWM", text, page_count=2, image_based=False)
        encoded = str(profile)
        self.assertNotIn("must provide", encoded)
        self.assertNotIn("ACCOUNT_NUMBER_1]", encoded)
        self.assertIn("approval conditions", profile["features"]["headings"])
        self.assertIn("integer", profile["features"]["numbering_styles"])
        self.assertIn("ptf", profile["features"]["group_codes"])

    def test_state_aggregates_same_format(self):
        profile = build_profile_from_sanitized("Rocket Mortgage", "Conditions\n1. [PERSON_1]", page_count=1, image_based=False)
        state = record_profile(empty_state(), profile)
        state = record_profile(state, profile)
        lender = next(iter(state["lenders"].values()))
        self.assertEqual(lender["total_samples"], 2)
        self.assertEqual(next(iter(lender["formats"].values()))["samples"], 2)

    def test_normalizer_drops_raw_fields(self):
        dirty = {
            "version": 1,
            "lenders": {
                "uwm": {
                    "name": "UWM",
                    "total_samples": 1,
                    "raw_text": "Borrower SSN 123-45-6789",
                    "formats": {},
                }
            },
        }
        cleaned = normalize_state(dirty)
        self.assertNotIn("raw_text", str(cleaned))
        self.assertNotIn("123-45-6789", str(cleaned))


if __name__ == "__main__":
    unittest.main()
