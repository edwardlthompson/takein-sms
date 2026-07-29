#!/usr/bin/env python3
"""Convert Google Voice Takeout HTML text exports to SMS Backup & Restore XML."""

from __future__ import annotations

import argparse
import html
import re
import sys
import zipfile
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ProgressCb = Callable[[str, int, int, int], None]  # phase, done, total, messages

MESSAGE_SPLIT_RE = re.compile(r'<div class="message">', re.IGNORECASE)
DT_RE = re.compile(
    r'<abbr class="dt"[^>]*\btitle="([^"]+)"',
    re.IGNORECASE,
)
SENDER_FN_RE = re.compile(
    r'<cite class="sender[^"]*">.*?(?:<abbr class="fn"[^>]*>(.*?)</abbr>|<span class="fn"[^>]*>(.*?)</span>)',
    re.DOTALL | re.IGNORECASE,
)
BODY_RE = re.compile(r"<q>(.*?)</q>", re.DOTALL | re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")
FILENAME_ADDR_RE = re.compile(r"^(\+?\d+)\s+-\s+Text\s+-", re.IGNORECASE)
FILENAME_CONTACT_RE = re.compile(r"^(.+?)\s+-\s+Text\s+-", re.IGNORECASE)
TEXT_HTML_NAME_RE = re.compile(r".+ - Text - .+\.html$", re.IGNORECASE)
TEL_HREF_RE = re.compile(r'href="tel:([^"]+)"', re.IGNORECASE)
ME_TEL_RE = re.compile(
    r'href="tel:([^"]+)"[^>]*>\s*<abbr class="fn"[^>]*>\s*Me\s*</abbr>',
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class SmsMessage:
    address: str
    date_ms: int
    type_: int  # 1=received, 2=sent
    body: str
    contact_name: str

    @property
    def dedupe_key(self) -> tuple[str, int, int, str]:
        return (self.address, self.date_ms, self.type_, self.body)


def parse_iso_to_ms(value: str) -> int | None:
    raw = value.strip()
    if not raw:
        return None
    # Google Voice uses offsets like -04:00; fromisoformat handles these on 3.11+
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        # Tolerate trailing Z
        if raw.endswith("Z"):
            try:
                dt = datetime.fromisoformat(raw[:-1] + "+00:00")
            except ValueError:
                return None
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return int(dt.timestamp() * 1000)


def strip_html_to_text(fragment: str) -> str:
    text = fragment.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    # Normalize NBSP / narrow no-break space variants
    text = text.replace("\u00a0", " ").replace("\u202f", " ")
    return text.strip()


def normalize_address(addr: str) -> str:
    addr = addr.strip()
    if not addr:
        return addr
    if not addr.startswith("+") and re.fullmatch(r"\d+", addr):
        addr = "+" + addr
    return addr


def address_from_filename(name: str) -> str | None:
    m = FILENAME_ADDR_RE.match(Path(name).name)
    if not m:
        return None
    return normalize_address(m.group(1))


def contact_name_from_filename(name: str) -> str | None:
    m = FILENAME_CONTACT_RE.match(Path(name).name)
    if not m:
        return None
    label = m.group(1).strip()
    if FILENAME_ADDR_RE.match(Path(name).name):
        return None
    return label or None


def address_from_html(content: str) -> str | None:
    """Pick the first non-Me tel: href as the conversation peer address."""
    me_numbers = {normalize_address(m) for m in ME_TEL_RE.findall(content)}
    for raw in TEL_HREF_RE.findall(content):
        addr = normalize_address(raw)
        if not addr:
            continue
        if addr in me_numbers:
            continue
        # Also skip if this tel is only attached to Me in a looser way
        return addr
    # Fallback: any tel not looking like the dominant Me number
    counts: dict[str, int] = {}
    for raw in TEL_HREF_RE.findall(content):
        addr = normalize_address(raw)
        if addr:
            counts[addr] = counts.get(addr, 0) + 1
    if not counts:
        return None
    # Prefer numbers that appear with a non-Me fn nearby: already handled above.
    # Last resort: least-associated with Me label — use least frequent if multiple Me.
    if me_numbers:
        for addr, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
            if addr not in me_numbers:
                return addr
    return max(counts.items(), key=lambda kv: kv[1])[0]


def parse_messages_from_html(content: str, address: str) -> list[SmsMessage]:
    messages: list[SmsMessage] = []
    # Split on message starts so nested <div> (MMS images) do not truncate early.
    parts = MESSAGE_SPLIT_RE.split(content)
    blocks = parts[1:] if len(parts) > 1 else []

    for block in blocks:
        dt_m = DT_RE.search(block)
        if not dt_m:
            continue
        date_ms = parse_iso_to_ms(dt_m.group(1))
        if date_ms is None:
            continue

        fn_m = SENDER_FN_RE.search(block)
        fn = ""
        if fn_m:
            fn = (fn_m.group(1) or fn_m.group(2) or "").strip()
            fn = html.unescape(TAG_RE.sub("", fn)).strip()

        body_m = BODY_RE.search(block)
        body = strip_html_to_text(body_m.group(1)) if body_m else ""

        is_me = fn.lower() == "me"
        type_ = 2 if is_me else 1
        contact_name = "(Unknown)" if is_me or not fn else fn

        messages.append(
            SmsMessage(
                address=address,
                date_ms=date_ms,
                type_=type_,
                body=body,
                contact_name=contact_name,
            )
        )
    return messages


def _log(msg: str, log_cb: Callable[[str], None] | None) -> None:
    if log_cb:
        log_cb(msg)
    else:
        print(msg)


def iter_text_html_from_dir(
    root: Path,
    log_cb: Callable[[str], None] | None = None,
) -> Iterator[tuple[str, str, str]]:
    """Yield (source_label, filename, html_text)."""
    if not root.exists():
        _log(f"[warn] path not found: {root}", log_cb)
        return
    count = 0
    for path in root.rglob("*.html"):
        if not TEXT_HTML_NAME_RE.match(path.name):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            _log(f"[warn] cannot read {path}: {exc}", log_cb)
            continue
        count += 1
        yield (str(root), path.name, text)
    _log(f"[info] {root}: {count} Text HTML file(s)", log_cb)


def iter_text_html_from_zip(
    zip_path: Path,
    log_cb: Callable[[str], None] | None = None,
) -> Iterator[tuple[str, str, str]]:
    if not zip_path.exists():
        _log(f"[warn] zip not found: {zip_path}", log_cb)
        return
    count = 0
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for info in zf.infolist():
                name = Path(info.filename).name
                if not TEXT_HTML_NAME_RE.match(name):
                    continue
                try:
                    raw = zf.read(info)
                    text = raw.decode("utf-8", errors="replace")
                except Exception as exc:  # noqa: BLE001
                    _log(f"[warn] cannot read zip entry {info.filename}: {exc}", log_cb)
                    continue
                count += 1
                yield (str(zip_path), name, text)
    except zipfile.BadZipFile as exc:
        _log(f"[warn] bad zip {zip_path}: {exc}", log_cb)
        return
    _log(f"[info] {zip_path}: {count} Text HTML file(s)", log_cb)


def collect_from_paths(
    paths: Iterable[Path],
    *,
    progress_cb: ProgressCb | None = None,
    log_cb: Callable[[str], None] | None = None,
) -> tuple[list[SmsMessage], dict[str, int]]:
    seen_files: set[str] = set()  # basename dedupe across overlapping dir/zip
    messages: list[SmsMessage] = []
    stats = {
        "sources": 0,
        "files_seen": 0,
        "files_skipped_dup": 0,
        "files_no_address": 0,
        "messages": 0,
        "messages_deduped": 0,
    }
    dedupe: set[tuple[str, int, int, str]] = set()
    path_list = list(paths)

    # Rough total for progress (unique basenames unknown until scan)
    estimated_total = 0
    for path in path_list:
        if path.is_file() and path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    estimated_total += sum(
                        1
                        for info in zf.infolist()
                        if TEXT_HTML_NAME_RE.match(Path(info.filename).name)
                    )
            except zipfile.BadZipFile:
                pass
        elif path.is_dir():
            estimated_total += sum(
                1 for p in path.rglob("*.html") if TEXT_HTML_NAME_RE.match(p.name)
            )
        elif path.is_file() and TEXT_HTML_NAME_RE.match(path.name):
            estimated_total += 1

    unique_processed = 0

    for path in path_list:
        stats["sources"] += 1
        if path.is_file() and path.suffix.lower() == ".zip":
            iterator = iter_text_html_from_zip(path, log_cb=log_cb)
        elif path.is_dir():
            iterator = iter_text_html_from_dir(path, log_cb=log_cb)
        elif path.is_file() and TEXT_HTML_NAME_RE.match(path.name):
            text = path.read_text(encoding="utf-8", errors="replace")
            iterator = iter([(str(path.parent), path.name, text)])
            _log(f"[info] {path}: 1 Text HTML file(s)", log_cb)
        elif path.exists():
            _log(
                f"[warn] unsupported path (need dir, .zip, or Text HTML): {path}",
                log_cb,
            )
            continue
        else:
            _log(f"[warn] path not found: {path}", log_cb)
            continue

        for source, filename, content in iterator:
            stats["files_seen"] += 1
            if filename in seen_files:
                stats["files_skipped_dup"] += 1
                continue
            seen_files.add(filename)
            unique_processed += 1

            address = address_from_filename(filename) or address_from_html(content)
            if not address:
                stats["files_no_address"] += 1
                continue

            parsed = parse_messages_from_html(content, address)
            file_contact = contact_name_from_filename(filename)
            contact = file_contact or next(
                (m.contact_name for m in parsed if m.contact_name != "(Unknown)"),
                "(Unknown)",
            )
            for msg in parsed:
                key = msg.dedupe_key
                if key in dedupe:
                    stats["messages_deduped"] += 1
                    continue
                dedupe.add(key)
                if msg.contact_name == "(Unknown)" and contact != "(Unknown)":
                    msg = SmsMessage(
                        address=msg.address,
                        date_ms=msg.date_ms,
                        type_=msg.type_,
                        body=msg.body,
                        contact_name=contact,
                    )
                messages.append(msg)
                stats["messages"] += 1

            if progress_cb:
                progress_cb(
                    "convert",
                    unique_processed,
                    max(estimated_total, unique_processed),
                    stats["messages"],
                )
            _ = source

    messages.sort(key=lambda m: (m.date_ms, m.address, m.type_))
    return messages, stats


def convert_paths_to_xml(
    inputs: Iterable[Path],
    output: Path,
    *,
    progress_cb: ProgressCb | None = None,
    log_cb: Callable[[str], None] | None = None,
) -> tuple[list[SmsMessage], dict[str, int]]:
    """Convert Takeout inputs to SMS Backup & Restore XML. Raises ValueError if empty."""
    messages, stats = collect_from_paths(inputs, progress_cb=progress_cb, log_cb=log_cb)
    if not messages:
        raise ValueError(f"no messages parsed; stats={stats}")
    output.parent.mkdir(parents=True, exist_ok=True)
    write_sms_xml(messages, output)
    sent = sum(1 for m in messages if m.type_ == 2)
    recv = sum(1 for m in messages if m.type_ == 1)
    _log(
        f"[ok] wrote {output} with {len(messages)} messages ({recv} received, {sent} sent)",
        log_cb,
    )
    _log(
        "[summary] "
        f"sources={stats['sources']} "
        f"files_seen={stats['files_seen']} "
        f"files_skipped_dup={stats['files_skipped_dup']} "
        f"files_no_address={stats['files_no_address']} "
        f"messages={stats['messages']} "
        f"messages_deduped={stats['messages_deduped']}",
        log_cb,
    )
    return messages, stats


def readable_date(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000.0, tz=UTC)
    return dt.strftime("%b %d, %Y %I:%M:%S %p UTC")


def write_sms_xml(messages: list[SmsMessage], out_path: Path) -> None:
    backup_date = int(datetime.now(tz=UTC).timestamp() * 1000)
    lines = [
        "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>",
        f'<smses count="{len(messages)}" backup_date="{backup_date}" type="full">',
    ]
    for msg in messages:
        body = xml_escape(msg.body, {'"': "&quot;", "'": "&apos;"})
        contact = xml_escape(msg.contact_name, {'"': "&quot;", "'": "&apos;"})
        address = xml_escape(msg.address, {'"': "&quot;", "'": "&apos;"})
        rdate = xml_escape(readable_date(msg.date_ms), {'"': "&quot;", "'": "&apos;"})
        lines.append(
            "<sms "
            'protocol="0" '
            f'address="{address}" '
            f'date="{msg.date_ms}" '
            f'type="{msg.type_}" '
            'subject="null" '
            f'body="{body}" '
            'toa="null" '
            'sc_toa="null" '
            'service_center="null" '
            'read="1" '
            'status="-1" '
            'locked="0" '
            'date_sent="0" '
            f'readable_date="{rdate}" '
            f'contact_name="{contact}" '
            "/>"
        )
    lines.append("</smses>")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Convert Google Voice Takeout Text HTML to SMS Backup & Restore XML."
    )
    p.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output XML path (e.g. gvoice_sms.xml)",
    )
    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Input directories and/or .zip archives containing Voice Text HTML",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        convert_paths_to_xml(args.inputs, args.output)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
