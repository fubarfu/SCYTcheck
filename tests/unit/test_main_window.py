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


def _make_window_stub(patterns: str = "", filter_non_matching: bool = False, gap: float = 1.0) -> MainWindow:
    window = MainWindow.__new__(MainWindow)
    window.patterns_text = _TextStub(patterns)
    window.filter_non_matching_var = _VarStub(filter_non_matching)
    window.event_gap_var = _VarStub(gap)
    window.filename_display = MagicMock()
    window.url_input = SimpleNamespace(get=lambda: "")
    return window


def test_get_advanced_settings_parses_multiple_patterns() -> None:
    window = _make_window_stub(
        patterns="joined||true\n|connected|false\nprefix|suffix|true",
        filter_non_matching=True,
        gap=2.5,
    )

    settings = window.get_advanced_settings()

    assert settings.filter_non_matching is True
    assert settings.event_gap_threshold_sec == 2.5
    assert len(settings.context_patterns) == 3
    assert settings.context_patterns[0]["before_text"] == "joined"
    assert settings.context_patterns[0]["after_text"] is None
    assert settings.context_patterns[1]["before_text"] is None
    assert settings.context_patterns[1]["after_text"] == "connected"
    assert settings.context_patterns[1]["enabled"] is False


def test_get_advanced_settings_uses_defaults_when_patterns_empty() -> None:
    window = _make_window_stub(patterns="\n\n  ", filter_non_matching=False, gap=1.0)

    settings = window.get_advanced_settings()

    assert len(settings.context_patterns) == 2
    assert settings.context_patterns[0]["after_text"] == "joined"
    assert settings.context_patterns[1]["after_text"] == "connected"


def test_apply_advanced_settings_populates_controls() -> None:
    window = _make_window_stub()
    settings = AdvancedSettings(
        context_patterns=[
            {"id": "p1", "before_text": "Player:", "after_text": None, "enabled": True},
            {"id": "p2", "before_text": None, "after_text": "joined", "enabled": False},
        ],
        filter_non_matching=True,
        event_gap_threshold_sec=3.0,
    )

    window.apply_advanced_settings(settings)

    content = window.patterns_text.get("1.0", "end")
    assert "Player:||true" in content
    assert "|joined|false" in content
    assert window.filter_non_matching_var.get() is True
    assert window.event_gap_var.get() == 3.0


def test_update_filename_display_with_valid_url() -> None:
    window = _make_window_stub()

    with patch("src.components.main_window.ExportService.generate_filename", return_value="scytcheck_test.csv"):
        window.update_filename_display("https://youtube.com/watch?v=test")

    window.filename_display.configure.assert_called_with(text="scytcheck_test.csv", foreground="black")


def test_update_filename_display_with_invalid_url() -> None:
    window = _make_window_stub()

    with patch("src.components.main_window.ExportService.generate_filename", side_effect=ValueError("bad url")):
        window.update_filename_display("not-a-url")

    window.filename_display.configure.assert_called_with(
        text="(Invalid YouTube URL - filename will be generated from valid URL)",
        foreground="orange",
    )
