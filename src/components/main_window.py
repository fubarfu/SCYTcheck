from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import ttk

from src.components.file_selector import FileSelector
from src.components.progress_display import ProgressDisplay
from src.components.url_input import URLInput
from src.config import AdvancedSettings
from src.services.export_service import ExportService


class _FallbackVar:
    def __init__(self, value: object = None) -> None:
        self._value = value

    def get(self) -> object:
        return self._value

    def set(self, value: object) -> None:
        self._value = value


class _FallbackWidget:
    def grid(self, *args, **kwargs) -> None:  # pragma: no cover - simple test fallback
        return


class MainWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SCYTcheck - YouTube Text Analyzer")
        self.root.minsize(720, 320)

        container = ttk.Frame(root, padding=16)
        container.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=0)

        self.url_input = URLInput(container)
        self.url_input.grid(row=0, column=0, columnspan=2)

        self.file_selector = FileSelector(container)
        self.file_selector.grid(row=2, column=0, columnspan=2)

        # Auto-generated filename preview (folder-only output workflow)
        self.filename_label = ttk.Label(
            container,
            text="Output Filename",
            font=("TkDefaultFont", 9, "bold")
        )
        self.filename_label.grid(row=3, column=0, sticky="w", pady=(12, 2))

        self.filename_display = ttk.Label(
            container,
            text="(Filename will be generated from YouTube video ID)",
            foreground="gray",
            font=("TkDefaultFont", 9)
        )
        self.filename_display.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 0))

        # Advanced settings section (separate from primary workflow controls)
        self.advanced_settings_frame = ttk.LabelFrame(container, text="Advanced Settings", padding=8)
        self.advanced_settings_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        self.advanced_settings_frame.columnconfigure(0, weight=1)
        self.advanced_settings_frame.columnconfigure(1, weight=0)
        self.advanced_settings_frame.columnconfigure(2, weight=0)
        self.advanced_settings_frame.columnconfigure(3, weight=0)

        self.pattern_help = ttk.Label(
            self.advanced_settings_frame,
            text="Context patterns (one per line): before|after|enabled  (enabled: true/false)",
            foreground="gray",
        )
        self.pattern_help.grid(row=0, column=0, columnspan=3, sticky="w")

        self.patterns_text = tk.Text(self.advanced_settings_frame, height=5, width=64, wrap="none")
        self.patterns_text.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(4, 8))

        self.filter_non_matching_var = tk.BooleanVar(value=True)
        self.filter_non_matching_check = ttk.Checkbutton(
            self.advanced_settings_frame,
            text="Only extract names matching a context pattern",
            variable=self.filter_non_matching_var,
        )
        self.filter_non_matching_check.grid(row=2, column=0, columnspan=2, sticky="w")

        self.video_quality_label = ttk.Label(self.advanced_settings_frame, text="Video quality")
        self.video_quality_label.grid(row=2, column=2, sticky="e")
        try:
            self.video_quality_var = tk.StringVar(value="best")
        except RuntimeError:
            self.video_quality_var = _FallbackVar("best")
        try:
            self.video_quality_combo = ttk.Combobox(
                self.advanced_settings_frame,
                textvariable=self.video_quality_var,
                values=["best", "720p", "480p", "360p"],
                width=10,
                state="readonly",
            )
        except Exception:
            self.video_quality_combo = _FallbackWidget()
        self.video_quality_combo.grid(row=2, column=3, sticky="w", padx=(8, 0))

        self.logging_enabled_var = tk.BooleanVar(value=False)
        self.logging_enabled_check = ttk.Checkbutton(
            self.advanced_settings_frame,
            text="Enable detailed sidecar log (_log.csv)",
            variable=self.logging_enabled_var,
        )
        self.logging_enabled_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.event_gap_label = ttk.Label(self.advanced_settings_frame, text="Event merge gap (seconds)")
        self.event_gap_label.grid(row=4, column=0, sticky="w", pady=(8, 0))

        self.event_gap_var = tk.DoubleVar(value=1.0)
        self.event_gap_spinbox = ttk.Spinbox(
            self.advanced_settings_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.event_gap_var,
            width=8,
        )
        self.event_gap_spinbox.grid(row=4, column=1, sticky="w", pady=(8, 0))

        self.ocr_sensitivity_label = ttk.Label(self.advanced_settings_frame, text="OCR sensitivity (confidence 0-100)")
        self.ocr_sensitivity_label.grid(row=5, column=0, sticky="w", pady=(8, 0))

        self.ocr_confidence_var = tk.IntVar(value=40)
        self.ocr_sensitivity_spinbox = ttk.Spinbox(
            self.advanced_settings_frame,
            from_=0,
            to=100,
            increment=1,
            textvariable=self.ocr_confidence_var,
            width=8,
        )
        self.ocr_sensitivity_spinbox.grid(row=5, column=1, sticky="w", pady=(8, 0))

        self.low_quality_guidance = ttk.Label(
            self.advanced_settings_frame,
            text=(
                "Low-quality videos can reduce OCR reliability. Lower confidence to improve recall, "
                "or raise it to reduce false positives."
            ),
            foreground="gray",
            wraplength=620,
            justify="left",
        )
        self.low_quality_guidance.grid(row=6, column=0, columnspan=4, sticky="w", pady=(6, 0))

        self.progress = ProgressDisplay(container)
        self.progress.grid(row=6, column=0, columnspan=2)

        self.status = ttk.Label(container, text="Ready")
        self.status.grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.analyze_button = ttk.Button(container, text="Select Regions + Analyze")
        self.analyze_button.grid(row=8, column=0, sticky="w", pady=(12, 0))

        self.retry_export_button = ttk.Button(container, text="Retry Export", state="disabled")
        self.retry_export_button.grid(row=8, column=1, sticky="e", pady=(12, 0))

        self.url_input.entry.bind("<KeyRelease>", self._on_url_changed)
        self.url_input.entry.bind("<FocusOut>", self._on_url_changed)
        self.update_filename_display()

        self.root.bind("<Control-Return>", self._on_analyze_shortcut)
        self.root.bind("<Alt-u>", self._focus_url_input)
        self.root.bind("<Alt-o>", self._focus_output_folder)

    @staticmethod
    def _parse_bool(value: str) -> bool:
        return value.strip().lower() not in {"false", "0", "no", "off"}

    def _parse_pattern_lines(self, content: str) -> list[dict[str, object]]:
        patterns: list[dict[str, object]] = []
        for index, raw_line in enumerate(content.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = [part.strip() for part in line.split("|")]
            if len(parts) == 1:
                before_text = None
                after_text = parts[0] or None
                enabled = True
            elif len(parts) == 2:
                before_text = parts[0] or None
                after_text = parts[1] or None
                enabled = True
            else:
                before_text = parts[0] or None
                after_text = parts[1] or None
                enabled = self._parse_bool(parts[2])

            if not before_text and not after_text:
                continue

            patterns.append(
                {
                    "id": f"pattern-{index}",
                    "before_text": before_text,
                    "after_text": after_text,
                    "enabled": enabled,
                }
            )

        return patterns

    def get_advanced_settings(self) -> AdvancedSettings:
        raw_patterns = self.patterns_text.get("1.0", "end").strip()
        patterns = self._parse_pattern_lines(raw_patterns)
        if not patterns:
            patterns = [
                {"id": "default-joined", "before_text": None, "after_text": "joined", "enabled": True},
                {
                    "id": "default-connected",
                    "before_text": None,
                    "after_text": "connected",
                    "enabled": True,
                },
            ]

        return AdvancedSettings(
            context_patterns=patterns,
            filter_non_matching=bool(self.filter_non_matching_var.get()),
            event_gap_threshold_sec=float(self.event_gap_var.get()),
            ocr_confidence_threshold=int(max(0, min(int(self.ocr_confidence_var.get()), 100))),
            video_quality=str(getattr(self, "video_quality_var", _FallbackVar("best")).get() or "best"),
            logging_enabled=bool(getattr(self, "logging_enabled_var", _FallbackVar(False)).get()),
        )

    def apply_advanced_settings(self, settings: AdvancedSettings) -> None:
        lines: list[str] = []
        for item in settings.context_patterns:
            before_text = "" if item.get("before_text") is None else str(item.get("before_text"))
            after_text = "" if item.get("after_text") is None else str(item.get("after_text"))
            enabled = "true" if bool(item.get("enabled", True)) else "false"
            lines.append(f"{before_text}|{after_text}|{enabled}")

        self.patterns_text.delete("1.0", "end")
        self.patterns_text.insert("1.0", "\n".join(lines))
        self.filter_non_matching_var.set(bool(settings.filter_non_matching))
        self.event_gap_var.set(float(settings.event_gap_threshold_sec))
        self.ocr_confidence_var.set(int(max(0, min(int(settings.ocr_confidence_threshold), 100))))
        getattr(self, "video_quality_var", _FallbackVar("best")).set(str(settings.video_quality or "best"))
        getattr(self, "logging_enabled_var", _FallbackVar(False)).set(bool(settings.logging_enabled))

    def _on_url_changed(self, _event: object | None = None) -> None:
        self.update_filename_display()

    def update_filename_display(self, url: str | None = None) -> None:
        """Update the displayed filename based on the current URL."""
        if url is None:
            url = self.url_input.get()

        if not url:
            self.filename_display.configure(
                text="(Enter a YouTube URL to generate filename)",
                foreground="gray"
            )
            return

        try:
            filename = ExportService.generate_filename(url)
            self.filename_display.configure(
                text=filename,
                foreground="black"
            )
        except ValueError:
            self.filename_display.configure(
                text="(Invalid YouTube URL - filename will be generated from valid URL)",
                foreground="orange"
            )

    def set_status(self, value: str) -> None:
        self.status.configure(text=value)
        self.status.update_idletasks()

    def set_analyze_command(self, command) -> None:
        self.analyze_button.configure(command=command)

    def set_retry_export_command(self, command: object | None) -> None:
        if command is None:
            self.retry_export_button.configure(command=None, state="disabled")
        else:
            self.retry_export_button.configure(command=command, state="normal")

    def _on_analyze_shortcut(self, _event=None):
        command = self.analyze_button.options.get("command") if hasattr(self.analyze_button, "options") else None
        if command is None:
            try:
                self.analyze_button.invoke()
            except Exception:
                return "break"
        else:
            command()
        return "break"

    def _focus_url_input(self, _event=None):
        try:
            self.url_input.entry.focus_set()
        except Exception:
            pass
        return "break"

    def _focus_output_folder(self, _event=None):
        try:
            self.file_selector.entry.focus_set()
        except Exception:
            pass
        return "break"
