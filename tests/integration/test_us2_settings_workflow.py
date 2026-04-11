from __future__ import annotations

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


def _window_stub(patterns: str, filter_non_matching: bool, gap: float, confidence: int = 40) -> MainWindow:
    window = MainWindow.__new__(MainWindow)
    window.patterns_text = _TextStub(patterns)
    window.filter_non_matching_var = _VarStub(filter_non_matching)
    window.event_gap_var = _VarStub(gap)
    window.ocr_confidence_var = _VarStub(confidence)
    return window


def test_advanced_settings_first_run_defaults_and_persistence(tmp_path) -> None:
    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.filter_non_matching is True
    assert loaded.event_gap_threshold_sec == 1.0
    assert loaded.ocr_confidence_threshold == 40
    assert len(loaded.context_patterns) == 2
    assert loaded.context_patterns[0]["after_text"] == "joined"
    assert (tmp_path / "scytcheck_settings.json").exists()


def test_advanced_settings_ui_to_disk_roundtrip(tmp_path) -> None:
    window = _window_stub(
        patterns="Player:||true\n|connected|false\nstart|end|true",
        filter_non_matching=True,
        gap=1.7,
        confidence=23,
    )

    from_ui = window.get_advanced_settings()
    save_advanced_settings(from_ui, base_dir=str(tmp_path))

    reloaded = load_advanced_settings(base_dir=str(tmp_path))

    assert reloaded.filter_non_matching is True
    assert reloaded.event_gap_threshold_sec == 1.7
    assert reloaded.ocr_confidence_threshold == 23
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
    ).get_advanced_settings()
    save_advanced_settings(saved, base_dir=str(tmp_path))

    window = _window_stub(patterns="", filter_non_matching=False, gap=1.0, confidence=40)
    window.apply_advanced_settings(load_advanced_settings(base_dir=str(tmp_path)))

    assert window.filter_non_matching_var.get() is True
    assert float(window.event_gap_var.get()) == 2.2
    assert int(window.ocr_confidence_var.get()) == 18
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
