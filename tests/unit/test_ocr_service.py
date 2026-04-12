from unittest.mock import patch

import numpy as np

from src.data.models import ContextPattern
from src.services.ocr_service import OCRService


def test_extract_with_boundaries_before_only() -> None:
    value = OCRService.extract_with_boundaries(
        line="Player: Alice Wonder",
        before_text="Player:",
    )
    assert value == "Alice"


def test_extract_with_boundaries_after_only() -> None:
    value = OCRService.extract_with_boundaries(
        line="Alice Wonder Rank",
        after_text="Rank",
    )
    assert value == "Wonder"


def test_extract_with_boundaries_before_and_after() -> None:
    value = OCRService.extract_with_boundaries(
        line="Name Alice Wonder Score",
        before_text="Name",
        after_text="Score",
    )
    assert value == "Alice"


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

    assert candidates == [("Alice", "long")]


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
            "tested_string_raw": "Raw OCR Name",
            "tested_string_normalized": "Raw OCR Name",
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


def test_detect_text_with_diagnostics_aggregates_tokens_to_lines() -> None:
    service = OCRService(confidence_threshold=40)
    image = np.zeros((16, 16, 3), dtype=np.uint8)

    with patch("src.services.ocr_service.pytesseract.image_to_data") as image_to_data:
        image_to_data.return_value = {
            "text": ["Alice", "joined", "Bob", "left"],
            "conf": ["80", "80", "80", "80"],
            "block_num": [1, 1, 1, 1],
            "par_num": [1, 1, 1, 1],
            "line_num": [1, 1, 2, 2],
        }
        tokens, diagnostics = service.detect_text_with_diagnostics(image, (0, 0, 16, 16))

    assert tokens == ["Alice joined", "Bob left"]
    assert [row["raw_string"] for row in diagnostics if row["accepted"]] == [
        "Alice joined",
        "Bob left",
    ]


# ---------------------------------------------------------------------------
# T028 – OCR line aggregation / normalization
# ---------------------------------------------------------------------------


def test_normalize_for_matching_collapses_whitespace() -> None:
    assert OCRService.normalize_for_matching("  Alice   Wonder  ") == "Alice Wonder"


def test_normalize_for_matching_removes_newlines() -> None:
    assert OCRService.normalize_for_matching("Alice\nWonder\r\nRank") == "Alice Wonder Rank"


def test_normalize_for_matching_empty_string_returns_empty() -> None:
    assert OCRService.normalize_for_matching("") == ""


# ---------------------------------------------------------------------------
# T029 – Fuzzy substring matching (threshold and best-occurrence scan)
# ---------------------------------------------------------------------------


def test_find_in_text_exact_match_returns_span() -> None:
    span = OCRService._find_in_text("Player", "Player: Alice")
    assert span == (0, 6)


def test_find_in_text_exact_match_case_insensitive() -> None:
    span = OCRService._find_in_text("player", "Player: Alice")
    assert span == (0, 6)


def test_find_in_text_fuzzy_match_above_threshold() -> None:
    # "Plyaer" typo should fuzzily match "Player"
    span = OCRService._find_in_text("Player", "Plyaer: Alice", threshold=0.7)
    assert span is not None
    assert span[1] - span[0] == len("Player")


def test_find_in_text_returns_none_below_threshold() -> None:
    # Completely different text should not match above default threshold
    span = OCRService._find_in_text("Player", "XXXXXX", threshold=0.75)
    assert span is None


def test_find_in_text_returns_none_empty_pattern() -> None:
    assert OCRService._find_in_text("", "Player: Alice") is None


def test_find_in_text_returns_none_empty_text() -> None:
    assert OCRService._find_in_text("Player", "") is None


# ---------------------------------------------------------------------------
# T030 – Boundary-clipped matching (≥2-char overlap at OCR region edge)
# ---------------------------------------------------------------------------


def test_find_in_text_boundary_clipped_at_start_of_text() -> None:
    # Pattern "Player" clipped at start: text begins with tail "layer"
    span = OCRService._find_in_text("Player", "layer: Alice")
    assert span is not None
    assert span[0] == 0


def test_find_in_text_boundary_clipped_at_end_of_text() -> None:
    # Pattern "Rank" clipped at end: text ends with head "Ra"
    span = OCRService._find_in_text("Rank", "Alice Ra")
    assert span is not None
    assert span[1] == len("Alice Ra")


def test_find_in_text_boundary_clipped_requires_at_least_two_chars() -> None:
    # Single-char overlap should NOT match
    span = OCRService._find_in_text("Player", "r: Alice")
    assert span is None


# ---------------------------------------------------------------------------
# T031 – Single-token extraction (after-only, before-only, both modes)
# ---------------------------------------------------------------------------


def test_extract_with_boundaries_before_only_keeps_first_token() -> None:
    # Multi-word after the marker → first token returned
    value = OCRService.extract_with_boundaries(
        line="Name: Alice Bob",
        before_text="Name:",
    )
    assert value == "Alice"


def test_extract_with_boundaries_after_only_keeps_last_token() -> None:
    # Multi-word before the marker → last token returned
    value = OCRService.extract_with_boundaries(
        line="Alice Bob Score",
        after_text="Score",
    )
    assert value == "Bob"


def test_extract_with_boundaries_both_keeps_first_token_between() -> None:
    # Multiple tokens between markers → first token returned
    value = OCRService.extract_with_boundaries(
        line="Name Alice Bob Score",
        before_text="Name",
        after_text="Score",
    )
    assert value == "Alice"


def test_extract_with_boundaries_returns_none_when_no_token_between() -> None:
    # Markers are adjacent with only whitespace between them → None
    value = OCRService.extract_with_boundaries(
        line="Name  Score",
        before_text="Name",
        after_text="Score",
    )
    assert value is None


def test_extract_with_boundaries_returns_none_when_marker_not_found() -> None:
    value = OCRService.extract_with_boundaries(
        line="Alice Wonder",
        before_text="Player:",
    )
    assert value is None


# ---------------------------------------------------------------------------
# T028 – evaluate_lines includes tested_string fields in decisions
# ---------------------------------------------------------------------------


def test_evaluate_lines_includes_tested_string_fields_in_accepted_decision() -> None:
    service = OCRService()
    patterns = [
        ContextPattern(id="player", before_text="Player:", after_text=None, enabled=True)
    ]

    decisions = service.evaluate_lines(
        ["Player: Alice"],
        patterns=patterns,
        filter_non_matching=True,
    )

    assert len(decisions) == 1
    decision = decisions[0]
    assert "tested_string_raw" in decision
    assert "tested_string_normalized" in decision
    assert decision["tested_string_raw"] == "Player: Alice"
    assert decision["tested_string_normalized"] == "Player: Alice"
