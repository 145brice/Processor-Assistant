import unittest

import cloud_client


class CloudPlaceholderCleanupTests(unittest.TestCase):
    def test_approval_rows_neutralize_redaction_placeholders_before_display(self):
        raw = (
            "| 1 | Payoff - Provide proof [KNOWN_VALUE_82] has been paid from [ACCOUNT_NUMBER_1]. | Borrower | Needed | High Confidence |\n"
            "| 2 | Employment - Explain salary change dated [EXACT_DATE_1] and income [INCOME_AMOUNT]. | Borrower | Needed | High Confidence |"
        )

        cleaned = cloud_client._neutralize_placeholders(raw)
        rows = cloud_client._parse_approval_condition_rows(cleaned)
        rendered = "\n".join(rows)

        self.assertNotIn("[KNOWN_VALUE", rendered)
        self.assertNotIn("[ACCOUNT_NUMBER", rendered)
        self.assertNotIn("[EXACT_DATE", rendered)
        self.assertIn("the provided detail", rendered)
        self.assertIn("the account number", rendered)
        self.assertIn("the date", rendered)


if __name__ == "__main__":
    unittest.main()
