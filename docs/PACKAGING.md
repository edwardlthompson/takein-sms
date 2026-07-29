# Packaging — TakeIn SMS

## Windows (current)

```powershell
.\build.ps1
```

Output: `dist\TakeInSMS\TakeInSMS.exe` (one-folder build with bundled `adb` under `_internal\vendor\platform-tools\`).

GitHub Releases: attach the `dist\TakeInSMS\` zip when cutting a version. Prefer Conventional Commits; optional release-please can be enabled later (`[HUMAN]`).

## Winget (future)

When ready to publish:

1. Publish a GitHub Release with a portable zip or installer.
2. Add a manifest under `manifests/e/EdwardLThompson/TakeInSMS/` (or community PR to microsoft/winget-pkgs).
3. Point `InstallerUrl` at the Release asset; keep MIT license URL to this repo.

No release-please automation is enabled yet (lean CI policy).
