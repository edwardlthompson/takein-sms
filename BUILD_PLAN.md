# BUILD_PLAN — TakeIn SMS

**Labels:** `[AGENT]` `[HUMAN]` `[ADB]` `[AUTO]`  
**Status:** 🔲 open · ✅ done · ❌ blocked  
**Rule:** Finish Sequential before starting Parallel. Human/device items wait until automation is green.

> **Audit sprint — 2026-07-29** archived in COMPLETED_TASKS.md.

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

### Human & device (after automation)

1. 🔲 `[HUMAN]` Enable Dependabot alerts + private vulnerability reporting on GitHub (H-001 / F-006)
2. 🔲 `[HUMAN]` Review Dependabot PR bumping github-actions (F-007)
3. 🔲 `[ADB]` GUI smoke on rooted Lineage device (prefer dry-run unless human requests live import)
4. 🔲 `[HUMAN]` Branch protection on `main` (CI required) when comfortable
5. 🔲 `[HUMAN]` Optional: CodeQL / Scorecard / release-please workflows later (F-010)

---

## Parallel

_(none open — TEMPLATE_INDEX refreshed during audit)_

---

## Archived Sprints

| Sprint | Complete | Archive |
|--------|----------|---------|
| Sprint 0 — Bootstrap alignment | 2026-07-29 | COMPLETED_TASKS.md |
| Audit sprint — 2026-07-29 | 2026-07-29 | COMPLETED_TASKS.md |
