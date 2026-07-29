# Decision Log — TakeIn SMS

## 2026-07-29 — /audit remediation

**Context:** Full `/audit` against child TakeIn SMS repo after bootstrap alignment.

**Actions:** Restored missing hygiene/example stubs; fixed changelog Unreleased heading; added release-please version manifest (no workflow); made pytest workflow check accept root `pyproject.toml`; pinned runtime deps; documented packaging; slimmed `TEMPLATE_INDEX.json` then re-indexed scripts/workflows; achieved green `validate-bootstrap --quick`, hygiene, feature-gate (python), watch-agent-gates.

**Deferred to HUMAN:** Dependabot alerts UI, CodeQL/Scorecard, branch protection, actions Dependabot PR review.

## 2026-07-29 — Bootstrap alignment high-risk defaults

**Context:** Align live TakeIn SMS repo with `agent-project-bootstrap` v0.15.1. Human asked agent to choose the most logical and ethical answers to Phase 0 confirmation questions.

| Question | Decision | Rationale |
|----------|----------|-----------|
| License | **MIT** | Matches upstream FOSS template; maximizes reuse; ethical default for open tooling |
| Git | **`git init` + public GitHub repo `takein-sms`** | Enables CI, Dependabot, and collaboration; public matches MIT FOSS intent |
| CI scope | **Lean** (ruff + pytest smoke + Dependabot; not full template suite) | Proportionate to a small desktop tool; avoids broken unused stack jobs |
| Python toolchain | **`pyproject.toml` + ruff now; keep `requirements.txt` for PyInstaller** | Improves quality without breaking `build.ps1` |
| Live SMS DB import | **Forbidden for agents unless human explicitly requests** | Ethical: message DBs are sensitive; prefer `--dry-run` |

**Stack:** `modules/python` only; `[ADB]` as device label (no Android APK module).

**Refs:** `docs/BOOTSTRAP_ALIGNMENT.md`, `.cursor/stack-selection.json`
