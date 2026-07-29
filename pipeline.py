#!/usr/bin/env python3
"""Orchestrate TakeIn SMS convert → import → verification."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from adb_util import AdbClient, AdbDevice, find_adb
from convert_gvoice import convert_paths_to_xml
from import_gvoice_adb import ImportResult, run_import

LogCb = Callable[[str], None]
ProgressCb = Callable[[str, int, int, int], None]


@dataclass
class PipelineResult:
    mode: str  # "root" | "xml_only"
    message_count: int
    xml_path: Path
    stats: dict[str, int] = field(default_factory=dict)
    import_result: ImportResult | None = None
    remote_xml: str | None = None
    instructions: str = ""


def get_device_status(
    adb_path: str | None = None,
) -> tuple[str | None, list[AdbDevice], str]:
    """
    Returns (adb_path, devices, error_message).
    Devices are enriched when state == device.
    """
    path = adb_path or find_adb()
    if not path:
        return None, [], "adb not found. Place platform-tools under vendor/ or install ADB on PATH."
    try:
        client = AdbClient(path)
        devices = client.list_devices()
    except Exception as exc:  # noqa: BLE001
        return path, [], str(exc)

    enriched: list[AdbDevice] = []
    for d in devices:
        if d.state == "device":
            try:
                enriched.append(client.enrich_device(d))
            except Exception:  # noqa: BLE001
                enriched.append(d)
        else:
            enriched.append(d)
    return path, enriched, ""


def run_pipeline(
    inputs: list[Path],
    *,
    work_dir: Path,
    prefer_root_import: bool = True,
    push_xml_if_no_root: bool = True,
    dry_run: bool = False,
    adb_path: str | None = None,
    serial: str | None = None,
    progress_cb: ProgressCb | None = None,
    log_cb: LogCb | None = None,
) -> PipelineResult:
    """
    Convert Takeout sources to XML, then either root-import or export/push XML.
    """
    work_dir = Path(work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    xml_path = work_dir / "gvoice_sms.xml"

    def log(msg: str) -> None:
        if log_cb:
            log_cb(msg)
        else:
            print(msg)

    log("[TakeIn SMS] Converting Google Voice Takeout…")
    messages, stats = convert_paths_to_xml(
        inputs,
        xml_path,
        progress_cb=progress_cb,
        log_cb=log_cb,
    )

    adb = adb_path or find_adb()
    rooted = False
    if prefer_root_import and adb:
        try:
            client = AdbClient(adb)
            devices = [d for d in client.list_devices() if d.state == "device"]
            if not devices:
                log("[warn] No authorized ADB device; exporting XML only.")
            else:
                use_serial = serial or devices[0].serial
                rooted = client.probe_root(use_serial)
                if rooted and not dry_run:
                    log("[TakeIn SMS] Root available — importing into native SMS DB…")
                    result = run_import(
                        xml_path,
                        backup_dir=work_dir / "backups",
                        sql_out=work_dir / "gvoice_import.sql",
                        dry_run=False,
                        adb_path=adb,
                        serial=use_serial,
                        progress_cb=progress_cb,
                        log_cb=log_cb,
                    )
                    verify = (
                        f"Verification: before={result.before}, after={result.after}, "
                        f"delta={result.delta}, expected={result.expected}"
                    )
                    log(f"[ok] {verify}")
                    if result.backup_path:
                        log(f"[ok] DB backup: {result.backup_path}")
                    return PipelineResult(
                        mode="root",
                        message_count=len(messages),
                        xml_path=xml_path,
                        stats=stats,
                        import_result=result,
                        instructions=(
                            "Import complete. Open Google Messages to confirm threads, "
                            "then open Cloze Pro (or your CRM) to reindex SMS."
                        ),
                    )
                if rooted and dry_run:
                    log("[dry-run] Would import via adb root.")
                    result = run_import(
                        xml_path,
                        backup_dir=work_dir / "backups",
                        sql_out=work_dir / "gvoice_import.sql",
                        dry_run=True,
                        adb_path=adb,
                        serial=use_serial,
                        progress_cb=progress_cb,
                        log_cb=log_cb,
                    )
                    return PipelineResult(
                        mode="root",
                        message_count=len(messages),
                        xml_path=xml_path,
                        stats=stats,
                        import_result=result,
                        instructions="Dry run only — no device changes.",
                    )
                log("[info] Device is not rooted via adb. Using XML export path.")
        except Exception as exc:  # noqa: BLE001
            log(f"[warn] Root import unavailable: {exc}")

    remote = None
    if push_xml_if_no_root and adb:
        try:
            client = AdbClient(adb)
            devices = [d for d in client.list_devices() if d.state == "device"]
            if devices and not dry_run:
                use_serial = serial or devices[0].serial
                remote = "/sdcard/Download/gvoice_sms.xml"
                client.push(xml_path, remote, serial=use_serial)
                log(f"[ok] Pushed XML to phone: {remote}")
        except Exception as exc:  # noqa: BLE001
            log(f"[warn] Could not push XML: {exc}")

    instructions = (
        "XML ready for SMS Backup & Restore:\n"
        f"  Local: {xml_path}\n" + (f"  On phone: {remote}\n" if remote else "") + "\nNext steps:\n"
        "1. Install SMS Backup & Restore on the phone.\n"
        "2. Open Restore and select gvoice_sms.xml.\n"
        "3. Temporarily allow it as the default SMS app when prompted.\n"
        "4. When finished, switch the default SMS app back to Messages.\n"
        "5. Open Cloze Pro (or your CRM) to reindex SMS."
    )
    log(instructions)
    return PipelineResult(
        mode="xml_only",
        message_count=len(messages),
        xml_path=xml_path,
        stats=stats,
        remote_xml=remote,
        instructions=instructions,
    )
