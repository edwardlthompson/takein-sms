# Bootstrap Alignment — Gap Analysis

**Project:** TakeIn SMS (Google Voice Takeout → Android SMS)  
**Upstream:** [edwardlthompson/agent-project-bootstrap](https://github.com/edwardlthompson/agent-project-bootstrap) **v0.15.1**  
**Date:** 2026-07-29  
**Mode:** Migration / alignment (not fresh bootstrap)  
**Status:** Phase 0–4 alignment executed under agent-chosen ethical defaults (2026-07-29). See `DECISION_LOG.md`.

---

## 1. Current repo snapshot

| Area | Present today |
|------|----------------|
| App identity | TakeIn SMS — Windows GUI + CLI |
| Tech stack | **Python 3.11+** (CustomTkinter GUI, stdlib XML/zip, ADB subprocess). Packaged via PyInstaller. Bundled Android `platform-tools` for ADB. |
| Application code | `gui_app.py`, `pipeline.py`, `convert_gvoice.py`, `import_gvoice_adb.py`, `adb_util.py`, `build.ps1`, `TakeInSMS.spec`, `requirements.txt`, `README.md` |
| Agent surface | **None** (no `AGENTS.md`, `.cursor/`, `docs/START_HERE.md`, memory files, `BUILD_PLAN.md`) |
| VCS | **No git repository** initialized |
| License | **None** (`LICENSE` missing; README says “use at your own risk”) |
| CI / security | **None** (no `.github/`, Dependabot, CodeQL, `SECURITY.md`) |
| Tooling | Minimal `.gitignore` only; no `.editorconfig`, `.gitattributes`, `.cursorignore`, pre-commit, ruff/mypy/pytest |
| Artifacts in tree | `dist/`, `build/`, `vendor/platform-tools/`, `backups/`, `gvoice_sms.xml`, `gvoice_import.sql`, `__pycache__/` |

**Not in scope for product:** Android APK, web/PWA, Node, Rust, Go, Lightroom. Phone interaction is via **host ADB** (Windows), not an on-device app.

---

## 2. What already matches the template

Very little. Intentional overlaps only:

- FOSS-friendly product direction (local-first, no proprietary SDKs in the import path)
- README with run/build instructions
- `.gitignore` covering some generated paths (`dist/`, `build/`, `vendor/platform-tools/`, backups, XML/SQL outputs)
- Python as the sole application language (maps cleanly to `modules/python/`)

---

## 3. What is missing (relative to v0.15.1)

### Phase 1 — Core agent infrastructure (required)

- [ ] `AGENTS.md` (router; deprecate any future `.cursorrules`)
- [ ] `docs/START_HERE.md`, `docs/CURSOR_MODES.md`, `docs/FOR_AGENTS.md`
- [ ] `docs/INITIALIZATION_PROMPT.md` (adapted for TakeIn SMS, not blank template)
- [ ] `.cursor/rules/*.mdc` (core set: cursor-modes, batch-commands, destructive-ops, local-compute, read-before-write, foss-compliance, repo-hygiene, windows-encoding, testing, ci-gates, security-triage, …)
- [ ] `.cursor/commands/` batch slash-commands + `docs/help/BATCH_COMMANDS.md` + `docs/BATCH_COMMANDS.md`
- [ ] `AGENT_MEMORY.md`, `DECISION_LOG.md`, `KNOWLEDGE_BASE.md`
- [ ] Living `BUILD_PLAN.md` with labels `[AGENT]` / `[HUMAN]` / `[ADB]` / `[AUTO]` and emoji status 🔲 ✅ ❌
- [ ] `.cursorignore`, `.editorconfig`, `.gitattributes`, expanded `.gitignore`
- [ ] `.env.example` (merge-safe; no secrets — ADB paths only if needed)
- [ ] `.cursor-session-state.example.json`
- [ ] `.template-version` + `.template-update.json` (track upstream **0.15.1**)
- [ ] `PROMPT_LIBRARY.md`, `TEMPLATE_INDEX.json` (adapted)
- [ ] `COMPLETED_TASKS.md`, `HUMAN_BACKLOG.md`
- [ ] `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (FOSS hygiene)

### Phase 2 — Tooling, scripts, CI, security

- [ ] Curated `scripts/` from upstream (validate-bootstrap, hygiene, encoding, gates, template-update checker) — **subset**, not all 86 blindly
- [ ] `.github/workflows/` — start lean: `ci.yml` (ruff/pytest), `security.yml` or CodeQL, `dependency-review.yml`, Dependabot
- [ ] `SECURITY.md`, `docs/SECURITY_TRIAGE.md` (and light `docs/THREAT_MODEL.md` for SMS DB / ADB root risks)
- [ ] `.github/dependabot.yml`
- [ ] `.pre-commit-config.yaml` (ruff + basic hygiene)
- [ ] `pyproject.toml` + stricter dependency story (per `modules/python/MODULE.md`) — keep `requirements.txt` for PyInstaller path or migrate carefully

### Phase 3 — Stack modules

- [ ] Activate **`modules/python/MODULE.md`** only
- [ ] Do **not** copy `examples/python/` wholesale; optionally reference Golden Path for ruff/mypy/pytest later
- [ ] Do **not** activate `modules/android` as an app module (no APK). Document ADB as a **device label** in BUILD_PLAN instead
- [ ] Skip web / design-tokens / i18n modules (N/A)

### Phase 4 — Process & memory

- [ ] Session protocol documented in README + START_HERE
- [ ] Conventional Commits expectation
- [ ] Archive prior work (TakeIn SMS v1 GUI/import) into `COMPLETED_TASKS.md`

---

## 4. Conflicts / careful migrations

| Conflict | Risk | Strategy |
|----------|------|----------|
| **No git repo** | Cannot use CI, Dependabot, or conventional history until `git init` (+ optional remote) | `[HUMAN]` decide: init local git now? push to GitHub? |
| **No LICENSE** | Template assumes MIT; README disclaimer only | `[HUMAN]` confirm MIT (or other). Agent will not invent a conflicting license. |
| **Large `dist/` / `vendor/` / SMS backups** | Accidental commit of binaries / PII-adjacent SMS DB dumps | Strengthen `.gitignore`; never track `backups/`, `output/`, `gvoice_*.xml/sql`, `dist/`, `build/` |
| **`requirements.txt` unpinned loosely** | Python module wants lockfile (`uv.lock`) + ruff/mypy | Additive: add `pyproject.toml` + ruff; introduce `uv.lock` when ready; keep `requirements.txt` for current build.ps1 until migrated |
| **ADB root import is destructive to device SMS DB** | Template destructive-ops rules are git-centric; need project-specific ADB/SMS rules | Extend `.cursor/rules/destructive-ops.mdc` (or project rule) to require `[HUMAN]`/`[ADB]` before live DB writes |
| **Full upstream CI suite** (Pages, release-please, scorecard, stale, …) | Noise / broken checks on a tiny desktop tool with no release pipeline yet | Adopt **minimal CI first**; leave release-please/Pages/scorecard as optional `[HUMAN]` follow-ups |
| **Copying all 86 scripts** | Many assume bash/devcontainer/web/android examples | Copy validation + hygiene + encoding + template-update + agent-run helpers that work on Windows (Git Bash / Python wrappers) |
| **Product README** | Must not be replaced by template README | Merge: keep TakeIn SMS product docs; add “How agents work here” section |

---

## 5. Recommended stack selection

```text
distribution_tier: foss
stacks: [python]
device_labels: [ADB]   # host-side adb root import; not modules/android
ui: customtkinter (Windows desktop)
packaging: PyInstaller (TakeInSMS.exe)
```

**Inactive / do not copy:** `modules/web`, `modules/android` (app), `modules/node`, `modules/rust`, `modules/go`, `modules/lightroom`, `examples/*` wholesale, `design-tokens` (unless later UI polish sprint).

---

## 6. Risk areas

1. **Device SMS integrity** — root import mutates `mmssms.db`; backups already exist in product; agents must never re-run live import without confirmation.
2. **PII** — Takeout HTML / generated XML / DB backups contain message content; must stay gitignored.
3. **No VCS yet** — structural alignment without git leaves CI untestable; recommend `git init` early in Phase 1.
4. **Windows-first** — prefer Python scripts / PowerShell alongside upstream `.sh` (template has Windows encoding rules; keep them).
5. **Secrets** — none today; `.env.example` should stay empty of credentials; never commit `.env`.

---

## 7. Prioritized alignment plan (Sequential)

### Sequential lane (proposed)

1. 🔲 `[HUMAN]` Confirm MIT license + whether to `git init` / create GitHub remote  
2. 🔲 `[AGENT]` Write/seed core docs + memory + `AGENTS.md` + adapted START_HERE / FOR_AGENTS / CURSOR_MODES / INITIALIZATION_PROMPT  
3. 🔲 `[AGENT]` Add `.cursor/rules` + commands + batch-command docs (from upstream 0.15.1)  
4. 🔲 `[AGENT]` Add `BUILD_PLAN.md` (product + alignment remaining work), `COMPLETED_TASKS.md`, `HUMAN_BACKLOG.md`  
5. 🔲 `[AGENT]` Editor/hygiene files: `.editorconfig`, `.gitattributes`, `.cursorignore`, expand `.gitignore`, `.env.example`, session-state example, `.template-version`  
6. 🔲 `[AGENT]` Activate `modules/python/MODULE.md`; add minimal `pyproject.toml` + ruff config **without** rewriting app logic  
7. 🔲 `[AGENT]` Curate `scripts/` subset + wire `validate-bootstrap` / hygiene for this tree  
8. 🔲 `[AGENT]` Add `SECURITY.md` + `docs/SECURITY_TRIAGE.md` (ADB/SMS threat notes)  
9. 🔲 `[AGENT]` Add lean `.github/workflows/ci.yml` + Dependabot + dependency-review (only after git remote exists)  
10. 🔲 `[AUTO]` Run validate/hygiene scripts; fix failures  
11. 🔲 `[HUMAN]` Review CI enablement (CodeQL / Scorecard / release-please — optional)  
12. 🔲 `[ADB]` Manual: GUI smoke + dry-run import on rooted phone (no live re-import unless requested)

### Parallel lane (after Sequential 2–5)

- 🔲 `[AGENT]` PROMPT_LIBRARY + TEMPLATE_INDEX adaptation  
- 🔲 `[AGENT]` CONTRIBUTING / CODE_OF_CONDUCT / THIRD_PARTY note for bundled platform-tools  
- 🔲 `[AGENT]` README “How agents should work in this repo”

### Human & device (after automation)

- 🔲 `[HUMAN]` Approve MIT + git remote  
- 🔲 `[HUMAN]` Enable GitHub Dependabot / security features on remote  
- 🔲 `[ADB]` Device verification pass for TakeIn SMS  
- 🔲 `[HUMAN]` Decide whether to adopt release-please / Scorecard later  

---

## 8. High-risk decisions (resolved)

Human asked the agent to choose the most logical/ethical defaults:

1. **License:** MIT adopted.  
2. **Git:** `git init` + public GitHub `takein-sms`.  
3. **CI scope:** Lean (ruff + pytest + Dependabot + dependency-review).  
4. **Python toolchain:** `pyproject.toml` + ruff; keep `requirements.txt` for PyInstaller.  
5. **Live device imports:** Forbidden for agents unless human explicitly requests.

---

## 9. Out of scope for this alignment

- Rewriting TakeIn SMS application logic  
- Building an Android APK  
- Blind overwrite of product `README.md`  
- Committing `dist/`, `vendor/platform-tools/`, SMS backups, or Takeout data  
- Force-push / history rewrite (N/A until git exists)

---

## 10. Migration notes (preview for human)

After Phase 1–4 (post-approval), expect:

- New agent entrypoints at repo root and under `docs/`  
- Cursor rules/commands from bootstrap v0.15.1  
- A living `BUILD_PLAN.md` tracking both product work and remaining alignment  
- Security + lean CI once git remote exists  
- Product code unchanged except additive config (`pyproject.toml`, ignore rules)

**Still manual after automation:** license/git remote approval, GitHub security toggles, optional ADB device re-verify.
