import csv
import io
import json
import os
import unittest
from unittest.mock import patch

import fitz
import product_config
import scan_history_store
import scan_outputs


class ScanOutputTests(unittest.TestCase):
    def test_sample_and_outputs_are_offline(self):
        with patch("urllib.request.urlopen", side_effect=AssertionError("Network call")):
            batch = scan_outputs.load_sample()
            borrower, officer = scan_outputs.email_drafts(batch)
            self.assertIn("pay stubs", borrower)
            self.assertNotIn("title commitment", borrower)
            self.assertIn("title commitment", officer)
            self.assertIn("DEMO-1042", scan_outputs.summary_text(batch))
            pdf = fitz.open(stream=scan_outputs.pdf_bytes(batch), filetype="pdf")
            self.assertIn("DEMO-1042", pdf[0].get_text())
            rows = list(csv.reader(io.StringIO(scan_outputs.csv_bytes(batch).decode("utf-8-sig"))))
            self.assertIn(["Borrower", "Alex Morgan"], rows)

    def test_pdf_paginates_without_losing_conditions(self):
        batch = {"result": {"conditions": [{"desc": f"Condition {i} " + "words " * 25} for i in range(200)]}}
        with fitz.open(stream=scan_outputs.pdf_bytes(batch), filetype="pdf") as pdf:
            self.assertGreater(len(pdf), 1)
            self.assertIn("Condition 199", "".join(p.get_text() for p in pdf))

    def test_csv_handles_formulas_quotes_and_newlines(self):
        batch = {"result": {"borrower": '=HYPERLINK("bad")', "conditions": [{"desc": 'One, two\n"three"'}]}}
        rows = list(csv.reader(io.StringIO(scan_outputs.csv_bytes(batch).decode("utf-8-sig"))))
        self.assertIn(["Borrower", '\'=HYPERLINK("bad")'], rows)
        self.assertTrue(any('One, two\n"three"' in row[1] for row in rows))

    def test_cleared_conditions_are_not_requested(self):
        batch = {"result": {"conditions": [{"desc": "Already delivered", "party": "Borrower", "status": "Cleared"}]}}
        borrower, officer = scan_outputs.email_drafts(batch)
        self.assertNotIn("Already delivered", borrower)
        self.assertNotIn("Already delivered", officer)


class ConfigTests(unittest.TestCase):
    def test_tools_are_on_by_default_and_can_be_switched_off(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(product_config.advanced_tools_enabled())
            self.assertEqual(product_config.visible_page("fraud_detector"), "fraud_detector")
        with patch.dict(os.environ, {"PA_ENABLE_ADVANCED_TOOLS": "0"}):
            for page in ("fraud_detector", "rate_lock_monitor", "overview", "compliance_checker"):
                self.assertEqual(product_config.visible_page(page), "dashboard")
            self.assertEqual(product_config.visible_page("pipeline"), "pipeline")

    def test_beta_offer_uses_only_supplied_values(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertNotIn("[END DATE]", product_config.beta_offer())
        with patch.dict(os.environ, {"PA_BETA_END_DATE": "December 1, 2026", "PA_FOUNDER_SPOTS": "20", "PA_FOUNDER_MONTHLY_PRICE": "$19"}):
            self.assertEqual(product_config.beta_offer(), "Free beta access until December 1, 2026 in exchange for feedback. The first 20 beta users lock in a founder price of $19/month after launch.")


class HistoryTests(unittest.TestCase):
    @patch("supabase_auth._supabase_url", return_value="https://example.supabase.co")
    @patch("supabase_auth._service_key", return_value="test-only")
    @patch("supabase_auth._json_request")
    def test_load_filters_accounts_and_reports_network_failure(self, request, *_):
        request.return_value = {"ok": True, "data": [{"value_json": json.dumps({"items": [
            {"id": "mine", "user_key": "a", "ts": 1}, {"id": "other", "user_key": "b"}]})}]}
        self.assertEqual(scan_history_store.load("a")["items"], [{"id": "mine", "user_key": "a", "ts": 1}])
        request.return_value = {"ok": False}
        self.assertFalse(scan_history_store.load("a")["ok"])

    def test_history_excludes_document_content(self):
        batch = {"file": "loan.pdf", "result": {"raw_text": "entire document", "bank_raw_text": "private source",
                 "pdf_bytes": b"PDF", "extracted_data": {"amount": 100}, "conditions": [{"desc": "Pay stub", "bytes": b"x"}]}}
        cleaned = scan_history_store.parsed_batch(batch)
        self.assertNotIn("raw_text", cleaned["result"])
        self.assertNotIn("bank_raw_text", cleaned["result"])
        self.assertNotIn("pdf_bytes", cleaned["result"])
        self.assertEqual(cleaned["result"]["extracted_data"], {"amount": 100})
        json.dumps(cleaned)

    @patch("supabase_auth._save_setting_json", return_value={"ok": True})
    def test_saves_only_current_account_and_keeps_old_results(self, save):
        items = [{"id": "old", "user_key": "user-a", "ts": 1, "batch": {}},
                 {"id": "other", "user_key": "user-b", "batch": {}}]
        scan_history_store.save("user-a", items)
        self.assertEqual(save.call_args.args[0], "scan_history:user-a")
        self.assertEqual([i["id"] for i in save.call_args.args[1]["items"]], ["old"])
        scan_history_store.save("user-a", [])
        self.assertEqual(save.call_args.args[1], {"items": []})


if __name__ == "__main__":
    unittest.main()
