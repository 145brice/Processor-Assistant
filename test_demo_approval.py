"""Keep the recording PDF compatible with the live approval scanner."""

import tempfile
import unittest
from pathlib import Path

import ai_engine
from scripts.make_demo_approval import make_pdf


class DemoApprovalTests(unittest.TestCase):
    def test_generated_pdf_is_detected_and_all_conditions_are_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = make_pdf(Path(directory) / "approval.pdf", seed=2)
            data = pdf.read_bytes()

        self.assertEqual(ai_engine.detect_doc_type(data)["doc_type"], "Approval Letter")
        text = ai_engine.extract_text_from_pdf(data)
        conditions = ai_engine.extract_conditions(text, "Approval Letter")
        self.assertIn("DEMO-LOAN-00002", text)
        self.assertIn("FICTIONAL LENDER", text)
        self.assertIn("12 condition(s) extracted", conditions)
        self.assertIn("Funding Review", conditions)


if __name__ == "__main__":
    unittest.main()
