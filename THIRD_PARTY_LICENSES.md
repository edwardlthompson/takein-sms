# Third-Party Licenses — TakeIn SMS

## Runtime (Python)

See `requirements.txt` / `pyproject.toml`. Major UI dependency:

- **customtkinter** — customtkinter license (see package metadata)
- **windnd** — for Windows drag-and-drop (see package metadata)

## Bundled tools (not committed; downloaded by `build.ps1`)

- **Android SDK Platform-Tools** (`adb`) from Google — see `vendor/platform-tools/NOTICE.txt` after download. Redistribute according to Google’s SDK license terms when shipping `TakeInSMS.exe` builds that bundle platform-tools.

## Upstream template

Agent/CI/docs scaffolding adapted from [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) (MIT).
