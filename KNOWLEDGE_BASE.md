# Knowledge Base — TakeIn SMS

## KB-TI-001 — Google Voice Takeout HTML shape

Takeout Text HTML uses `<div class="message">`, `<abbr class="dt" title="ISO-8601">`, sender in `cite.sender`, body in `<q>`. Sent messages use `<abbr class="fn">Me</abbr>`. Named-contact filenames lack E.164; resolve peer via non-Me `tel:` hrefs.

## KB-TI-002 — Android SMS write requires default SMS app or root

On modern Android, `content://sms` inserts from shell fail unless the caller is the default SMS app. With `adb root` on LineageOS, direct sqlite to `mmssms.db` works and avoids a helper APK.

## KB-TI-003 — Thread resolution

1:1 threads use `canonical_addresses._id` as `threads.recipient_ids` (text). Create canonical row + thread before inserting `sms` rows. Triggers update message_count/snippet.

## KB-TI-004 — PII handling

Takeout archives, generated XML, SQL, and DB backups contain message content. Never commit them. Prefer local `output/` and `backups/` (gitignored).

## KB-TI-005 — Template alignment

Upstream: `edwardlthompson/agent-project-bootstrap`. Child does not auto-sync; use `scripts/check-template-updates.*` and `docs/UPGRADING_FROM_TEMPLATE.md`.
