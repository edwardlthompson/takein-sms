#!/usr/bin/env python3
"""TakeIn SMS — Windows GUI for Google Voice Takeout → Android SMS."""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from adb_util import find_adb
from pipeline import get_device_status, run_pipeline

APP_NAME = "TakeIn SMS"
APP_TAGLINE = "Google Voice Takeout → Android SMS"
WORK_DIR = Path(__file__).resolve().parent / "output"


class TakeInApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — {APP_TAGLINE}")
        self.geometry("920x720")
        self.minsize(800, 600)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.sources: list[Path] = []
        self.adb_path = find_adb()
        self._busy = False
        self._build_ui()
        self._enable_dnd()
        self.refresh_device()

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text=APP_NAME, font=ctk.CTkFont(size=26, weight="bold")).pack(
            anchor="w"
        )
        ctk.CTkLabel(header, text=APP_TAGLINE, font=ctk.CTkFont(size=14), text_color="gray").pack(
            anchor="w"
        )

        # Device panel
        device = ctk.CTkFrame(self)
        device.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        device.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(device, text="Phone (ADB)", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.device_label = ctk.CTkLabel(device, text="Checking ADB…", justify="left", anchor="w")
        self.device_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        ctk.CTkButton(device, text="Refresh", width=100, command=self.refresh_device).grid(
            row=1, column=1, padx=12, pady=(0, 10)
        )

        # Sources panel
        sources = ctk.CTkFrame(self)
        sources.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        sources.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            sources,
            text="Takeout sources",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 4))

        self.drop_frame = ctk.CTkFrame(sources, height=90, border_width=2)
        self.drop_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=6)
        self.drop_frame.grid_propagate(False)
        self.drop_label = ctk.CTkLabel(
            self.drop_frame,
            text="Drag & drop Google Takeout .zip files here\n(or use Add ZIP / Add Folder)",
            justify="center",
        )
        self.drop_label.place(relx=0.5, rely=0.5, anchor="center")

        btns = ctk.CTkFrame(sources, fg_color="transparent")
        btns.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 8))
        ctk.CTkButton(btns, text="Add ZIP…", command=self.add_zips).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text="Add Folder…", command=self.add_folder).pack(
            side="left", padx=(0, 8)
        )
        ctk.CTkButton(btns, text="Clear", command=self.clear_sources, fg_color="gray").pack(
            side="left"
        )

        self.source_list = ctk.CTkTextbox(sources, height=80)
        self.source_list.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 12))
        self.source_list.configure(state="disabled")

        # Log / progress
        mid = ctk.CTkFrame(self)
        mid.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(mid, text="Activity", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.log_box = ctk.CTkTextbox(mid)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 8))
        self.progress = ctk.CTkProgressBar(mid)
        self.progress.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 4))
        self.progress.set(0)
        self.status_label = ctk.CTkLabel(mid, text="Ready", anchor="w")
        self.status_label.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))

        # Footer actions
        foot = ctk.CTkFrame(self, fg_color="transparent")
        foot.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.run_btn = ctk.CTkButton(
            foot,
            text="Take In Messages",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=40,
            command=self.start_run,
        )
        self.run_btn.pack(side="left")
        self.verify_label = ctk.CTkLabel(foot, text="", anchor="w")
        self.verify_label.pack(side="left", padx=16)

    def _enable_dnd(self) -> None:
        try:
            import windnd

            def on_drop(files: list) -> None:
                paths = []
                for f in files:
                    if isinstance(f, bytes):
                        f = f.decode("utf-8", errors="replace")
                    paths.append(Path(str(f)))
                self.after(0, lambda: self._add_paths(paths))

            windnd.hook_dropfiles(self.drop_frame, func=on_drop)
            self.drop_label.configure(
                text="Drag & drop Google Takeout .zip files here\n(or use Add ZIP / Add Folder)"
            )
        except Exception:
            self.drop_label.configure(
                text="Use Add ZIP / Add Folder to select Google Takeout archives\n"
                "(install windnd for drag-and-drop: pip install windnd)"
            )

    def log(self, msg: str) -> None:
        def _append() -> None:
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")

        self.after(0, _append)

    def set_progress(self, phase: str, done: int, total: int, messages: int) -> None:
        def _upd() -> None:
            frac = 0.0 if total <= 0 else min(1.0, done / total)
            self.progress.set(frac)
            self.status_label.configure(text=f"{phase}: {done}/{total}  |  messages: {messages}")

        self.after(0, _upd)

    def refresh_device(self) -> None:
        def work() -> None:
            path, devices, err = get_device_status(self.adb_path)
            self.adb_path = path

            def ui() -> None:
                if err and not devices:
                    self.device_label.configure(text=f"ADB: {err}")
                    return
                if not devices:
                    self.device_label.configure(
                        text=f"ADB: {path}\nNo devices. Enable USB debugging and authorize this PC."
                    )
                    return
                lines = [f"ADB: {path}"]
                for d in devices:
                    root_s = "yes" if d.rooted else ("no" if d.rooted is False else "?")
                    lines.append(
                        f"• {d.serial}  [{d.state}]  {d.model or d.product}  "
                        f"Android {d.android_version or '?'}  "
                        f"Root: {root_s}  SMS: {d.sms_role or '—'}"
                    )
                self.device_label.configure(text="\n".join(lines))

            self.after(0, ui)

        threading.Thread(target=work, daemon=True).start()

    def _refresh_source_list(self) -> None:
        self.source_list.configure(state="normal")
        self.source_list.delete("1.0", "end")
        if not self.sources:
            self.source_list.insert("end", "(none selected)")
        else:
            for p in self.sources:
                self.source_list.insert("end", f"{p}\n")
        self.source_list.configure(state="disabled")

    def _add_paths(self, paths: list[Path]) -> None:
        added = 0
        for p in paths:
            p = Path(p)
            if not p.exists():
                continue
            if p.suffix.lower() == ".zip" or p.is_dir():
                if p not in self.sources:
                    self.sources.append(p)
                    added += 1
        if added:
            self.log(f"[info] Added {added} source(s)")
        self._refresh_source_list()

    def add_zips(self) -> None:
        files = filedialog.askopenfilenames(
            title="Select Google Takeout ZIP files",
            filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")],
        )
        if files:
            self._add_paths([Path(f) for f in files])

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select Takeout Voice folder")
        if folder:
            self._add_paths([Path(folder)])

    def clear_sources(self) -> None:
        self.sources.clear()
        self._refresh_source_list()

    def start_run(self) -> None:
        if self._busy:
            return
        if not self.sources:
            messagebox.showwarning(APP_NAME, "Add at least one Takeout ZIP or folder.")
            return

        path, devices, _ = get_device_status(self.adb_path)
        rooted = any(d.state == "device" and d.rooted for d in devices)
        if rooted:
            ok = messagebox.askyesno(
                APP_NAME,
                "Rooted device detected.\n\n"
                "TakeIn SMS will back up mmssms.db, then import messages into the "
                "native Android SMS database.\n\nContinue?",
            )
            if not ok:
                return
        else:
            ok = messagebox.askyesno(
                APP_NAME,
                "No adb root detected.\n\n"
                "TakeIn SMS will convert to XML and (if a phone is connected) "
                "push it for restore via SMS Backup & Restore.\n\nContinue?",
            )
            if not ok:
                return

        self._busy = True
        self.run_btn.configure(state="disabled")
        self.verify_label.configure(text="")
        self.progress.set(0)
        serial = next((d.serial for d in devices if d.state == "device"), None)

        def work() -> None:
            try:
                result = run_pipeline(
                    list(self.sources),
                    work_dir=WORK_DIR,
                    prefer_root_import=True,
                    push_xml_if_no_root=True,
                    adb_path=path,
                    serial=serial,
                    progress_cb=self.set_progress,
                    log_cb=self.log,
                )

                def done() -> None:
                    if result.import_result:
                        ir = result.import_result
                        self.verify_label.configure(
                            text=(
                                f"Verified: {ir.before} → {ir.after} "
                                f"(+{ir.delta} / expected {ir.expected})"
                            )
                        )
                        if ir.delta <= 0 and result.mode == "root":
                            messagebox.showwarning(
                                APP_NAME,
                                "Import finished but SMS count did not increase.\n"
                                "Messages may already be present (idempotent skip).",
                            )
                        else:
                            messagebox.showinfo(APP_NAME, result.instructions)
                    else:
                        self.verify_label.configure(
                            text=f"Converted {result.message_count} messages → XML"
                        )
                        messagebox.showinfo(APP_NAME, result.instructions)
                    self._busy = False
                    self.run_btn.configure(state="normal")
                    self.refresh_device()

                self.after(0, done)
            except Exception as exc:  # noqa: BLE001
                err = exc

                def fail(error: BaseException = err) -> None:
                    self.log(f"[error] {error}")
                    messagebox.showerror(APP_NAME, str(error))
                    self._busy = False
                    self.run_btn.configure(state="normal")

                self.after(0, fail)

        threading.Thread(target=work, daemon=True).start()


def main() -> None:
    app = TakeInApp()
    app.mainloop()


if __name__ == "__main__":
    main()
