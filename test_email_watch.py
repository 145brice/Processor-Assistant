import json
import os
import tempfile
import threading
import unittest
from email.message import EmailMessage
from pathlib import Path
from unittest.mock import MagicMock, patch

import account_email_watch as watch
import email_store


class EmailWatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"PA_EMAIL_DATA_DIR": self.temp.name,
                              "PA_SETTINGS_ENCRYPTION_KEY": "test-server-secret",
                              "SUPABASE_URL": "", "SUPABASE_SERVICE_ROLE_KEY": "",
                              "RAILWAY_ENVIRONMENT_ID": ""})
        self.env.start()
        watch._watchers.clear()
        self.a = watch.for_user("alice")
        self.b = watch.for_user("bob")

    def tearDown(self):
        self.a.stop()
        self.b.stop()
        self.env.stop()
        self.temp.cleanup()

    def save(self, watcher=None):
        (watcher or self.a).save_config("alice@example.com", "private-app-password", "Gmail")

    def test_encrypted_configuration_survives_restart_and_is_private(self):
        self.save()
        raw = (self.a.directory / "config.json").read_text()
        self.assertNotIn("private-app-password", raw)
        self.assertNotIn("alice@example.com", raw)
        self.assertNotIn("password", self.a.get_config())
        self.assertTrue(watch.EmailWatcher("alice").get_config()["password_saved"])
        self.assertEqual(self.b.get_config(), {})
        self.assertEqual(email_store.load("alice")["password"], "private-app-password")

    def test_missing_or_wrong_key_does_not_fall_back_to_plaintext(self):
        with patch.dict(os.environ, {"PA_SETTINGS_ENCRYPTION_KEY": ""}):
            with self.assertRaises(ValueError):
                self.save()
        self.assertFalse((self.a.directory / "config.json").exists())
        self.save()
        with patch.dict(os.environ, {"PA_SETTINGS_ENCRYPTION_KEY": "wrong-key"}):
            with self.assertRaises(ValueError):
                self.a.get_config()

    def test_copied_ciphertext_cannot_be_used_by_another_account(self):
        self.save()
        self.b.directory.mkdir(parents=True)
        (self.b.directory / "config.json").write_bytes((self.a.directory / "config.json").read_bytes())
        with self.assertRaises(ValueError):
            self.b.get_config()

    def test_anonymous_and_sandbox_users_rejected(self):
        for user_key in ("", "sandbox"):
            with self.assertRaises(ValueError):
                watch.for_user(user_key)
        self.assertTrue(email_store.account_dir("../../outside").is_relative_to(Path(self.temp.name)))

    def test_password_preserved_only_for_same_inbox(self):
        self.save()
        self.a.save_config("alice@example.com", "", "Gmail", interval=10)
        self.assertEqual(email_store.load("alice")["password"], "private-app-password")
        with self.assertRaises(ValueError):
            self.a.save_config("another@example.com", "", "Gmail")

    def test_legacy_shared_config_is_never_loaded(self):
        with patch("pathlib.Path.read_text", side_effect=AssertionError("Legacy read")):
            self.assertEqual(self.b.get_config(), {})

    def test_account_worker_stop_does_not_stop_other_worker(self):
        self.save(self.a)
        self.save(self.b)
        started = {"alice": threading.Event(), "bob": threading.Event()}
        def run(instance):
            started[instance.user_key].set()
            instance._stop.wait(5)
        with patch.object(watch.EmailWatcher, "_loop", run):
            self.a.start()
            self.b.start()
            self.assertTrue(started["alice"].wait(1))
            self.assertTrue(started["bob"].wait(1))
            self.a.stop()
            self.a._thread.join(1)
            self.assertFalse(self.a.is_running())
            self.assertTrue(self.b.is_running())
            self.b.stop()
            self.b._thread.join(1)

    def test_readonly_attachments_deduplicated_and_persisted_per_account(self):
        self.save()
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["Subject"] = "Alice Smith"
        msg.set_content("Document")
        msg.add_attachment(b"private file", maintype="text", subtype="plain", filename="../../Alice Smith.txt")
        mail = MagicMock()
        mail.select.return_value = ("OK", [b"1"])
        mail.response.return_value = ("UIDVALIDITY", [b"1"])
        mail.uid.side_effect = lambda command, *args: ("OK", [b"1"]) if command == "search" else ("OK", [(b"1", msg.as_bytes())])
        loans = [{"id": 1, "borrower": "Alice Smith", "owner_user_key": "bob"}]
        with patch("imaplib.IMAP4_SSL", return_value=mail):
            self.assertEqual(self.a.check_now(loans=loans)[0], 1)
            self.assertEqual(self.a.check_now()[0], 0)
            restarted = watch.EmailWatcher("alice")
            self.assertEqual(restarted.check_now()[0], 0)
        mail.select.assert_called_with("inbox", readonly=True)
        self.assertIn("(BODY.PEEK[])", [call.args[-1] for call in mail.uid.call_args_list])
        match = restarted.get_matches()[0]
        self.assertIsNone(match.get("loan_id"))
        self.assertTrue(Path(match["file_path"]).is_relative_to(self.a.incoming_dir))
        self.assertEqual(self.b.get_matches(), [])
        restarted.dismiss(0)
        self.assertEqual(watch.EmailWatcher("alice").get_matches(), [])

    def test_login_failure_closes_connection_without_leaking_password(self):
        self.save()
        mail = MagicMock()
        mail.login.side_effect = watch.imaplib.IMAP4.error("private-app-password")
        with patch("imaplib.IMAP4_SSL", return_value=mail):
            count, message = self.a.check_now()
        self.assertEqual(count, 0)
        self.assertNotIn("private-app-password", message)
        mail.logout.assert_called_once()

    def test_cloud_save_uses_private_key_and_verifies_readback(self):
        import supabase_auth
        stored = {}
        def save(key, value, **kwargs):
            self.assertEqual(key, "email_watch:alice")
            self.assertEqual(kwargs["user_key"], "alice")
            self.assertNotIn("private-app-password", json.dumps(value))
            stored.update(value)
            return {"ok": True}
        with patch.dict(os.environ, {"SUPABASE_URL": "https://example.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "service-key"}), \
             patch.object(supabase_auth, "_save_setting_json", side_effect=save), \
             patch.object(email_store, "_cloud_load", side_effect=lambda auth, user: stored):
            self.save()
            self.assertEqual(self.a.get_config()["email"], "alice@example.com")
        self.assertFalse((self.a.directory / "config.json").exists())

    def test_hosted_storage_failure_never_reports_durable_save(self):
        with patch.dict(os.environ, {"RAILWAY_ENVIRONMENT_ID": "production"}):
            with self.assertRaises(ValueError):
                self.save()

    def test_disconnect_removes_only_own_credentials(self):
        self.save(self.a)
        self.save(self.b)
        self.a.disconnect()
        self.assertEqual(self.a.get_config(), {})
        self.assertTrue(self.b.get_config()["password_saved"])

    def test_enabled_watcher_resumes_after_process_restart(self):
        self.save()
        def run(instance):
            instance._stop.wait(5)
        with patch.object(watch.EmailWatcher, "_loop", run):
            self.a.start()
            # Simulate process termination without the user turning off watching.
            self.a._stop.set()
            self.a._thread.join(1)
            watch._watchers.clear()
            resumed = watch.for_user("alice")
            self.assertTrue(resumed.is_running())
            resumed.stop()
            resumed._thread.join(1)
            self.a = resumed


if __name__ == "__main__":
    unittest.main()
