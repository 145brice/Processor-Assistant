import ast
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import account_email_watch as watch


class EmailWatchUITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"PA_EMAIL_DATA_DIR": self.temp.name,
                              "PA_SETTINGS_ENCRYPTION_KEY": "test-secret",
                              "SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "",
                              "RAILWAY_ENVIRONMENT_ID": ""})
        self.env.start()
        watch._watchers.clear()
        source = Path("app.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(source)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                        and node.name == "show_email_watch_controls_page")
        self.script = ("import streamlit as st\n"
                       "def _current_auth_user_key(): return 'alice'\n"
                       "def _visible_account_loans(loans): return loans\n"
                       + ast.get_source_segment(source, function)
                       + "\nshow_email_watch_controls_page()\n")

    def tearDown(self):
        watch._watchers.clear()
        self.env.stop()
        self.temp.cleanup()

    def test_saved_password_cleared_and_disconnect_works(self):
        app = AppTest.from_string(self.script).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        app.text_input(key="ew_email").set_value("alice@example.com")
        app.text_input(key="ew_pass").set_value("private-app-password")
        app.button(key="ew_save_creds").click().run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.text_input(key="ew_pass").value, "")
        self.assertTrue(watch.for_user("alice").get_config()["password_saved"])
        app.button(key="ew_disconnect").click().run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(watch.for_user("alice").get_config(), {})

    def test_sandbox_does_not_show_credentials(self):
        # Replace only the call, keeping the function definition intact.
        script = self.script.rsplit("\nshow_email_watch_controls_page()", 1)[0] + "\nst.session_state.sandbox_mode = True\nshow_email_watch_controls_page()\n"
        app = AppTest.from_string(script).run(timeout=30)
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.text_input), 0)


if __name__ == "__main__":
    unittest.main()
