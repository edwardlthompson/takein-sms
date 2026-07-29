# Start Here — TakeIn SMS

> **Read this file first** — whether you are a human or a Cursor agent.

## What is this?

**TakeIn SMS** imports Google Voice Takeout archives into Android SMS. This repository is aligned with [`agent-project-bootstrap`](https://github.com/edwardlthompson/agent-project-bootstrap) **v0.15.1** (see `docs/BOOTSTRAP_ALIGNMENT.md`).

## Which mode?

- **Product development:** read `docs/CURSOR_MODES.md`, then `AGENTS.md`, then `BUILD_PLAN.md`
- **Bootstrap reference / template upgrade:** `docs/FOR_AGENTS.md` + `docs/UPGRADING_FROM_TEMPLATE.md` + `TEMPLATE_INDEX.json`

## Cursor modes

See [`docs/CURSOR_MODES.md`](CURSOR_MODES.md) — pick Ask / Plan / Agent / Debug before editing code.

## Agent shortcuts

Type **`/`** in Cursor Agent chat. Cheat sheet: [`docs/help/BATCH_COMMANDS.md`](help/BATCH_COMMANDS.md). Useful here: `/verify`, `/gates`, `/plan`, `/build`.

## Read order (product)

1. `README.md` (product usage)
2. `docs/START_HERE.md` (this file)
3. `docs/CURSOR_MODES.md`
4. `AGENTS.md`
5. `BUILD_PLAN.md` Sequential lane
6. `modules/python/MODULE.md`
7. App modules: `gui_app.py`, `pipeline.py`, `convert_gvoice.py`, `import_gvoice_adb.py`, `adb_util.py`

## BUILD_PLAN labels

`AGENT` | `HUMAN` | `ADB` | `AUTO` — filter with `grep '\[AGENT\]' BUILD_PLAN.md`

**Status markers:** 🔲 open · ✅ done · ❌ blocked — emoji only (never GitHub `- [ ]` checkboxes).

## Security & device safety

- Vulnerability reporting: `SECURITY.md`
- CVE triage: `docs/SECURITY_TRIAGE.md`
- **Never** run a live root SMS import unless the human explicitly asks — use `--dry-run` for agent verification
- Keep Takeout ZIPs, XML exports, and `mmssms.db` backups **out of git**

## Human quick start

```powershell
python -m pip install -r requirements.txt
python gui_app.py
# or build: .\build.ps1  →  dist\TakeInSMS\TakeInSMS.exe
```
