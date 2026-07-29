#!/usr/bin/env python3
"""ADB discovery, device listing, and root probing for TakeIn SMS."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


def app_base_dir() -> Path:
    """Directory containing the app (or PyInstaller bundle root)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def find_adb() -> str | None:
    """Locate adb.exe: bundled vendor/platform-tools, then PATH."""
    base = app_base_dir()
    candidates = [
        base / "vendor" / "platform-tools" / "adb.exe",
        base / "platform-tools" / "adb.exe",
        Path(sys.executable).resolve().parent / "vendor" / "platform-tools" / "adb.exe",
    ]
    # When frozen as one-folder, also check next to the exe
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        candidates.insert(0, exe_dir / "vendor" / "platform-tools" / "adb.exe")
        candidates.insert(1, exe_dir / "adb.exe")

    for path in candidates:
        if path.is_file():
            return str(path)

    which = shutil.which("adb")
    if which:
        return which
    return None


@dataclass
class AdbDevice:
    serial: str
    state: str  # device, unauthorized, offline, ...
    model: str = ""
    product: str = ""
    android_version: str = ""
    sdk: str = ""
    rooted: bool | None = None
    sms_role: str = ""


class AdbClient:
    def __init__(self, adb_path: str | None = None) -> None:
        self.adb_path = adb_path or find_adb()
        if not self.adb_path:
            raise FileNotFoundError(
                "adb not found. Install Android platform-tools or place adb under vendor/platform-tools/."
            )

    def run(
        self,
        args: list[str],
        *,
        check: bool = True,
        text: bool = True,
        timeout: float | None = 120,
    ) -> subprocess.CompletedProcess:
        cmd = [self.adb_path, *args]
        # Ensure adb's directory is on PATH so AdbWinApi.dll resolves on Windows
        env = os.environ.copy()
        adb_dir = str(Path(self.adb_path).resolve().parent)
        env["PATH"] = adb_dir + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=text,
            timeout=timeout,
            env=env,
        )
        if check and result.returncode != 0:
            stderr = result.stderr if text else result.stderr.decode("utf-8", "replace")
            stdout = result.stdout if text else result.stdout.decode("utf-8", "replace")
            raise RuntimeError(
                f"adb {' '.join(args)} failed ({result.returncode})\n"
                f"stdout: {stdout}\nstderr: {stderr}"
            )
        return result

    def shell(self, command: str, *, check: bool = True, timeout: float | None = 120) -> str:
        result = self.run(["shell", command], check=check, timeout=timeout)
        return (result.stdout or "").strip()

    def list_devices(self) -> list[AdbDevice]:
        result = self.run(["devices", "-l"], check=False)
        devices: list[AdbDevice] = []
        for line in (result.stdout or "").splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            serial, state = parts[0], parts[1]
            meta: dict[str, str] = {}
            for token in parts[2:]:
                if ":" in token:
                    k, v = token.split(":", 1)
                    meta[k] = v
            devices.append(
                AdbDevice(
                    serial=serial,
                    state=state,
                    model=meta.get("model", "").replace("_", " "),
                    product=meta.get("product", ""),
                )
            )
        return devices

    def enrich_device(self, device: AdbDevice) -> AdbDevice:
        if device.state != "device":
            return device

        # Prefer -s serial for multi-device safety
        def shell_s(cmd: str) -> str:
            r = self.run(["-s", device.serial, "shell", cmd], check=False)
            return (r.stdout or "").strip()

        device.android_version = shell_s("getprop ro.build.version.release")
        device.sdk = shell_s("getprop ro.build.version.sdk")
        if not device.model:
            device.model = shell_s("getprop ro.product.model")
        device.sms_role = shell_s("cmd role get-role-holders android.app.role.SMS")
        device.rooted = self.probe_root(device.serial)
        return device

    def probe_root(self, serial: str | None = None) -> bool:
        prefix = ["-s", serial] if serial else []
        self.run([*prefix, "root"], check=False, timeout=30)
        time.sleep(0.8)
        for _ in range(8):
            r = self.run([*prefix, "shell", "id -u"], check=False, timeout=15)
            if (r.stdout or "").strip() == "0":
                return True
            time.sleep(0.4)
        return False

    def ensure_root(self, serial: str | None = None) -> None:
        if not self.probe_root(serial):
            raise RuntimeError(
                "Could not obtain adb root (uid=0). "
                "One-click import requires a rooted device with adb root (e.g. LineageOS)."
            )

    def push(self, local: Path | str, remote: str, serial: str | None = None) -> None:
        prefix = ["-s", serial] if serial else []
        self.run([*prefix, "push", str(local), remote])

    def pull(self, remote: str, local: Path | str, serial: str | None = None) -> None:
        prefix = ["-s", serial] if serial else []
        self.run([*prefix, "pull", remote, str(local)], check=False)
