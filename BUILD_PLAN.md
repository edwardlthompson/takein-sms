# Build Plan

<!-- remaining-tally -->
**Remaining:** (tally on next sync)
<!-- /remaining-tally -->

Live board. Canonical shape: agent-project-bootstrap `BUILD_PLAN_TEMPLATE.md`.
Finished work: [`COMPLETED_TASKS.md`](COMPLETED_TASKS.md).

**Who:** `AGENT` code · `HUMAN` person · `ADB` device · `AUTO` CI/scripts
**Venue (AGENT only):** `[LOCAL]` This Computer · `[CLOUD]` Cursor Cloud
**State:** 🔲 open · ✅ done · ❌ blocked

Format: `🔲 [AGENT][LOCAL] Short task — scope: path/prefix`.

### Open PRs (synced)

> Auto-managed. Do not hand-edit inside the markers.

<!-- open-prs-sync:begin -->
_No open Dependabot or Release Please PRs._
<!-- open-prs-sync:end -->

### Template gaps (synced)

> Auto-managed. Do not hand-edit inside the markers.

<!-- template-gaps-sync:begin -->
_No template gaps._
<!-- template-gaps-sync:end -->

### Waiting on a person

1. 🔲 `[HUMAN]` Enable Dependabot alerts + private vulnerability reporting on GitHub (H-001 / F-006)
2. 🔲 `[HUMAN]` Review Dependabot PR bumping github-actions (F-007)
3. 🔲 `[ADB]` GUI smoke on rooted Lineage device (prefer dry-run unless human requests live import)
4. 🔲 `[HUMAN]` Branch protection on `main` (CI required) when comfortable
5. 🔲 `[HUMAN]` Optional: CodeQL / Scorecard / release-please workflows later (F-010)

### Local agent (This Computer)

Standing queue for This Computer. Rows: `🔲 [AGENT][LOCAL] … — scope: path`.

<!-- local-agent-lane:begin -->
**Status:** 🔲 open · ✅ done · ❌ blocked
<!-- local-agent-lane:end -->

### Cloud agent (Cursor Cloud)

Standing queue for Cursor Cloud. Rows: `🔲 [AGENT][CLOUD] … — scope: path`.

<!-- cloud-agent-lane:begin -->
_No cloud agent items._
<!-- cloud-agent-lane:end -->

## Child Repo Playbook

### Sprint News — News Bot follow-ups

<!-- parallel_exception: independent news follow-ups; run sequentially -->

_No open news tasks._


## Archive

Older sprints: [`COMPLETED_TASKS.md`](COMPLETED_TASKS.md).

## Preserved source board

Quoted so no prior task is lost. Prefer the lanes above; do not invent work.

<details>
<summary>Previous board</summary>

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

</details>
