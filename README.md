# TakeIn SMS

**Google Voice Takeout → Android SMS**

TakeIn SMS is the inverse of Google Takeout: drop your Voice export ZIPs, connect a phone over ADB, and take your message history *in* to the native Android SMS store.

## Features

- Drag-and-drop (or browse) one or more Google Takeout `.zip` files / Voice folders
- Parses real Google Voice HTML threads (including named-contact files)
- **Rooted devices** (`adb root`, e.g. LineageOS): one-click import into `mmssms.db` with before/after SMS count verification and automatic DB backup
- **Non-root devices**: converts to SMS Backup & Restore XML, optionally pushes it to `/sdcard/Download/`, and shows restore steps

## Requirements

- Windows 10/11
- Python 3.11+ (for running from source) **or** the built `TakeInSMS.exe`
- Android phone with **USB debugging** enabled and authorized for this PC
- For one-click import: **adb root** (LineageOS / userdebug builds). Stock phones without root use the XML + [SMS Backup & Restore](https://play.google.com/store/apps/details?id=com.riteshsahu.SMSBackupRestore) path.

## Run from source

```powershell
cd "C:\Users\edwar\Google Voice"
python -m pip install -r requirements.txt
# Optional: bundle platform-tools under vendor\ (or use adb on PATH)
.\build.ps1   # downloads platform-tools if missing, then builds; or just:
python gui_app.py
```

### CLI (same engine)

```powershell
python convert_gvoice.py -o gvoice_sms.xml path\to\takeout.zip
python import_gvoice_adb.py gvoice_sms.xml          # requires adb root
python import_gvoice_adb.py gvoice_sms.xml --dry-run
```

## Build Windows app

```powershell
.\build.ps1
```

Output: `dist\TakeInSMS\TakeInSMS.exe` (one-folder build with bundled `adb`).

## Safety

- Before a root import, TakeIn SMS pulls a copy of `mmssms.db` into `output\backups\` (or `backups\` for CLI).
- Re-running import skips exact duplicate rows `(address, date, type, body)`.
- Keep USB connected until verification finishes.

## After import

1. Open **Google Messages** and confirm conversations appear.
2. Open **Cloze Pro** (or your CRM) so it can reindex the native SMS database.

## How agents should work in this repo

1. Read [`docs/START_HERE.md`](docs/START_HERE.md) and [`docs/CURSOR_MODES.md`](docs/CURSOR_MODES.md).
2. Follow [`AGENTS.md`](AGENTS.md); execute [`BUILD_PLAN.md`](BUILD_PLAN.md) **Sequential** lane first.
3. Prefer small diffs; do not rewrite convert/import logic without cause.
4. **Never** run a live root SMS import unless a human explicitly asks — use `--dry-run`.
5. Status markers in plans: 🔲 open · ✅ done · ❌ blocked (no GitHub `- [ ]` checkboxes).
6. Alignment notes: [`docs/BOOTSTRAP_ALIGNMENT.md`](docs/BOOTSTRAP_ALIGNMENT.md).

## License

MIT — see [`LICENSE`](LICENSE).

Always keep a backup of your phone’s SMS database before importing. Use at your own risk for device-side changes.
