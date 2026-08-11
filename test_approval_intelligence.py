import unittest

import approval_intelligence as intelligence


class ApprovalIntelligenceTests(unittest.TestCase):
    def test_detects_known_lender_without_retaining_document(self):
        text = "Borrower: Jane Doe\nLoan: 99887766\nUNITED WHOLESALE MORTGAGE\nApproval"
        self.assertEqual(intelligence.detect_lender_name(text), "United Wholesale Mortgage")

    def test_three_way_classification_and_ambiguity(self):
        borrower = intelligence.classify_condition("Borrower must provide updated paystubs and statements")
        lender = intelligence.classify_condition("Underwriter to verify employment and review VOE")
        broker = intelligence.classify_condition("Broker company licensing and good standing compliance")
        ambiguous = intelligence.classify_condition("Updated documentation required")
        self.assertEqual(borrower["owner"], "Borrower")
        self.assertEqual(lender["owner"], "Lender")
        self.assertEqual(broker["owner"], "Broker / Loan Officer")
        self.assertFalse(borrower["needs_confirmation"])
        self.assertTrue(ambiguous["needs_confirmation"])

    def test_correction_stores_only_allowlisted_features(self):
        state, _ = intelligence.record_confirmation(
            intelligence.empty_state(), "UWM",
            intelligence.pattern_features("Jane Doe at 123 Main Street: company good standing"),
            "Borrower", "Broker / Loan Officer",
        )
        serialized = str(state)
        self.assertNotIn("Jane", serialized)
        self.assertNotIn("Main Street", serialized)
        self.assertIn("company", serialized)
        self.assertIn("standing", serialized)
        learned = intelligence.classify_condition("company remains in good standing", state)
        self.assertEqual(learned["owner"], "Broker / Loan Officer")

    def test_lender_summary_uses_confirmed_feedback_when_available(self):
        rows = intelligence.apply_ownership([
            {"desc": "Borrower must provide updated paystubs and statements"},
            {"desc": "Updated documentation required"},
        ])
        state, estimated = intelligence.record_scan(intelligence.empty_state(), "UWM", rows)
        self.assertEqual(estimated["basis"], "estimated")
        state, confirmed = intelligence.record_confirmation(
            state, "UWM", rows[1]["ownership_pattern_features"],
            rows[1]["ownership_bucket"], "Lender",
        )
        self.assertEqual(confirmed["basis"], "processor-confirmed")
        self.assertEqual(confirmed["accuracy_percent"], 0)


if __name__ == "__main__":
    unittest.main()
