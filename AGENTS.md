# Agent Router — TakeIn SMS

1. **First read:** `docs/START_HERE.md`
2. **Cursor modes:** `docs/CURSOR_MODES.md` (Ask / Plan / Agent / Debug)
3. **Project context:** `docs/INITIALIZATION_PROMPT.md` (TakeIn SMS dimensions)
4. **Task board:** `BUILD_PLAN.md` — Sequential before Parallel — status: 🔲 open · ✅ done · ❌ blocked
5. **Living memory:** update `AGENT_MEMORY.md` only at milestone boundaries
6. **Alignment record:** `docs/BOOTSTRAP_ALIGNMENT.md`

> Legacy `.cursorrules` is deprecated. Use `.cursor/rules/*.mdc` and this file instead.

## Product

**TakeIn SMS** — Google Voice Takeout → Android SMS (Windows GUI + CLI).

| Layer | Tech |
|-------|------|
| UI | CustomTkinter (`gui_app.py`) |
| Convert | `convert_gvoice.py` |
| Import | `import_gvoice_adb.py` (requires `adb root`) |
| Orchestration | `pipeline.py`, `adb_util.py` |
| Packaging | PyInstaller → `TakeInSMS.exe` |

**Stack selection:** FOSS · `modules/python` only · device label `[ADB]` (host-side; no Android APK module).

## Architecture Constraints

- Pure FOSS under MIT; no proprietary closed-source SDKs in the production path
- Prefer small, reviewable diffs; do not rewrite working convert/import logic without cause
- Strict typing and linting for new Python (ruff; mypy as milestone gate)
- Core business logic stays framework-light (GUI wraps library APIs)

## Coding Style

- Conventional Commits
- Read-before-write via `@filename`
- Cursor mode routing per `docs/CURSOR_MODES.md`

## Session Protocol

- On session start: `START_HERE.md` → pick mode → `BUILD_PLAN.md` Sequential lane
- On milestone end: update `AGENT_MEMORY.md`, append `DECISION_LOG.md`
- On 3-strike failure: halt and escalate
- Destructive ops require `[HUMAN]` approval (see `.cursor/rules/destructive-ops.mdc`)
- **SMS / ADB:** never run live root import (`import_gvoice_adb` / pipeline without `--dry-run`) unless the human explicitly requests a device write — prefer dry-run and XML export

## Module Activation

- Active: `modules/python/MODULE.md`
- Inactive: web, android app, node, rust, go, lightroom — do not copy `examples/` wholesale
