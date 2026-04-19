from __future__ import annotations

from src.data.models import ContextPattern
from src.services.ocr_service import OCRService


def _accepted_count(lines: list[str], tolerance: float) -> int:
    service = OCRService()
    accepted = 0
    for line in lines:
        decisions = service.evaluate_lines(
            [line],
            patterns=[
                ContextPattern(
                    id="played",
                    before_text="Played",
                    after_text=None,
                    enabled=True,
                )
            ],
            filter_non_matching=True,
            tolerance_threshold=tolerance,
        )
        accepted += sum(1 for decision in decisions if bool(decision["accepted"]))
    return accepted


def test_sc002_relaxed_tolerance_improves_recovery_by_at_least_20_percent() -> None:
    lines = [
        "Played Alice",
        "Played Bob",
        "Pxyzed Carol",
        "Plxxed Dora",
        "Pxyzed Evan",
        "Plxxed Finn",
        "Played Gina",
        "Played Hugo",
        "P1xye# Ivy",
        "P1xye# Jay",
    ]

    strict = _accepted_count(lines, 0.75)
    relaxed = _accepted_count(lines, 0.65)

    improvement_ratio = (relaxed - strict) / strict if strict > 0 else 0.0

    assert relaxed >= strict
    assert improvement_ratio >= 0.20
