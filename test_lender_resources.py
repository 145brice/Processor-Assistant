import unittest

from approval_intelligence import detect_lender_name
from lender_resources import resources_for_lender


class LenderResourceTests(unittest.TestCase):
    def test_matches_supported_lender_aliases(self):
        cases = {
            "UWM": "uwm",
            "United Wholesale Mortgage": "uwm",
            "11 Mortgage": "eleven_mortgage",
            "Ark-La-Tex Financial Services, LLC dba Eleven Mortgage": "eleven_mortgage",
            "Rocket Mortgage": "rocket",
            "Equity Prime Mortgage LLC": "epm",
            "EPM Wholesale": "epm",
        }
        for lender, expected in cases.items():
            with self.subTest(lender=lender):
                self.assertEqual(resources_for_lender(lender).get("key"), expected)

    def test_unknown_lender_has_no_links(self):
        self.assertEqual(resources_for_lender("Unknown Lender"), {})
        self.assertEqual(resources_for_lender("Unlisted Community Bank"), {})

    def test_catalog_only_returns_https_links(self):
        entry = resources_for_lender("EPM")
        self.assertTrue(entry["resources"])
        self.assertTrue(all(row["url"].startswith("https://") for row in entry["resources"]))

    def test_detects_new_lender_names_from_approval_text(self):
        self.assertEqual(detect_lender_name("EPM Wholesale\nConditional Approval"), "EPM Wholesale")
        self.assertEqual(detect_lender_name("11 Mortgage\nUnderwriting Approval"), "11 Mortgage")


if __name__ == "__main__":
    unittest.main()
