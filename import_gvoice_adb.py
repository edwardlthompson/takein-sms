#!/usr/bin/env python3
"""Import SMS Backup & Restore XML into Android mmssms.db via adb root + sqlite3."""

from __future__ import annotations

import argparse
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from adb_util import AdbClient, find_adb

DB_DIR = "/data/data/com.android.providers.telephony/databases"
DB_PATH = f"{DB_DIR}/mmssms.db"
REMOTE_SQL = "/data/local/tmp/gvoice_import.sql"
REMOTE_DB_COPY = "/data/local/tmp/mmssms_gvoice_work.db"

LogCb = Callable[[str], None]
ProgressCb = Callable[[str, int, int, int], None]


@dataclass
class SmsRow:
    address: str
    date_ms: int
    type_: int
    body: str


@dataclass
class ImportResult:
    before: int
    after: int
    delta: int
    expected: int
    backup_path: Path | None
    sql_path: Path
    rooted: bool = True


def _log(msg: str, log_cb: LogCb | None) -> None:
    if log_cb:
        log_cb(msg)
    else:
        print(msg)


def parse_xml(xml_path: Path) -> list[SmsRow]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    rows: list[SmsRow] = []
    for el in root.findall("sms"):
        address = (el.get("address") or "").strip()
        date_s = el.get("date") or ""
        type_s = el.get("type") or "1"
        body = el.get("body") or ""
        if not address or not date_s:
            continue
        try:
            date_ms = int(date_s)
            type_ = int(type_s)
        except ValueError:
            continue
        rows.append(SmsRow(address=address, date_ms=date_ms, type_=type_, body=body))
    return rows


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def detect_sub_id(client: AdbClient, serial: str | None = None) -> int:
    prefix = ["-s", serial] if serial else []
    out = (
        client.run(
            [
                *prefix,
                "shell",
                f'sqlite3 {DB_PATH} "SELECT sub_id, COUNT(*) AS c FROM sms '
                f'GROUP BY sub_id ORDER BY c DESC LIMIT 1;"',
            ],
            check=False,
        ).stdout
        or ""
    )
    out = out.strip()
    if not out:
        return 1
    part = out.split("|", 1)[0].strip()
    try:
        return int(part)
    except ValueError:
        return 1


def sms_count(client: AdbClient, serial: str | None = None) -> int:
    prefix = ["-s", serial] if serial else []
    out = (
        client.run(
            [*prefix, "shell", f'sqlite3 {DB_PATH} "SELECT COUNT(*) FROM sms;"'],
            check=False,
        ).stdout
        or ""
    ).strip()
    return int(out or "0")


def stop_providers(client: AdbClient, serial: str | None = None) -> None:
    prefix = ["-s", serial] if serial else []
    for cmd in (
        "am force-stop com.google.android.apps.messaging",
        "am force-stop com.android.providers.telephony",
        "kill $(pidof com.android.providers.telephony) 2>/dev/null || true",
    ):
        client.run([*prefix, "shell", cmd], check=False)
    time.sleep(1)


def start_providers(client: AdbClient, serial: str | None = None) -> None:
    prefix = ["-s", serial] if serial else []
    client.run(
        [
            *prefix,
            "shell",
            "am start -a android.intent.action.MAIN "
            "-c android.intent.category.LAUNCHER "
            "com.google.android.apps.messaging/.ui.ConversationListActivity",
        ],
        check=False,
    )


def backup_db(
    client: AdbClient,
    backup_dir: Path,
    serial: str | None = None,
    log_cb: LogCb | None = None,
) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    dest = backup_dir / f"mmssms_{stamp}"
    dest.mkdir(parents=True, exist_ok=True)

    prefix = ["-s", serial] if serial else []
    client.run(
        [*prefix, "shell", f'sqlite3 {DB_PATH} "PRAGMA wal_checkpoint(FULL);"'],
        check=False,
    )
    listing = client.run([*prefix, "shell", f"ls -1 {DB_DIR}"], check=False).stdout or ""
    for name in listing.splitlines():
        name = name.strip()
        if not name.startswith("mmssms.db"):
            continue
        local = dest / name
        client.run([*prefix, "pull", f"{DB_DIR}/{name}", str(local)], check=False)
    if not (dest / "mmssms.db").exists():
        raise RuntimeError(f"Failed to pull mmssms.db into {dest}")
    _log(f"[ok] backed up DB to {dest}", log_cb)
    return dest


def build_import_sql(rows: list[SmsRow], sub_id: int) -> str:
    lines = [
        "PRAGMA busy_timeout=60000;",
        "BEGIN IMMEDIATE;",
    ]
    by_address: dict[str, list[SmsRow]] = {}
    for row in rows:
        by_address.setdefault(row.address, []).append(row)

    for address, msgs in by_address.items():
        addr_sql = sql_quote(address)
        lines.append(
            "INSERT INTO canonical_addresses(address, sub_id) "
            f"SELECT {addr_sql}, {sub_id} "
            f"WHERE NOT EXISTS (SELECT 1 FROM canonical_addresses WHERE address={addr_sql});"
        )
        lines.append(
            "INSERT INTO threads(date, message_count, recipient_ids, snippet, read, sub_id) "
            f"SELECT 0, 0, "
            f"(SELECT _id FROM canonical_addresses WHERE address={addr_sql} LIMIT 1), "
            f"'', 1, {sub_id} "
            "WHERE NOT EXISTS ("
            "  SELECT 1 FROM threads "
            "  WHERE recipient_ids = CAST("
            f"    (SELECT _id FROM canonical_addresses WHERE address={addr_sql} LIMIT 1) AS TEXT"
            "  )"
            ");"
        )
        for msg in msgs:
            body_sql = sql_quote(msg.body)
            lines.append(
                "INSERT INTO sms("
                "thread_id, address, date, date_sent, protocol, read, status, type, "
                "body, locked, sub_id, seen"
                ") "
                "SELECT "
                f"(SELECT _id FROM threads WHERE recipient_ids = CAST("
                f"(SELECT _id FROM canonical_addresses WHERE address={addr_sql} LIMIT 1) AS TEXT) LIMIT 1), "
                f"{addr_sql}, {msg.date_ms}, {msg.date_ms}, 0, 1, -1, {msg.type_}, "
                f"{body_sql}, 0, {sub_id}, 1 "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM sms WHERE "
                f"  address={addr_sql} AND date={msg.date_ms} AND type={msg.type_} "
                f"  AND body={body_sql}"
                ");"
            )

    lines.append("COMMIT;")
    lines.append('SELECT "import_done";')
    return "\n".join(lines) + "\n"


def apply_sql_on_device(client: AdbClient, local_sql: Path, serial: str | None = None) -> None:
    prefix = ["-s", serial] if serial else []
    client.run([*prefix, "push", str(local_sql), REMOTE_SQL])
    client.run([*prefix, "shell", f"cp -f {DB_PATH} {REMOTE_DB_COPY}"], check=False)
    result = client.run(
        [*prefix, "shell", f'sqlite3 {REMOTE_DB_COPY} ".read {REMOTE_SQL}"'],
        check=False,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"sqlite3 import failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    client.run([*prefix, "shell", f"cp -f {REMOTE_DB_COPY} {DB_PATH}"])
    client.run([*prefix, "shell", f"rm -f {DB_PATH}-wal {DB_PATH}-shm"], check=False)
    client.run([*prefix, "shell", f"chmod 660 {DB_PATH}"], check=False)
    client.run([*prefix, "shell", f"chown radio:radio {DB_PATH}"], check=False)
    client.run([*prefix, "shell", f"restorecon {DB_PATH}"], check=False)


def apply_sql_live(client: AdbClient, local_sql: Path, serial: str | None = None) -> str:
    prefix = ["-s", serial] if serial else []
    client.run([*prefix, "push", str(local_sql), REMOTE_SQL])
    client.run(
        [*prefix, "shell", f'sqlite3 {DB_PATH} "PRAGMA wal_checkpoint(FULL);"'],
        check=False,
    )
    result = client.run(
        [*prefix, "shell", f'sqlite3 {DB_PATH} ".read {REMOTE_SQL}"'],
        check=False,
        timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"sqlite3 live import failed\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    client.run([*prefix, "shell", f"chmod 660 {DB_PATH}"], check=False)
    client.run([*prefix, "shell", f"chown radio:radio {DB_PATH}"], check=False)
    client.run([*prefix, "shell", f"restorecon {DB_PATH}"], check=False)
    return (result.stdout or "").strip()


def run_import(
    xml_path: Path,
    *,
    backup_dir: Path | None = None,
    sql_out: Path | None = None,
    dry_run: bool = False,
    adb_path: str | None = None,
    serial: str | None = None,
    progress_cb: ProgressCb | None = None,
    log_cb: LogCb | None = None,
) -> ImportResult:
    """Import XML into device SMS DB. Requires adb root."""
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML not found: {xml_path}")

    base = Path(__file__).resolve().parent
    backup_dir = Path(backup_dir or (base / "backups"))
    sql_out = Path(sql_out or (base / "gvoice_import.sql"))

    if progress_cb:
        progress_cb("import", 0, 5, 0)

    rows = parse_xml(xml_path)
    _log(f"[info] parsed {len(rows)} SMS rows from {xml_path}", log_cb)
    if not rows:
        raise ValueError("no SMS rows to import")

    client = AdbClient(adb_path or find_adb())
    client.ensure_root(serial)
    if progress_cb:
        progress_cb("import", 1, 5, len(rows))

    before = sms_count(client, serial)
    sub_id = detect_sub_id(client, serial)
    _log(f"[info] device sms count before={before}, using sub_id={sub_id}", log_cb)

    sql = build_import_sql(rows, sub_id=sub_id)
    sql_out.write_text(sql, encoding="utf-8")
    _log(f"[ok] wrote SQL ({sql_out.stat().st_size} bytes) -> {sql_out}", log_cb)
    if progress_cb:
        progress_cb("import", 2, 5, len(rows))

    if dry_run:
        _log("[dry-run] skipping device write", log_cb)
        return ImportResult(
            before=before,
            after=before,
            delta=0,
            expected=len(rows),
            backup_path=None,
            sql_path=sql_out,
        )

    backup_path = backup_db(client, backup_dir, serial=serial, log_cb=log_cb)
    if progress_cb:
        progress_cb("import", 3, 5, len(rows))

    stop_providers(client, serial)
    try:
        try:
            out = apply_sql_live(client, sql_out, serial=serial)
            if out:
                _log(out, log_cb)
        except Exception as exc:  # noqa: BLE001
            _log(f"[warn] live import failed ({exc}); trying copy-edit-replace", log_cb)
            stop_providers(client, serial)
            apply_sql_on_device(client, sql_out, serial=serial)
    finally:
        start_providers(client, serial)

    if progress_cb:
        progress_cb("import", 4, 5, len(rows))

    time.sleep(2)
    after = sms_count(client, serial)
    delta = after - before
    _log(f"[ok] device sms count after={after} (delta={delta})", log_cb)
    _log(
        "[next] Open Cloze Pro (or your CRM) so it can index the native SMS database.",
        log_cb,
    )
    if progress_cb:
        progress_cb("import", 5, 5, len(rows))

    return ImportResult(
        before=before,
        after=after,
        delta=delta,
        expected=len(rows),
        backup_path=backup_path,
        sql_path=sql_out,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import gvoice_sms.xml into Android SMS DB via adb root."
    )
    parser.add_argument("xml", type=Path, help="Path to gvoice_sms.xml")
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "backups",
        help="Local directory for mmssms.db backups",
    )
    parser.add_argument(
        "--sql-out",
        type=Path,
        default=Path(__file__).resolve().parent / "gvoice_import.sql",
        help="Where to write generated SQL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse/generate SQL only; do not modify device",
    )
    parser.add_argument("--adb", type=str, default=None, help="Path to adb executable")
    parser.add_argument("--serial", type=str, default=None, help="ADB device serial")
    args = parser.parse_args(argv)

    try:
        result = run_import(
            args.xml,
            backup_dir=args.backup_dir,
            sql_out=args.sql_out,
            dry_run=args.dry_run,
            adb_path=args.adb,
            serial=args.serial,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        return 0
    if result.delta <= 0:
        print(
            "[warn] SMS count did not increase. Messages may already exist, "
            "or inserts were skipped. Check Messages app / SQL errors.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
