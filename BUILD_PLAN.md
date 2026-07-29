# BUILD_PLAN — TakeIn SMS

**Labels:** `[AGENT]` `[HUMAN]` `[ADB]` `[AUTO]`  
**Status:** 🔲 open · ✅ done · ❌ blocked  
**Rule:** Finish Sequential before starting Parallel. Human/device items wait until automation is green.

---

## Legend

| Label | Meaning |
|-------|---------|
| `[AGENT]` | Agent may execute |
| `[HUMAN]` | Requires human decision or GitHub settings |
| `[ADB]` | Requires physical device / USB debugging |
| `[AUTO]` | CI or local gate scripts |

---

## Sequential

### Sprint 0 — Bootstrap alignment

1. ✅ `[AGENT]` Phase 0 gap analysis → `docs/BOOTSTRAP_ALIGNMENT.md`
2. ✅ `[HUMAN]` High-risk defaults chosen (MIT, git, lean CI, pyproject+ruff, no surprise DB writes)
3. ✅ `[AGENT]` Core agent surface (AGENTS, START_HERE, rules, commands, memory seeds)
4. ✅ `[AGENT]` `pyproject.toml` + ruff; keep `requirements.txt` for PyInstaller
5. ✅ `[AGENT]` Lean GitHub Actions CI + Dependabot (pip + github-actions)
6. ✅ `[AGENT]` Security docs adapted for ADB/SMS; expand `.gitignore`
7. 🔲 `[AGENT]` `git init` + push public `takein-sms` remote
8. ✅ `[AUTO]` pytest smoke + ruff on app modules (local)
9. 🔲 `[HUMAN]` Enable Dependabot alerts + private vulnerability reporting on GitHub

### Sprint 1 — Product hardening (post-alignment)

10. 🔲 `[AGENT]` Add minimal pytest smoke (convert sample HTML / dry-run parse)
11. 🔲 `[AGENT]` Pin dependencies more strictly (`uv.lock` or hashed requirements) when ready
12. 🔲 `[AGENT]` Document Winget/Release packaging path (no release-please until requested)

### Human & device (after automation)

13. 🔲 `[ADB]` GUI smoke on rooted Lineage device (prefer dry-run unless human requests live import)
14. 🔲 `[HUMAN]` Branch protection on `main` (CI required) when comfortable
15. 🔲 `[HUMAN]` Optional: CodeQL / Scorecard / release-please later

---

## Parallel (after Sequential items 3–7)

- 🔲 `[AGENT]` Refresh `TEMPLATE_INDEX.json` for this repo’s files
- 🔲 `[AGENT]` README “How agents should work here”
- 🔲 `[AGENT]` `THIRD_PARTY_LICENSES.md` note for bundled Android platform-tools
- 🔲 `[AGENT]` Project-specific ADB destructive-ops note in rules or `docs/RUNBOOK.md`

---

## Completed product baseline (archived detail in COMPLETED_TASKS.md)

- ✅ `[AGENT]` Google Voice HTML → SMS Backup & Restore XML converter
- ✅ `[AGENT]` Root `adb` sqlite importer with backup + verification
- ✅ `[AGENT]` TakeIn SMS CustomTkinter GUI + PyInstaller packaging
