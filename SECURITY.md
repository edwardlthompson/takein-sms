# Security Policy — TakeIn SMS

## Supported Versions

| Version | Supported |
| ------- | --------- |
| latest `main` | yes |
| older local builds | best-effort |

Template alignment version: see `.template-version`.

## Threat Model (product-specific)

TakeIn SMS processes **private SMS/chat history** from Google Takeout and can write the Android telephony SMS database when `adb root` is available.

Risks:

- Accidental or malicious import of forged XML into a rooted device
- Leakage of Takeout/XML/DB backups via git or cloud sync
- USB debugging / `adb root` exposure on an unlocked machine

Mitigations:

- Back up `mmssms.db` before live import
- Idempotent inserts; prefer dry-run in agent sessions
- Gitignore sensitive artifacts; never commit Takeout data
- MIT FOSS; no telemetry

See also `docs/THREAT_MODEL.md`, `docs/PRIVACY.md`, `docs/SECURITY_TRIAGE.md`.

## Reporting a Vulnerability

**Do not** open public GitHub issues for security vulnerabilities.

1. Use GitHub **Private vulnerability reporting**, or
2. Contact the maintainers listed in `.github/CODEOWNERS` with description, repro, impact, and suggested fix.

## Response Timeline

| Stage | Target |
|-------|--------|
| Acknowledgment | 3 business days |
| Initial assessment | 7 business days |
| Fix or mitigation plan | 30 days (severity-dependent) |

## Security Practices

- Dependabot alerts + weekly triage: `docs/SECURITY_TRIAGE.md`
- Lean CI + dependency-review on PRs
- Secrets must never be committed
- Live SMS DB mutation requires explicit human/`[ADB]` approval
