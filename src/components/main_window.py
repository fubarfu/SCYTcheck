from __future__ import annotations

import tkinter as tk
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


class _Tooltip:
    """Simple hover tooltip for Tk widgets."""

    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 350) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id: str | None = None
        self._window: tk.Toplevel | None = None

        self.widget.bind("<Enter>", self._on_enter, add="+")
        self.widget.bind("<Leave>", self._on_leave, add="+")
        self.widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event: object | None = None) -> None:
        self._schedule_show()

    def _on_leave(self, _event: object | None = None) -> None:
        self._cancel_scheduled_show()
        self._hide()

    def _schedule_show(self) -> None:
        self._cancel_scheduled_show()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel_scheduled_show(self) -> None:
        if self._after_id is None:
            return
        self.widget.after_cancel(self._after_id)
        self._after_id = None

    def _show(self) -> None:
        if self._window is not None:
            return

        try:
            x, y = self.widget.winfo_pointerxy()
            window = tk.Toplevel(self.widget)
            window.wm_overrideredirect(True)
            window.wm_geometry(f"+{x + 12}+{y + 12}")
            label = tk.Label(
                window,
                text=self.text,
                justify="left",
                relief="solid",
                borderwidth=1,
                background="#ffffe0",
                foreground="#222222",
                padx=8,
                pady=5,
                wraplength=420,
            )
            label.pack()
            self._window = window
        except Exception:
            self._window = None

    def _hide(self) -> None:
        if self._window is None:
            return
        self._window.destroy()
        self._window = None


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
            container, text="Output Filename", font=("TkDefaultFont", 9, "bold")
        )
        self.filename_label.grid(row=4, column=0, sticky="w", pady=(12, 2))

        self.filename_display = ttk.Label(
            container,
            text="(Filename will be generated from YouTube video ID)",
            foreground="gray",
            font=("TkDefaultFont", 9),
        )
        self.filename_display.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 0))

        # Advanced settings section (separate from primary workflow controls)
        self.advanced_settings_frame = ttk.LabelFrame(
            container, text="Advanced Settings", padding=8
        )
        self.advanced_settings_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(12, 0))
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

        self.tolerance_label = ttk.Label(self.advanced_settings_frame, text="Matching tolerance")
        self.tolerance_label.grid(row=3, column=2, sticky="e", pady=(8, 0))
        self.tolerance_var = tk.DoubleVar(value=0.75)
        self.tolerance_spinbox = ttk.Spinbox(
            self.advanced_settings_frame,
            from_=0.60,
            to=0.95,
            increment=0.01,
            textvariable=self.tolerance_var,
            width=8,
        )
        self.tolerance_spinbox.grid(row=3, column=3, sticky="w", padx=(8, 0), pady=(8, 0))

        self.gating_enabled_var = tk.BooleanVar(value=False)
        self.gating_enabled_check = ttk.Checkbutton(
            self.advanced_settings_frame,
            text="Enable Frame-Change Gating",
            variable=self.gating_enabled_var,
        )
        self.gating_enabled_check.grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.gating_threshold_label = ttk.Label(
            self.advanced_settings_frame, text="Gating threshold"
        )
        self.gating_threshold_label.grid(row=4, column=2, sticky="e", pady=(8, 0))
        self.gating_threshold_var = tk.DoubleVar(value=0.02)
        self.gating_threshold_spinbox = ttk.Spinbox(
            self.advanced_settings_frame,
            from_=0.0,
            to=1.0,
            increment=0.01,
            textvariable=self.gating_threshold_var,
            width=8,
        )
        self.gating_threshold_spinbox.grid(row=4, column=3, sticky="w", padx=(8, 0), pady=(8, 0))

        self.event_gap_label = ttk.Label(
            self.advanced_settings_frame, text="Event merge gap (seconds)"
        )
        self.event_gap_label.grid(row=5, column=0, sticky="w", pady=(8, 0))

        self.event_gap_var = tk.DoubleVar(value=1.0)
        self.event_gap_spinbox = ttk.Spinbox(
            self.advanced_settings_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.event_gap_var,
            width=8,
        )
        self.event_gap_spinbox.grid(row=5, column=1, sticky="w", pady=(8, 0))

        self.ocr_sensitivity_label = ttk.Label(
            self.advanced_settings_frame, text="OCR sensitivity (confidence 0-100)"
        )
        self.ocr_sensitivity_label.grid(row=6, column=0, sticky="w", pady=(8, 0))

        self.ocr_confidence_var = tk.IntVar(value=40)
        self.ocr_sensitivity_spinbox = ttk.Spinbox(
            self.advanced_settings_frame,
            from_=0,
            to=100,
            increment=1,
            textvariable=self.ocr_confidence_var,
            width=8,
        )
        self.ocr_sensitivity_spinbox.grid(row=6, column=1, sticky="w", pady=(8, 0))

        self.progress = ProgressDisplay(container)
        self.progress.grid(row=7, column=0, columnspan=2)

        self.status = ttk.Label(container, text="Ready")
        self.status.grid(row=8, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.analyze_button = ttk.Button(container, text="Select Regions + Analyze")
        self.analyze_button.grid(row=9, column=0, sticky="w", pady=(12, 0))

        self.retry_export_button = ttk.Button(container, text="Retry Export", state="disabled")
        self.retry_export_button.grid(row=9, column=1, sticky="e", pady=(12, 0))

        self.url_input.entry.bind("<KeyRelease>", self._on_url_changed)
        self.url_input.entry.bind("<FocusOut>", self._on_url_changed)
        self.update_filename_display()

        self.root.bind("<Control-Return>", self._on_analyze_shortcut)
        self.root.bind("<Alt-u>", self._focus_url_input)
        self.root.bind("<Alt-o>", self._focus_output_folder)

        self._tooltips: list[_Tooltip] = []
        self._attach_setting_tooltips()

    def _add_tooltip(self, widget: object, text: str) -> None:
        bind_method = getattr(widget, "bind", None)
        if bind_method is None:
            return
        self._tooltips.append(_Tooltip(widget, text))

    def _attach_setting_tooltips(self) -> None:
        self._add_tooltip(
            self.pattern_help,
            (
                "Context patterns define text expected around player names. "
                "More accurate patterns improve precision, but very strict patterns "
                "can miss valid names."
            ),
        )
        self._add_tooltip(
            self.patterns_text,
            (
                "One pattern per line: before|after|enabled. "
                "Good patterns reduce false positives and speed post-filtering by "
                "discarding irrelevant OCR matches earlier."
            ),
        )
        self._add_tooltip(
            self.filter_non_matching_check,
            (
                "When enabled, names that do not match context patterns are removed. "
                "Usually improves quality, but can lower recall if patterns are incomplete."
            ),
        )
        self._add_tooltip(
            self.video_quality_label,
            (
                "Higher video quality improves OCR readability and matching quality, "
                "but increases download time and processing cost."
            ),
        )
        self._add_tooltip(
            self.video_quality_combo,
            (
                "best gives highest visual fidelity for OCR. "
                "Lower resolutions can be faster to fetch/process but may hurt text clarity."
            ),
        )
        self._add_tooltip(
            self.logging_enabled_check,
            (
                "Writes a detailed sidecar log for diagnostics and tuning. "
                "Helps troubleshooting, with small additional disk I/O overhead."
            ),
        )
        self._add_tooltip(
            self.tolerance_label,
            (
                "Matching tolerance controls fuzzy-name matching strictness. "
                "Lower values increase recall (and potential false positives); "
                "higher values improve precision."
            ),
        )
        self._add_tooltip(
            self.tolerance_spinbox,
            (
                "Lower tolerance is more permissive and may require more downstream filtering. "
                "Higher tolerance is stricter and can miss noisy OCR names."
            ),
        )
        self._add_tooltip(
            self.gating_enabled_check,
            (
                "Frame-change gating skips OCR on visually unchanged frames. "
                "This can significantly improve speed while preserving quality in stable scenes."
            ),
        )
        self._add_tooltip(
            self.gating_threshold_label,
            (
                "Threshold for deciding whether a frame changed enough to run OCR. "
                "Higher values skip more OCR (faster) but risk missing subtle text updates."
            ),
        )
        self._add_tooltip(
            self.gating_threshold_spinbox,
            (
                "Lower threshold runs OCR more often (slower, safer for quality). "
                "Higher threshold runs OCR less often (faster, higher miss risk)."
            ),
        )
        self._add_tooltip(
            self.event_gap_label,
            (
                "Events within this gap are merged into one detection interval. "
                "Higher values produce fewer merged events and less output noise, "
                "but can hide rapid separate changes."
            ),
        )
        self._add_tooltip(
            self.event_gap_spinbox,
            (
                "Lower gap preserves fine-grained timing details. "
                "Higher gap smooths fragmented detections and can simplify results."
            ),
        )
        self._add_tooltip(
            self.ocr_sensitivity_label,
            (
                "Minimum OCR confidence score to accept text. "
                "Lower confidence improves recall; higher confidence improves precision."
            ),
        )
        self._add_tooltip(
            self.ocr_sensitivity_spinbox,
            (
                "Lower values may catch faint text but add false positives. "
                "Higher values reduce noise but may drop legitimate low-confidence text."
            ),
        )

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
                {
                    "id": "default-has-joined",
                    "before_text": None,
                    "after_text": "has joined",
                    "enabled": True,
                },
                {
                    "id": "default-party-connected",
                    "before_text": "Party",
                    "after_text": "connected",
                    "enabled": True,
                },
                {
                    "id": "default-party-disconnected",
                    "before_text": "Party",
                    "after_text": "disconnected",
                    "enabled": True,
                },
                {
                    "id": "default-started-by",
                    "before_text": "started by",
                    "after_text": None,
                    "enabled": True,
                },
            ]

        return AdvancedSettings(
            context_patterns=patterns,
            filter_non_matching=bool(self.filter_non_matching_var.get()),
            event_gap_threshold_sec=float(self.event_gap_var.get()),
            ocr_confidence_threshold=int(max(0, min(int(self.ocr_confidence_var.get()), 100))),
            video_quality=str(
                getattr(self, "video_quality_var", _FallbackVar("best")).get() or "best"
            ),
            logging_enabled=bool(getattr(self, "logging_enabled_var", _FallbackVar(False)).get()),
            tolerance_value=float(
                max(
                    0.60,
                    min(
                        float(getattr(self, "tolerance_var", _FallbackVar(0.75)).get()),
                        0.95,
                    ),
                )
            ),
            gating_enabled=bool(getattr(self, "gating_enabled_var", _FallbackVar(True)).get()),
            gating_threshold=float(
                max(
                    0.0,
                    min(
                        float(getattr(self, "gating_threshold_var", _FallbackVar(0.02)).get()),
                        1.0,
                    ),
                )
            ),
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
        getattr(self, "video_quality_var", _FallbackVar("best")).set(
            str(settings.video_quality or "best")
        )
        getattr(self, "logging_enabled_var", _FallbackVar(False)).set(
            bool(settings.logging_enabled)
        )
        getattr(self, "tolerance_var", _FallbackVar(0.75)).set(
            float(max(0.60, min(settings.tolerance_value, 0.95)))
        )
        getattr(self, "gating_enabled_var", _FallbackVar(True)).set(bool(settings.gating_enabled))
        getattr(self, "gating_threshold_var", _FallbackVar(0.02)).set(
            float(max(0.0, min(settings.gating_threshold, 1.0)))
        )

    def _on_url_changed(self, _event: object | None = None) -> None:
        self.update_filename_display()

    def update_filename_display(self, url: str | None = None) -> None:
        """Update the displayed filename based on the current URL."""
        if url is None:
            url = self.url_input.get()

        if not url:
            self.filename_display.configure(
                text="(Enter a YouTube URL to generate filename)", foreground="gray"
            )
            return

        try:
            filename = ExportService.generate_filename(url)
            self.filename_display.configure(text=filename, foreground="black")
        except ValueError:
            self.filename_display.configure(
                text="(Invalid YouTube URL - filename will be generated from valid URL)",
                foreground="orange",
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
        command = (
            self.analyze_button.options.get("command")
            if hasattr(self.analyze_button, "options")
            else None
        )
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
