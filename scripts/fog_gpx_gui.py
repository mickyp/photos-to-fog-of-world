#!/usr/bin/env python3
"""Simple desktop GUI for exporting Fog of World GPX files from photos."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from build_fog_gpx import RunOptions, normalize_cli_path, run_conversion


AUTHOR_URL = "https://github.com/mickyp/photos-to-fog-of-world"

TRANSLATIONS = {
    "zh-TW": {
        "window_title": "照片轉 GPX",
        "language_label": "介面語言",
        "language_zh-TW": "正體中文",
        "language_en": "English",
        "intro": "一般情況下，只要選擇照片資料夾，再按下「匯出 GPX」即可。其餘欄位大多可以先維持預設值。",
        "photo_folder": "照片資料夾",
        "browse": "選擇...",
        "photo_folder_hint": "必填。請選擇要掃描的照片所在資料夾。",
        "output_gpx": "輸出 GPX（可不填）",
        "save_as": "另存為...",
        "output_gpx_hint": "可不填。若留白，程式會自動把 GPX 存在你選的照片資料夾內，並自動加上時間。",
        "timezone": "時區",
        "timezone_hint": "只有在照片時間本身沒有時區資訊時才會用到。如果照片是在台灣拍的，通常可使用 Asia/Taipei。",
        "track_name": "軌跡名稱（可不填）",
        "track_name_hint": "可不填。這是寫進 GPX 內的名稱，匯入地圖工具後可能會顯示這個名字。若留白，會改用資料夾名稱。",
        "reuse_child": "年度資料夾可重用既有子資料夾 GPX",
        "skip_existing": "若已存在 GPX 就不要再建立新的",
        "options_hint": "這兩個選項主要適合大量照片或重複匯出的情況。多數使用者可以先不勾選。",
        "export": "匯出 GPX",
        "status_ready": "請先選擇照片資料夾，然後按下「匯出 GPX」。",
        "dialog_choose_input": "選擇要掃描的照片資料夾",
        "dialog_choose_output": "選擇 GPX 儲存位置",
        "filetype_gpx": "GPX 檔案",
        "msg_in_progress_title": "匯出進行中",
        "msg_in_progress_body": "目前仍在處理中，請等待這次匯出完成。",
        "msg_missing_folder_title": "尚未選擇資料夾",
        "msg_missing_folder_body": "請先選擇照片資料夾。",
        "log_scanning": "正在掃描：{path}",
        "status_scanning": "正在掃描照片並建立 GPX...",
        "export_failed": "匯出失敗。",
        "unexpected_error": "發生未預期的錯誤：{error}",
        "no_gpx_created": "沒有建立 GPX，因為找不到同時具備拍攝時間與 GPS 資訊的照片。",
        "status_done": "已完成，GPX 已儲存到：{path}",
        "msg_done_title": "匯出完成",
        "msg_done_body": "GPX 已儲存到：\n{path}",
        "author_label": "作者：",
        "author_name": "Micky",
    },
    "en": {
        "window_title": "Photos to GPX",
        "language_label": "Language",
        "language_zh-TW": "Traditional Chinese",
        "language_en": "English",
        "intro": "In most cases, choose a photo folder and click Export GPX. The other fields are usually optional.",
        "photo_folder": "Photo folder",
        "browse": "Browse...",
        "photo_folder_hint": "Required. Choose the folder that contains the photos you want to scan.",
        "output_gpx": "Output GPX (optional)",
        "save_as": "Save as...",
        "output_gpx_hint": "Optional. Leave blank to save a timestamped GPX inside the selected photo folder.",
        "timezone": "Timezone",
        "timezone_hint": "Used only when photo timestamps do not already include timezone data. For photos taken in Taiwan, Asia/Taipei is usually correct.",
        "track_name": "Track name (optional)",
        "track_name_hint": "Optional. This is the track title stored inside the GPX. If left blank, the selected folder name is used.",
        "reuse_child": "Reuse existing child GPX for yearly folders",
        "skip_existing": "Skip writing a new GPX when one already exists",
        "options_hint": "These options are mainly useful for large or repeated exports. Most users can leave them unchecked.",
        "export": "Export GPX",
        "status_ready": "Select a photo folder, then click Export GPX.",
        "dialog_choose_input": "Choose the photo folder to scan",
        "dialog_choose_output": "Choose where to save the GPX file",
        "filetype_gpx": "GPX file",
        "msg_in_progress_title": "Export in progress",
        "msg_in_progress_body": "Please wait for the current export to finish.",
        "msg_missing_folder_title": "Missing folder",
        "msg_missing_folder_body": "Please choose a photo folder first.",
        "log_scanning": "Scanning: {path}",
        "status_scanning": "Scanning photos and building GPX...",
        "export_failed": "Export failed.",
        "unexpected_error": "Unexpected error: {error}",
        "no_gpx_created": "No GPX was created because no photos had both capture time and GPS data.",
        "status_done": "Completed. GPX saved to: {path}",
        "msg_done_title": "Export complete",
        "msg_done_body": "GPX saved to:\n{path}",
        "author_label": "Author: ",
        "author_name": "Micky",
    },
}

LANGUAGE_CHOICES = [
    ("zh-TW", "language_zh-TW"),
    ("en", "language_en"),
]


class FogGpxApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.minsize(760, 620)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.timezone_var = tk.StringVar(value="Asia/Taipei")
        self.track_name_var = tk.StringVar()
        self.language_var = tk.StringVar(value="zh-TW")
        self.reuse_child_var = tk.BooleanVar(value=False)
        self.skip_existing_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar()

        self._message_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._widgets: dict[str, object] = {}
        self._language_value_to_code: dict[str, str] = {}

        self._build_layout()
        self._apply_language()
        self.root.after(150, self._poll_messages)

    def _t(self, key: str, **kwargs: str) -> str:
        template = TRANSLATIONS[self.language_var.get()][key]
        return template.format(**kwargs) if kwargs else template

    def _language_display(self, code: str) -> str:
        label_key = f"language_{code}"
        return TRANSLATIONS[self.language_var.get()][label_key]

    def _build_layout(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(13, weight=1)

        self._widgets["language_label"] = ttk.Label(frame)
        self._widgets["language_label"].grid(row=0, column=0, sticky="w", pady=(0, 6))

        self._widgets["language_combo"] = ttk.Combobox(
            frame,
            state="readonly",
            textvariable=tk.StringVar(),
            width=20,
        )
        self._widgets["language_combo"].grid(row=0, column=1, sticky="w", pady=(0, 6))
        self._widgets["language_combo"].bind("<<ComboboxSelected>>", self._on_language_selected)

        self._widgets["intro_label"] = ttk.Label(frame, wraplength=700, justify="left")
        self._widgets["intro_label"].grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 14))

        self._widgets["photo_folder_label"] = ttk.Label(frame)
        self._widgets["photo_folder_label"].grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.input_var).grid(
            row=2, column=1, sticky="ew", padx=(8, 8), pady=(0, 6)
        )
        self._widgets["browse_button"] = ttk.Button(frame, command=self._choose_input)
        self._widgets["browse_button"].grid(row=2, column=2, sticky="ew", pady=(0, 6))
        self._widgets["photo_folder_hint"] = ttk.Label(frame, wraplength=700, justify="left")
        self._widgets["photo_folder_hint"].grid(row=3, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self._widgets["output_label"] = ttk.Label(frame)
        self._widgets["output_label"].grid(row=4, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.output_var).grid(
            row=4, column=1, sticky="ew", padx=(8, 8), pady=(0, 6)
        )
        self._widgets["save_as_button"] = ttk.Button(frame, command=self._choose_output)
        self._widgets["save_as_button"].grid(row=4, column=2, sticky="ew", pady=(0, 6))
        self._widgets["output_hint"] = ttk.Label(frame, wraplength=700, justify="left")
        self._widgets["output_hint"].grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self._widgets["timezone_label"] = ttk.Label(frame)
        self._widgets["timezone_label"].grid(row=6, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.timezone_var).grid(
            row=6, column=1, sticky="ew", padx=(8, 8), pady=(0, 6)
        )
        self._widgets["timezone_hint"] = ttk.Label(frame, wraplength=700, justify="left")
        self._widgets["timezone_hint"].grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 10))

        self._widgets["track_name_label"] = ttk.Label(frame)
        self._widgets["track_name_label"].grid(row=8, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.track_name_var).grid(
            row=8, column=1, sticky="ew", padx=(8, 8), pady=(0, 6)
        )
        self._widgets["track_name_hint"] = ttk.Label(frame, wraplength=700, justify="left")
        self._widgets["track_name_hint"].grid(row=9, column=0, columnspan=3, sticky="w", pady=(0, 10))

        options_frame = ttk.Frame(frame)
        options_frame.grid(row=10, column=0, columnspan=3, sticky="w", pady=(4, 6))

        self._widgets["reuse_child_check"] = ttk.Checkbutton(
            options_frame,
            variable=self.reuse_child_var,
        )
        self._widgets["reuse_child_check"].pack(anchor="w")

        self._widgets["skip_existing_check"] = ttk.Checkbutton(
            options_frame,
            variable=self.skip_existing_var,
        )
        self._widgets["skip_existing_check"].pack(anchor="w")

        self._widgets["options_hint"] = ttk.Label(frame, wraplength=700, justify="left")
        self._widgets["options_hint"].grid(row=11, column=0, columnspan=3, sticky="w", pady=(0, 12))

        actions = ttk.Frame(frame)
        actions.grid(row=12, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        actions.columnconfigure(0, weight=1)
        self._widgets["export_button"] = ttk.Button(actions, command=self._start_export)
        self._widgets["export_button"].grid(row=0, column=1, sticky="e")

        self.log_text = tk.Text(frame, height=16, wrap="word", state="disabled")
        self.log_text.grid(row=13, column=0, columnspan=3, sticky="nsew")

        self._widgets["status_label"] = ttk.Label(frame, textvariable=self.status_var)
        self._widgets["status_label"].grid(row=14, column=0, columnspan=3, sticky="w", pady=(12, 0))

        footer = ttk.Frame(frame)
        footer.grid(row=15, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self._widgets["author_label"] = ttk.Label(footer)
        self._widgets["author_label"].pack(side="left")
        self._widgets["author_link"] = tk.Label(
            footer,
            cursor="hand2",
            fg="#0b57d0",
            padx=0,
            pady=0,
        )
        self._widgets["author_link"].pack(side="left")
        self._widgets["author_link"].bind("<Button-1>", self._open_author_link)

    def _apply_language(self) -> None:
        self.root.title(self._t("window_title"))
        self.status_var.set(self._t("status_ready"))

        self._widgets["language_label"].configure(text=self._t("language_label"))
        self._widgets["intro_label"].configure(text=self._t("intro"))
        self._widgets["photo_folder_label"].configure(text=self._t("photo_folder"))
        self._widgets["browse_button"].configure(text=self._t("browse"))
        self._widgets["photo_folder_hint"].configure(text=self._t("photo_folder_hint"))
        self._widgets["output_label"].configure(text=self._t("output_gpx"))
        self._widgets["save_as_button"].configure(text=self._t("save_as"))
        self._widgets["output_hint"].configure(text=self._t("output_gpx_hint"))
        self._widgets["timezone_label"].configure(text=self._t("timezone"))
        self._widgets["timezone_hint"].configure(text=self._t("timezone_hint"))
        self._widgets["track_name_label"].configure(text=self._t("track_name"))
        self._widgets["track_name_hint"].configure(text=self._t("track_name_hint"))
        self._widgets["reuse_child_check"].configure(text=self._t("reuse_child"))
        self._widgets["skip_existing_check"].configure(text=self._t("skip_existing"))
        self._widgets["options_hint"].configure(text=self._t("options_hint"))
        self._widgets["export_button"].configure(text=self._t("export"))
        self._widgets["author_label"].configure(text=self._t("author_label"))
        self._widgets["author_link"].configure(text=self._t("author_name"))

        combo: ttk.Combobox = self._widgets["language_combo"]  # type: ignore[assignment]
        display_values = []
        self._language_value_to_code = {}
        current_value = None
        for code, _ in LANGUAGE_CHOICES:
            display = self._language_display(code)
            display_values.append(display)
            self._language_value_to_code[display] = code
            if code == self.language_var.get():
                current_value = display
        combo.configure(values=display_values)
        if current_value is not None:
            combo.set(current_value)

    def _on_language_selected(self, _event: object) -> None:
        combo: ttk.Combobox = self._widgets["language_combo"]  # type: ignore[assignment]
        selected = combo.get()
        code = self._language_value_to_code.get(selected)
        if code and code != self.language_var.get():
            self.language_var.set(code)
            self._apply_language()

    def _choose_input(self) -> None:
        selected = filedialog.askdirectory(title=self._t("dialog_choose_input"))
        if selected:
            self.input_var.set(selected)
            if not self.output_var.get().strip():
                suggested = Path(selected) / f"{Path(selected).name}_fog_of_world.gpx"
                self.output_var.set(str(suggested))

    def _choose_output(self) -> None:
        initial_dir = self.input_var.get().strip() or str(Path.home())
        selected = filedialog.asksaveasfilename(
            title=self._t("dialog_choose_output"),
            defaultextension=".gpx",
            filetypes=[(self._t("filetype_gpx"), "*.gpx")],
            initialdir=initial_dir if Path(initial_dir).exists() else str(Path.home()),
            initialfile="photos_fog_of_world.gpx",
        )
        if selected:
            self.output_var.set(selected)

    def _start_export(self) -> None:
        if self._worker and self._worker.is_alive():
            messagebox.showinfo(self._t("msg_in_progress_title"), self._t("msg_in_progress_body"))
            return

        input_dir = self.input_var.get().strip()
        if not input_dir:
            messagebox.showwarning(
                self._t("msg_missing_folder_title"),
                self._t("msg_missing_folder_body"),
            )
            return

        self._append_log("")
        self._append_log(self._t("log_scanning", path=input_dir))
        self.status_var.set(self._t("status_scanning"))

        self._worker = threading.Thread(
            target=self._run_export,
            args=(input_dir, self.output_var.get().strip()),
            daemon=True,
        )
        self._worker.start()

    def _run_export(self, input_dir: str, output_path: str) -> None:
        def enqueue_line(line: str) -> None:
            self._message_queue.put(("log", line))

        try:
            summary = run_conversion(
                RunOptions(
                    input_dir=normalize_cli_path(input_dir),
                    output=normalize_cli_path(output_path) if output_path else None,
                    timezone_name=self.timezone_var.get().strip() or "Asia/Taipei",
                    track_name=self.track_name_var.get().strip() or None,
                    reuse_existing_child_gpx=self.reuse_child_var.get(),
                    skip_existing_output=self.skip_existing_var.get(),
                ),
                line_printer=enqueue_line,
            )
        except SystemExit as exc:
            self._message_queue.put(("error", str(exc) or self._t("export_failed")))
            return
        except Exception as exc:  # pragma: no cover - defensive GUI error handling
            self._message_queue.put(("error", self._t("unexpected_error", error=str(exc))))
            return

        if summary.output_path:
            self._message_queue.put(("done", str(summary.output_path)))
        else:
            self._message_queue.put(("error", self._t("no_gpx_created")))

    def _poll_messages(self) -> None:
        while True:
            try:
                kind, value = self._message_queue.get_nowait()
            except queue.Empty:
                break

            if kind == "log":
                self._append_log(value)
            elif kind == "done":
                self.status_var.set(self._t("status_done", path=value))
                self._append_log(self._t("status_done", path=value))
                messagebox.showinfo(self._t("msg_done_title"), self._t("msg_done_body", path=value))
            elif kind == "error":
                self.status_var.set(self._t("export_failed"))
                self._append_log(value)
                messagebox.showerror(self._t("export_failed"), value)

        self.root.after(150, self._poll_messages)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        if message:
            self.log_text.insert("end", message + "\n")
        else:
            self.log_text.insert("end", "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _open_author_link(self, _event: object) -> None:
        webbrowser.open(AUTHOR_URL)


def main() -> int:
    root = tk.Tk()
    ttk.Style().theme_use("vista")
    FogGpxApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
