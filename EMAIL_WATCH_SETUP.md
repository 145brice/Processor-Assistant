Email Watch stores credentials privately under `email_watch:<account ID>` in
Supabase. The entire configuration is encrypted with the server's stable
`PA_SETTINGS_ENCRYPTION_KEY`. Saving fails if encryption or durable hosted
storage is unavailable; there is no plaintext fallback. Production requires
`SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`. Keep the service-role key on the
server. The settings table is supplied by `SUPABASE_SCHEMA.sql`.

Use a persistent volume for `PA_EMAIL_DATA_DIR`, or use Railway's
`RAILWAY_VOLUME_MOUNT_PATH`. Each account has a separate hashed directory for
attachments, pending results, duplicate detection and saved watch state.
Credentials survive container replacement through Supabase; attachments and
pending state survive through the volume. For local use, these files default
to ignored `email_data/` and encrypted config files. Back up the server secret
securely; changing or losing it makes existing credentials unreadable.

Workers resume for the signed-in account on its first visit after a server
restart. Workers run in one app process; keep the service at one replica.
Turning off watching allows an in-progress check to finish. Disconnecting also
removes saved credentials. Each client must set up their own inbox; the legacy
shared `email_config.json` is never automatically imported into any account.
The script `scripts/secure_legacy_email_config.py` verifies an encrypted local
archive before deleting that legacy plaintext file.

Mail is read using IMAP over TLS with a read-only inbox and `BODY.PEEK[]`.
Attachments are matched only against loans belonging or explicitly shared with
the account. Email content and passwords are excluded from error messages.
Password fields stay blank when displaying previously saved configuration.

The updated `SUPABASE_SECURITY.sql` includes the `email_watch:<auth.uid()>`
owner policy. Server-side operations use the service role, so this update does
not require a policy change to start working. Apply that SQL before enabling
direct authenticated client access; never enable anonymous settings access.

Removing the credential file in a new commit does not erase Git history.
Revoke any app password previously committed, including copies on older
branches. History rewriting requires coordinating with everyone using the repo
and force-pushing affected branches; it does not replace password revocation.
