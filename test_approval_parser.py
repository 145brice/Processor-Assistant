import unittest

import ai_engine


APPROVAL_WITH_NUMERIC_CODES = """
LOAN APPROVAL CONDITIONS
3365-4-4-51 Income Documentation Provide the most recent paystub covering 30 days.
3365-4-4-52 Asset Documentation Provide the most recent two months bank statements.
3365-4-4-53 Homeowners Insurance Provide evidence of acceptable hazard insurance.
3365-4-4-54 Appraisal Provide a final appraisal showing all repairs completed.
3365-4-4-55 Title Commitment Provide a clear title commitment with all liens addressed.
3365-4-4-56 Earnest Money Provide evidence the earnest money deposit cleared.
3365-4-4-57 Employment Complete a verbal verification of employment before closing.
3365-4-4-58 Closing Disclosure Provide the final closing disclosure for review.
3365-4-4-59 Debts to be paid directly from proceeds: Account Number 42051917169 Amount $331.00
3365-4-4-60 Tax Returns Provide complete signed federal tax returns for the last two years.
3365-4-4-61 Letter of Explanation Provide a signed letter explaining the recent inquiry.
3365-4-4-62 Government ID Provide a clear copy of an unexpired government-issued ID.
"""


class ApprovalParserTests(unittest.TestCase):
    def test_numeric_lender_codes_extract_all_conditions(self):
        result = ai_engine.extract_conditions(
            APPROVAL_WITH_NUMERIC_CODES,
            "Approval Letter",
        )
        rows = [
            line for line in result.splitlines()
            if line.strip().startswith("|") and line.strip()[1:].lstrip()[:1].isdigit()
        ]

        self.assertEqual(len(rows), 12)
        self.assertIn("Debts to be paid directly", result)
        self.assertIn("Government ID", result)
        self.assertNotIn("Each row above", "\n".join(rows))


if __name__ == "__main__":
    unittest.main()

