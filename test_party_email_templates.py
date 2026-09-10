"""Party emails use recipient-appropriate wording."""
import unittest
import sys
import types

sys.modules.setdefault("pypdf", types.SimpleNamespace(PdfReader=object))
from ai_engine import draft_email


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


if __name__ == "__main__":
    unittest.main()
