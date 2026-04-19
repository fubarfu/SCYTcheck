from __future__ import annotations

from src.config import AdvancedSettings, load_advanced_settings, save_advanced_settings
from src.data.models import ContextPattern
from src.services.ocr_service import OCRService


def _count_matches(lines: list[str], tolerance: float) -> int:
    service = OCRService()
    patterns = [ContextPattern(id="played", before_text="Played", after_text=None, enabled=True)]
    accepted = 0
    for line in lines:
        decisions = service.evaluate_lines(
            [line],
            patterns=patterns,
            filter_non_matching=True,
            tolerance_threshold=tolerance,
        )
        accepted += sum(1 for decision in decisions if bool(decision["accepted"]))
    return accepted


def test_us2_relaxed_tolerance_recovers_more_matches() -> None:
    lines = [
        "Pxyzed Alice",  # fuzz ratio ~= 0.67 to "Played"
        "Plxxed Bob",    # fuzz ratio ~= 0.67 to "Played"
        "Played Carol",  # clean baseline
    ]

    relaxed_matches = _count_matches(lines, 0.65)
    default_matches = _count_matches(lines, 0.75)

    assert relaxed_matches >= default_matches
    assert relaxed_matches > default_matches


def test_us2_tolerance_persists_across_reload(tmp_path) -> None:
    settings = AdvancedSettings(
        context_patterns=[
            {
                "id": "default-joined",
                "before_text": None,
                "after_text": "joined",
                "enabled": True,
            }
        ],
        tolerance_value=0.65,
    )

    save_advanced_settings(settings, str(tmp_path))
    reloaded = load_advanced_settings(str(tmp_path))

    assert reloaded.tolerance_value == 0.65


def test_us2_regression_relaxed_threshold_is_superset_of_default_acceptance() -> None:
    lines = [
        "Played Alice",
        "Pxyzed Bob",
        "Plxxed Carol",
        "P1xye# Dave",
    ]

    default_matches = _count_matches(lines, 0.75)
    relaxed_matches = _count_matches(lines, 0.60)

    assert relaxed_matches >= default_matches
