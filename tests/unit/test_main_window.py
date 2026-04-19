from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.components.main_window import MainWindow
from src.config import AdvancedSettings


class _VarStub:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class _TextStub:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self, *_args):
        return self.value

    def delete(self, *_args):
        self.value = ""

    def insert(self, *_args):
        self.value = _args[-1]


class _WidgetStub:
    def __init__(self, *args, **kwargs):
        self.grid_kwargs = None
        self.options = dict(kwargs)
        self.focused = False

    def grid(self, **kwargs):
        self.grid_kwargs = kwargs

    def configure(self, **kwargs):
        self.options.update(kwargs)

    def invoke(self):
        command = self.options.get("command")
        if command is not None:
            command()

    def columnconfigure(self, *_args, **_kwargs):
        return None

    def rowconfigure(self, *_args, **_kwargs):
        return None

    def bind(self, *_args, **_kwargs):
        return None

    def update_idletasks(self):
        return None

    def delete(self, *_args, **_kwargs):
        return None

    def insert(self, *_args, **_kwargs):
        return None

    def focus_set(self):
        self.focused = True


class _RootStub:
    def __init__(self):
        self.bindings = {}

    def title(self, *_args, **_kwargs):
        return None

    def minsize(self, *_args, **_kwargs):
        return None

    def columnconfigure(self, *_args, **_kwargs):
        return None

    def rowconfigure(self, *_args, **_kwargs):
        return None

    def bind(self, event, callback):
        self.bindings[event] = callback
        return None


class _URLInputStub:
    def __init__(self, _parent):
        self.label = _WidgetStub()
        self.entry = _WidgetStub()

    def grid(self, row: int, column: int, columnspan: int = 1):
        self.label.grid(row=row, column=column, sticky="w", pady=(4, 2))
        self.entry.grid(row=row + 1, column=column, columnspan=columnspan, sticky="ew")

    def get(self):
        return ""


class _FileSelectorStub:
    def __init__(self, _parent):
        self.label = _WidgetStub()
        self.entry = _WidgetStub()
        self.button = _WidgetStub()

    def grid(self, row: int, column: int, columnspan: int = 1):
        self.label.grid(row=row, column=column, sticky="w", pady=(8, 2))
        self.entry.grid(row=row + 1, column=column, columnspan=max(1, columnspan - 1), sticky="ew")
        self.button.grid(row=row + 1, column=column + columnspan - 1, sticky="e", padx=(8, 0))


class _ProgressDisplayStub:
    def __init__(self, _parent):
        self.grid_kwargs = None

    def grid(self, row: int, column: int, columnspan: int = 1):
        self.grid_kwargs = {"row": row, "column": column, "columnspan": columnspan}


def _make_window_stub(
    patterns: str = "",
    filter_non_matching: bool = True,
    gap: float = 1.0,
    confidence: int = 40,
    video_quality: str = "best",
    logging_enabled: bool = False,
    tolerance_value: float = 0.75,
    gating_enabled: bool = False,
    gating_threshold: float = 0.02,
) -> MainWindow:
    window = MainWindow.__new__(MainWindow)
    window.patterns_text = _TextStub(patterns)
    window.filter_non_matching_var = _VarStub(filter_non_matching)
    window.event_gap_var = _VarStub(gap)
    window.ocr_confidence_var = _VarStub(confidence)
    window.video_quality_var = _VarStub(video_quality)
    window.logging_enabled_var = _VarStub(logging_enabled)
    window.tolerance_var = _VarStub(tolerance_value)
    window.gating_enabled_var = _VarStub(gating_enabled)
    window.gating_threshold_var = _VarStub(gating_threshold)
    window.filename_display = MagicMock()
    window.url_input = SimpleNamespace(get=lambda: "")
    return window


def test_get_advanced_settings_parses_multiple_patterns() -> None:
    window = _make_window_stub(
        patterns="joined||true\n|connected|false\nprefix|suffix|true",
        filter_non_matching=True,
        gap=2.5,
        confidence=28,
    )

    settings = window.get_advanced_settings()

    assert settings.filter_non_matching is True
    assert settings.event_gap_threshold_sec == 2.5
    assert settings.ocr_confidence_threshold == 28
    assert len(settings.context_patterns) == 3
    assert settings.context_patterns[0]["before_text"] == "joined"
    assert settings.context_patterns[0]["after_text"] is None
    assert settings.context_patterns[1]["before_text"] is None
    assert settings.context_patterns[1]["after_text"] == "connected"
    assert settings.context_patterns[1]["enabled"] is False


def test_get_advanced_settings_uses_defaults_when_patterns_empty() -> None:
    window = _make_window_stub(patterns="\n\n  ", filter_non_matching=True, gap=1.0)

    settings = window.get_advanced_settings()

    assert len(settings.context_patterns) == 4
    assert settings.context_patterns[0]["before_text"] is None
    assert settings.context_patterns[0]["after_text"] == "has joined"
    assert settings.context_patterns[1]["before_text"] == "Party"
    assert settings.context_patterns[1]["after_text"] == "connected"
    assert settings.context_patterns[2]["before_text"] == "Party"
    assert settings.context_patterns[2]["after_text"] == "disconnected"
    assert settings.context_patterns[3]["before_text"] == "started by"
    assert settings.context_patterns[3]["after_text"] is None
    assert settings.filter_non_matching is True


def test_apply_advanced_settings_populates_controls() -> None:
    window = _make_window_stub()
    settings = AdvancedSettings(
        context_patterns=[
            {"id": "p1", "before_text": "Player:", "after_text": None, "enabled": True},
            {"id": "p2", "before_text": None, "after_text": "joined", "enabled": False},
        ],
        filter_non_matching=True,
        event_gap_threshold_sec=3.0,
        ocr_confidence_threshold=22,
    )

    window.apply_advanced_settings(settings)

    content = window.patterns_text.get("1.0", "end")
    assert "Player:||true" in content
    assert "|joined|false" in content
    assert window.filter_non_matching_var.get() is True
    assert window.event_gap_var.get() == 3.0
    assert window.ocr_confidence_var.get() == 22


def test_advanced_settings_round_trip_preserves_quality_and_logging() -> None:
    source = _make_window_stub(
        patterns="Player:||true",
        filter_non_matching=True,
        gap=2.0,
        confidence=30,
        video_quality="480p",
        logging_enabled=True,
    )
    target = _make_window_stub()

    settings = source.get_advanced_settings()
    target.apply_advanced_settings(settings)

    reapplied = target.get_advanced_settings()
    assert reapplied.video_quality == "480p"
    assert reapplied.logging_enabled is True
    assert reapplied.filter_non_matching is True


def test_advanced_settings_round_trip_preserves_tolerance_and_gating() -> None:
    source = _make_window_stub(
        patterns="Player:||true",
        tolerance_value=0.63,
        gating_enabled=False,
        gating_threshold=0.18,
    )
    target = _make_window_stub()

    settings = source.get_advanced_settings()
    target.apply_advanced_settings(settings)

    reapplied = target.get_advanced_settings()
    assert reapplied.tolerance_value == 0.63
    assert reapplied.gating_enabled is False
    assert reapplied.gating_threshold == 0.18


def test_advanced_settings_defaults_include_best_quality_and_logging_off() -> None:
    window = _make_window_stub()

    settings = window.get_advanced_settings()

    assert settings.filter_non_matching is True
    assert settings.video_quality == "best"
    assert settings.logging_enabled is False
    assert settings.tolerance_value == 0.75
    assert settings.gating_enabled is False
    assert settings.gating_threshold == 0.02


def test_apply_advanced_settings_keeps_selected_video_quality() -> None:
    window = _make_window_stub()

    window.apply_advanced_settings(
        AdvancedSettings(
            context_patterns=[
                {"id": "default", "before_text": None, "after_text": "joined", "enabled": True}
            ],
            video_quality="720p",
            logging_enabled=False,
        )
    )

    assert window.video_quality_var.get() == "720p"


def test_update_filename_display_with_valid_url() -> None:
    window = _make_window_stub()

    with patch(
        "src.components.main_window.ExportService.generate_filename",
        return_value="scytcheck_test.csv",
    ):
        window.update_filename_display("https://youtube.com/watch?v=test")

    window.filename_display.configure.assert_called_with(
        text="scytcheck_test.csv", foreground="black"
    )


def test_update_filename_display_with_invalid_url() -> None:
    window = _make_window_stub()

    with patch(
        "src.components.main_window.ExportService.generate_filename",
        side_effect=ValueError("bad url"),
    ):
        window.update_filename_display("not-a-url")

    window.filename_display.configure.assert_called_with(
        text="(Invalid YouTube URL - filename will be generated from valid URL)",
        foreground="orange",
    )


def test_layout_labels_do_not_overlap_controls_at_min_window_size() -> None:
    with (
        patch("src.components.main_window.URLInput", _URLInputStub),
        patch("src.components.main_window.FileSelector", _FileSelectorStub),
        patch("src.components.main_window.ProgressDisplay", _ProgressDisplayStub),
        patch("src.components.main_window.ttk.Frame", _WidgetStub),
        patch("src.components.main_window.ttk.LabelFrame", _WidgetStub),
        patch("src.components.main_window.ttk.Label", _WidgetStub),
        patch("src.components.main_window.ttk.Button", _WidgetStub),
        patch("src.components.main_window.ttk.Checkbutton", _WidgetStub),
        patch("src.components.main_window.ttk.Spinbox", _WidgetStub),
        patch("src.components.main_window.tk.Text", _WidgetStub),
        patch("src.components.main_window.tk.BooleanVar", _VarStub),
        patch("src.components.main_window.tk.DoubleVar", _VarStub),
        patch("src.components.main_window.tk.IntVar", _VarStub),
    ):
        window = MainWindow(_RootStub())

    assert window.url_input.label.grid_kwargs["row"] < window.url_input.entry.grid_kwargs["row"]
    assert (
        window.file_selector.label.grid_kwargs["row"]
        < window.file_selector.entry.grid_kwargs["row"]
    )
    assert window.filename_label.grid_kwargs["row"] < window.filename_display.grid_kwargs["row"]
    assert window.event_gap_label.grid_kwargs["row"] == window.event_gap_spinbox.grid_kwargs["row"]
    assert (
        window.event_gap_label.grid_kwargs["column"]
        < window.event_gap_spinbox.grid_kwargs["column"]
    )
    assert (
        window.ocr_sensitivity_label.grid_kwargs["row"]
        == window.ocr_sensitivity_spinbox.grid_kwargs["row"]
    )
    assert (
        window.ocr_sensitivity_label.grid_kwargs["column"]
        < window.ocr_sensitivity_spinbox.grid_kwargs["column"]
    )
    assert window.tolerance_label.grid_kwargs["row"] == window.tolerance_spinbox.grid_kwargs["row"]
    assert (
        window.tolerance_label.grid_kwargs["column"]
        < window.tolerance_spinbox.grid_kwargs["column"]
    )
    assert (
        window.gating_enabled_check.grid_kwargs["row"]
        > window.tolerance_spinbox.grid_kwargs["row"]
    )
    assert (
        window.gating_threshold_label.grid_kwargs["row"]
        == window.gating_threshold_spinbox.grid_kwargs["row"]
    )


def test_primary_workflow_controls_and_shortcuts_are_wired() -> None:
    with (
        patch("src.components.main_window.URLInput", _URLInputStub),
        patch("src.components.main_window.FileSelector", _FileSelectorStub),
        patch("src.components.main_window.ProgressDisplay", _ProgressDisplayStub),
        patch("src.components.main_window.ttk.Frame", _WidgetStub),
        patch("src.components.main_window.ttk.LabelFrame", _WidgetStub),
        patch("src.components.main_window.ttk.Label", _WidgetStub),
        patch("src.components.main_window.ttk.Button", _WidgetStub),
        patch("src.components.main_window.ttk.Checkbutton", _WidgetStub),
        patch("src.components.main_window.ttk.Combobox", _WidgetStub),
        patch("src.components.main_window.ttk.Spinbox", _WidgetStub),
        patch("src.components.main_window.tk.Text", _WidgetStub),
        patch("src.components.main_window.tk.BooleanVar", _VarStub),
        patch("src.components.main_window.tk.DoubleVar", _VarStub),
        patch("src.components.main_window.tk.IntVar", _VarStub),
        patch("src.components.main_window.tk.StringVar", _VarStub),
    ):
        root = _RootStub()
        window = MainWindow(root)

    triggered = []
    window.set_analyze_command(lambda: triggered.append("analyze"))

    assert window.analyze_button is not None
    assert window.retry_export_button is not None
    assert "<Control-Return>" in root.bindings
    assert "<Alt-u>" in root.bindings
    assert "<Alt-o>" in root.bindings
    assert root.bindings["<Control-Return>"](None) == "break"
    assert triggered == ["analyze"]
    assert root.bindings["<Alt-u>"](None) == "break"
    assert window.url_input.entry.focused is True
    assert root.bindings["<Alt-o>"](None) == "break"
    assert window.file_selector.entry.focused is True


def test_tooltip_guidance_contains_low_quality_help() -> None:
    with (
        patch("src.components.main_window.URLInput", _URLInputStub),
        patch("src.components.main_window.FileSelector", _FileSelectorStub),
        patch("src.components.main_window.ProgressDisplay", _ProgressDisplayStub),
        patch("src.components.main_window.ttk.Frame", _WidgetStub),
        patch("src.components.main_window.ttk.LabelFrame", _WidgetStub),
        patch("src.components.main_window.ttk.Label", _WidgetStub),
        patch("src.components.main_window.ttk.Button", _WidgetStub),
        patch("src.components.main_window.ttk.Checkbutton", _WidgetStub),
        patch("src.components.main_window.ttk.Combobox", _WidgetStub),
        patch("src.components.main_window.ttk.Spinbox", _WidgetStub),
        patch("src.components.main_window.tk.Text", _WidgetStub),
        patch("src.components.main_window.tk.BooleanVar", _VarStub),
        patch("src.components.main_window.tk.DoubleVar", _VarStub),
        patch("src.components.main_window.tk.IntVar", _VarStub),
        patch("src.components.main_window.tk.StringVar", _VarStub),
    ):
        window = MainWindow(_RootStub())

    tooltip_texts = [tooltip.text for tooltip in window._tooltips]
    assert any(
        "Lower values may catch faint text but add false positives." in text
        for text in tooltip_texts
    )


def test_tolerance_spinbox_range_is_configured() -> None:
    with (
        patch("src.components.main_window.URLInput", _URLInputStub),
        patch("src.components.main_window.FileSelector", _FileSelectorStub),
        patch("src.components.main_window.ProgressDisplay", _ProgressDisplayStub),
        patch("src.components.main_window.ttk.Frame", _WidgetStub),
        patch("src.components.main_window.ttk.LabelFrame", _WidgetStub),
        patch("src.components.main_window.ttk.Label", _WidgetStub),
        patch("src.components.main_window.ttk.Button", _WidgetStub),
        patch("src.components.main_window.ttk.Checkbutton", _WidgetStub),
        patch("src.components.main_window.ttk.Combobox", _WidgetStub),
        patch("src.components.main_window.ttk.Spinbox", _WidgetStub),
        patch("src.components.main_window.tk.Text", _WidgetStub),
        patch("src.components.main_window.tk.BooleanVar", _VarStub),
        patch("src.components.main_window.tk.DoubleVar", _VarStub),
        patch("src.components.main_window.tk.IntVar", _VarStub),
        patch("src.components.main_window.tk.StringVar", _VarStub),
    ):
        window = MainWindow(_RootStub())

    assert window.tolerance_spinbox.options["from_"] == 0.60
    assert window.tolerance_spinbox.options["to"] == 0.95
    assert window.tolerance_spinbox.options["increment"] == 0.01
    tooltip_texts = [tooltip.text for tooltip in window._tooltips]
    assert any("more permissive" in text for text in tooltip_texts)


def test_gating_controls_are_configured() -> None:
    with (
        patch("src.components.main_window.URLInput", _URLInputStub),
        patch("src.components.main_window.FileSelector", _FileSelectorStub),
        patch("src.components.main_window.ProgressDisplay", _ProgressDisplayStub),
        patch("src.components.main_window.ttk.Frame", _WidgetStub),
        patch("src.components.main_window.ttk.LabelFrame", _WidgetStub),
        patch("src.components.main_window.ttk.Label", _WidgetStub),
        patch("src.components.main_window.ttk.Button", _WidgetStub),
        patch("src.components.main_window.ttk.Checkbutton", _WidgetStub),
        patch("src.components.main_window.ttk.Combobox", _WidgetStub),
        patch("src.components.main_window.ttk.Spinbox", _WidgetStub),
        patch("src.components.main_window.tk.Text", _WidgetStub),
        patch("src.components.main_window.tk.BooleanVar", _VarStub),
        patch("src.components.main_window.tk.DoubleVar", _VarStub),
        patch("src.components.main_window.tk.IntVar", _VarStub),
        patch("src.components.main_window.tk.StringVar", _VarStub),
    ):
        window = MainWindow(_RootStub())

    assert "Frame-Change Gating" in window.gating_enabled_check.options["text"]
    assert window.gating_threshold_spinbox.options["from_"] == 0.0
    assert window.gating_threshold_spinbox.options["to"] == 1.0
    assert window.gating_threshold_spinbox.options["increment"] == 0.01
    tooltip_texts = [tooltip.text.lower() for tooltip in window._tooltips]
    assert any("skips ocr" in text for text in tooltip_texts)
