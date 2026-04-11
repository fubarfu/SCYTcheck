from unittest.mock import patch

import numpy as np

from src.data.models import ContextPattern
from src.services.ocr_service import OCRService


def test_extract_with_boundaries_before_only() -> None:
    value = OCRService.extract_with_boundaries(
        line="Player: Alice Wonder",
        before_text="Player:",
    )
    assert value == "Alice Wonder"


def test_extract_with_boundaries_after_only() -> None:
    value = OCRService.extract_with_boundaries(
        line="Alice Wonder Rank",
        after_text="Rank",
    )
    assert value == "Alice Wonder"


def test_extract_with_boundaries_before_and_after() -> None:
    value = OCRService.extract_with_boundaries(
        line="Name Alice Wonder Score",
        before_text="Name",
        after_text="Score",
    )
    assert value == "Alice Wonder"


def test_extract_candidates_preserves_all_context_matched_non_empty() -> None:
    service = OCRService()
    patterns = [
        ContextPattern(id="joined", before_text=None, after_text="joined", enabled=True),
        ContextPattern(id="player", before_text="Player:", after_text=None, enabled=True),
    ]

    candidates = service.extract_candidates(
        [
            "Alice joined",
            "Player: Alice",
            "  ",
            "Bob joined",
        ],
        patterns=patterns,
        filter_non_matching=True,
    )

    assert candidates == [
        ("Alice", "joined"),
        ("Alice", "player"),
        ("Bob", "joined"),
    ]


def test_extract_candidates_includes_unmatched_when_filter_disabled() -> None:
    service = OCRService()
    patterns = [ContextPattern(id="joined", before_text=None, after_text="joined", enabled=True)]

    candidates = service.extract_candidates(
        ["Alice joined", "Raw OCR Name"],
        patterns=patterns,
        filter_non_matching=False,
    )

    assert candidates == [("Alice", "joined"), ("Raw OCR Name", None)]


def test_extract_candidates_resolves_multi_pattern_conflicts_deterministically() -> None:
    service = OCRService()
    patterns = [
        ContextPattern(id="short", before_text="Player:", after_text="joined", enabled=True),
        ContextPattern(id="long", before_text="Player:", after_text="party", enabled=True),
    ]

    candidates = service.extract_candidates(
        ["Player: Alice joined the party"],
        patterns=patterns,
        filter_non_matching=True,
    )

    assert candidates == [("Alice joined the", "long")]


def test_evaluate_lines_marks_rejected_when_filter_requires_pattern_match() -> None:
    service = OCRService()
    patterns = [ContextPattern(id="joined", before_text=None, after_text="joined", enabled=True)]

    decisions = service.evaluate_lines(
        ["Raw OCR Name"],
        patterns=patterns,
        filter_non_matching=True,
    )

    assert decisions == [
        {
            "raw_string": "Raw OCR Name",
            "accepted": False,
            "rejection_reason": "no_pattern_match",
            "extracted_name": "",
            "matched_pattern": None,
        }
    ]


def test_detect_text_with_diagnostics_reports_empty_crop() -> None:
    service = OCRService()
    image = np.zeros((8, 8, 3), dtype=np.uint8)

    tokens, diagnostics = service.detect_text_with_diagnostics(image, (0, 0, 0, 4))

    assert tokens == []
    assert diagnostics[0]["rejection_reason"] == "empty_crop"


def test_detect_text_with_diagnostics_reports_low_confidence() -> None:
    service = OCRService(confidence_threshold=40)
    image = np.zeros((16, 16, 3), dtype=np.uint8)

    with patch("src.services.ocr_service.pytesseract.image_to_data") as image_to_data:
        image_to_data.return_value = {
            "text": ["Alice", "Bob"],
            "conf": ["12", "85"],
        }
        tokens, diagnostics = service.detect_text_with_diagnostics(image, (0, 0, 16, 16))

    assert tokens == ["Bob"]
    assert any(
        row["raw_string"] == "Alice"
        and row["accepted"] is False
        and row["rejection_reason"] == "low_confidence"
        for row in diagnostics
    )
