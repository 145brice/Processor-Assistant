"""Party emails use recipient-appropriate wording."""
import unittest
import sys
import types

sys.modules.setdefault("pypdf", types.SimpleNamespace(PdfReader=object))
from ai_engine import condition_for_email_language, draft_email


class PartyEmailTemplateTests(unittest.TestCase):
    def test_every_approval_section_has_its_own_email_language(self):
        expected_phrases = {
            "Borrower": "your mortgage loan processor",
            "Title": "Dear Title Team",
            "Insurance": "Dear Insurance Agent",
            "Appraiser": "Dear Appraiser",
            "Employer": "from the employer",
            "Realtor": "your buyer's loan file",
            "Seller": "from the seller",
            "Closer": "Dear Closer",
            "Processor": "processing items remain outstanding",
            "Underwriter": "Dear Underwriter",
        }
        for party, phrase in expected_phrases.items():
            with self.subTest(party=party):
                draft = draft_email("- #1: Test condition", party, "English")
                self.assertIn(phrase, draft)
                self.assertIn("- #1: Test condition", draft)

    def test_spanish_selection_localizes_condition_lines(self):
        translated = condition_for_email_language(
            "Provide the most recent complete bank statement", "Spanish"
        )
        self.assertIn("estado de cuenta bancario", translated)
        self.assertNotIn("bank statement", translated.lower())

    def test_unknown_spanish_condition_does_not_leak_english(self):
        translated = condition_for_email_language(
            "Unmapped proprietary lender wording", "Spanish"
        )
        self.assertEqual(
            translated,
            "Proporcione la documentación solicitada para completar esta condición del préstamo.",
        )


if __name__ == "__main__":
    unittest.main()
