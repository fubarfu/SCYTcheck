from __future__ import annotations

from unittest.mock import patch

from src.components.main_window import MainWindow
from src.config import load_advanced_settings, save_advanced_settings


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
        self.options = dict(kwargs)
        self.focused = False

    def grid(self, **_kwargs):
        return None

    def configure(self, **kwargs):
        self.options.update(kwargs)

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

    def grid(self, *_args, **_kwargs):
        return None

    def get(self):
        return ""


class _FileSelectorStub:
    def __init__(self, _parent):
        self.label = _WidgetStub()
        self.entry = _WidgetStub()
        self.button = _WidgetStub()

    def grid(self, *_args, **_kwargs):
        return None


class _ProgressDisplayStub:
    def __init__(self, _parent):
        return None

    def grid(self, *_args, **_kwargs):
        return None


def _window_stub(
    patterns: str,
    filter_non_matching: bool,
    gap: float,
    confidence: int = 40,
    video_quality: str = "best",
    logging_enabled: bool = False,
) -> MainWindow:
    window = MainWindow.__new__(MainWindow)
    window.patterns_text = _TextStub(patterns)
    window.filter_non_matching_var = _VarStub(filter_non_matching)
    window.event_gap_var = _VarStub(gap)
    window.ocr_confidence_var = _VarStub(confidence)
    window.video_quality_var = _VarStub(video_quality)
    window.logging_enabled_var = _VarStub(logging_enabled)
    return window


def test_advanced_settings_first_run_defaults_and_persistence(tmp_path) -> None:
    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.filter_non_matching is True
    assert loaded.event_gap_threshold_sec == 1.0
    assert loaded.ocr_confidence_threshold == 40
    assert loaded.video_quality == "best"
    assert loaded.logging_enabled is False
    assert len(loaded.context_patterns) == 4
    assert loaded.context_patterns[0]["before_text"] is None
    assert loaded.context_patterns[0]["after_text"] == "has joined"
    assert loaded.context_patterns[1]["before_text"] == "Party"
    assert loaded.context_patterns[1]["after_text"] == "connected"
    assert loaded.context_patterns[2]["before_text"] == "Party"
    assert loaded.context_patterns[2]["after_text"] == "disconnected"
    assert loaded.context_patterns[3]["before_text"] == "started by"
    assert loaded.context_patterns[3]["after_text"] is None
    assert (tmp_path / "scytcheck_settings.json").exists()


def test_advanced_settings_ui_to_disk_roundtrip(tmp_path) -> None:
    window = _window_stub(
        patterns="Player:||true\n|connected|false\nstart|end|true",
        filter_non_matching=True,
        gap=1.7,
        confidence=23,
        video_quality="480p",
        logging_enabled=True,
    )

    from_ui = window.get_advanced_settings()
    save_advanced_settings(from_ui, base_dir=str(tmp_path))

    reloaded = load_advanced_settings(base_dir=str(tmp_path))

    assert reloaded.filter_non_matching is True
    assert reloaded.event_gap_threshold_sec == 1.7
    assert reloaded.ocr_confidence_threshold == 23
    assert reloaded.video_quality == "480p"
    assert reloaded.logging_enabled is True
    assert len(reloaded.context_patterns) == 3
    assert reloaded.context_patterns[0]["before_text"] == "Player:"
    assert reloaded.context_patterns[1]["after_text"] == "connected"
    assert reloaded.context_patterns[1]["enabled"] is False


def test_advanced_settings_workflow_applies_reloaded_values(tmp_path) -> None:
    saved = _window_stub(
        patterns="Player:||true\n|connected|true",
        filter_non_matching=True,
        gap=2.2,
        confidence=18,
        video_quality="720p",
        logging_enabled=True,
    ).get_advanced_settings()
    save_advanced_settings(saved, base_dir=str(tmp_path))

    window = _window_stub(patterns="", filter_non_matching=False, gap=1.0, confidence=40)
    window.apply_advanced_settings(load_advanced_settings(base_dir=str(tmp_path)))

    assert window.filter_non_matching_var.get() is True
    assert float(window.event_gap_var.get()) == 2.2
    assert int(window.ocr_confidence_var.get()) == 18
    assert window.video_quality_var.get() == "720p"
    assert window.logging_enabled_var.get() is True
    assert "Player:||true" in window.patterns_text.get("1.0", "end")


def test_low_quality_warning_and_sensitivity_tuning_flow(tmp_path) -> None:
    guidance = (
        "Low-quality videos can reduce OCR reliability. Lower confidence to improve recall, "
        "or raise it to reduce false positives."
    )
    assert "Low-quality videos can reduce OCR reliability" in guidance
    assert "improve recall" in guidance

    window = _window_stub(patterns="|joined|true", filter_non_matching=True, gap=1.0, confidence=12)
    tuned = window.get_advanced_settings()
    save_advanced_settings(tuned, base_dir=str(tmp_path))

    reloaded = load_advanced_settings(base_dir=str(tmp_path))
    assert reloaded.ocr_confidence_threshold == 12


def test_keyboard_only_main_workflow_shortcuts(tmp_path) -> None:
    del tmp_path
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

    assert root.bindings["<Control-Return>"](None) == "break"
    assert root.bindings["<Alt-u>"](None) == "break"
    assert root.bindings["<Alt-o>"](None) == "break"
    assert triggered == ["analyze"]
    assert window.url_input.entry.focused is True
    assert window.file_selector.entry.focused is True
