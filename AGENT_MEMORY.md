# Agent Memory — TakeIn SMS

## Project

- **Name:** TakeIn SMS (Google Voice Takeout → Android SMS)
- **Stack:** Python + CustomTkinter + ADB; PyInstaller packaging
- **Template:** agent-project-bootstrap **0.15.1** (aligned)

## Durable facts

- Converter parses real GV HTML (`abbr.dt`, `<q>`, `Me` vs contact; named files via `tel:`)
- Root import writes `mmssms.db` via sqlite3; backs up first; idempotent on `(address,date,type,body)`
- Non-root path: XML + optional push + SMS Backup & Restore instructions
- Do **not** live-import SMS unless human explicitly asks

## Active focus

- Finish bootstrap alignment Sequential lane in `BUILD_PLAN.md`
- Keep product code stable while adding agent/CI surface

## Do not re-litigate

- Skip Android APK for v1 (SMS Backup & Restore covers phone-side non-root restore)
- Product name is **TakeIn SMS** / `TakeInSMS.exe`
