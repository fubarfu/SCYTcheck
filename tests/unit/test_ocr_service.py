from pathlib import Path
from unittest.mock import patch

import numpy as np

from src.data.models import ContextPattern
from src.services.ocr_service import OCRError, OCRService


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

    assert candidates == [("Alice", "joined")]


def test_extract_candidates_includes_unmatched_when_filter_disabled() -> None:
    service = OCRService()
    patterns = [ContextPattern(id="joined", before_text=None, after_text="joined", enabled=True)]

    candidates = service.extract_candidates(
        ["Alice joined", "Raw OCR Name"],
        patterns=patterns,
        filter_non_matching=False,
    )

    assert candidates == [("Alice", "joined")]


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

    assert candidates == [("Alice", "short")]


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


def test_build_joined_region_text_collapses_multiline_input() -> None:
    assert OCRService.build_joined_region_text(
        [" Joined by", "", "Alice\nRank "]
    ) == "Joined by Alice Rank"


def test_evaluate_lines_joined_only_returns_single_decision_for_multiple_lines() -> None:
    service = OCRService()
    patterns = [
        ContextPattern(id="joined", before_text="Joined by", after_text="Rank", enabled=True),
    ]

    decisions = service.evaluate_lines(
        ["Joined", "by", "Alice", "Rank"],
        patterns=patterns,
        filter_non_matching=True,
    )

    assert len(decisions) == 1
    assert decisions[0]["accepted"] is True
    assert decisions[0]["extracted_name"] == "Alice"


def test_detect_text_with_diagnostics_reports_empty_crop() -> None:
    service = OCRService()
    image = np.zeros((8, 8, 3), dtype=np.uint8)

    tokens, diagnostics = service.detect_text_with_diagnostics(image, (0, 0, 0, 4))

    assert tokens == []
    assert diagnostics[0]["rejection_reason"] == "empty_crop"


def test_detect_text_with_diagnostics_reports_low_confidence() -> None:
    service = OCRService(confidence_threshold=40)
    image = np.zeros((16, 16, 3), dtype=np.uint8)

    fake_engine = type(
        "FakeEngine",
        (),
        {
            "ocr": lambda *_args, **_kwargs: [
                [
                    [None, ("Alice", 0.12)],
                    [None, ("Bob", 0.85)],
                ]
            ]
        },
    )()

    with patch.object(service, "_get_ocr_engine", return_value=fake_engine):
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

    fake_engine = type(
        "FakeEngine",
        (),
        {
            "ocr": lambda *_args, **_kwargs: [
                [
                    [None, ("Alice joined", 0.80)],
                    [None, ("Bob left", 0.80)],
                ]
            ]
        },
    )()

    with patch.object(service, "_get_ocr_engine", return_value=fake_engine):
        tokens, diagnostics = service.detect_text_with_diagnostics(image, (0, 0, 16, 16))

    assert tokens == ["Alice joined", "Bob left"]
    assert [row["raw_string"] for row in diagnostics if row["accepted"]] == [
        "Alice joined",
        "Bob left",
    ]


def test_ocr_initialization_failure_raises_clear_error() -> None:
    service = OCRService(confidence_threshold=40, paddleocr_model_root="Z:/missing/models")

    with patch.object(service, "_notify_ocr_initialization_failure") as notify:
        with patch("src.services.ocr_service.PaddleOCR", side_effect=RuntimeError("boom")):
            with patch.object(service, "_resolve_model_dirs", return_value=(None, None, None)):
                try:
                    service._create_ocr_engine()
                except OCRError as exc:
                    assert "Failed to initialize PaddleOCR" in str(exc)
                else:  # pragma: no cover - explicit test failure path
                    raise AssertionError("Expected OCRError")

    notify.assert_called_once()


def test_ocr_import_failure_writes_log_hint() -> None:
    service = OCRService(confidence_threshold=40, paddleocr_model_root="C:/models")

    with patch("src.services.ocr_service.PaddleOCR", None):
        with patch("src.services.ocr_service._PADDLEOCR_IMPORT_ERROR", None):
            with patch(
                "src.services.ocr_service.import_module", side_effect=RuntimeError("missing dll")
            ):
                try:
                    service._create_ocr_engine()
                except OCRError as exc:
                    assert "PaddleOCR runtime is not available" in str(exc)
                    assert "missing dll" in str(exc)
                else:  # pragma: no cover - explicit test failure path
                    raise AssertionError("Expected OCRError")


def test_resolve_model_dirs_requires_cls(tmp_path: Path) -> None:
    root = tmp_path / "models"
    (root / "det_en").mkdir(parents=True)
    (root / "rec_en").mkdir(parents=True)

    service = OCRService(confidence_threshold=40, paddleocr_model_root=str(root))

    with patch("src.config._candidate_paddleocr_model_roots", return_value=[root]):
        try:
            service._resolve_model_dirs()
        except OCRError as exc:
            assert "det*, rec*, and cls*" in str(exc)
        else:  # pragma: no cover - explicit test failure path
            raise AssertionError("Expected OCRError")


# ---------------------------------------------------------------------------
# T028 – OCR line aggregation / normalization
# ---------------------------------------------------------------------------


def test_normalize_for_matching_collapses_whitespace() -> None:
    assert OCRService.normalize_for_matching("  Alice   Wonder  ") == "Alice Wonder"


def test_normalize_for_matching_removes_newlines() -> None:
    assert OCRService.normalize_for_matching("Alice\nWonder\r\nRank") == "Alice Wonder Rank"


def test_normalize_for_matching_empty_string_returns_empty() -> None:
    assert OCRService.normalize_for_matching("") == ""


def test_normalize_for_matching_multiline_irregular_whitespace() -> None:
    source = "  Name:\n   Alice\r\n   Expert  "
    assert OCRService.normalize_for_matching(source) == "Name: Alice Expert"


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


def test_extract_with_boundaries_before_only_on_multiline_text() -> None:
    value = OCRService.extract_with_boundaries(
        line="Player:\nAlice Wonder",
        before_text="Player:",
    )
    assert value == "Alice"


def test_extract_with_boundaries_after_only_on_multiline_text() -> None:
    value = OCRService.extract_with_boundaries(
        line="Alice Wonder\nScore",
        after_text="Score",
    )
    assert value == "Wonder"


def test_extract_with_boundaries_both_boundaries_on_multiline_text() -> None:
    value = OCRService.extract_with_boundaries(
        line="Joined by\nAlice\nRank",
        before_text="Joined by",
        after_text="Rank",
    )
    assert value == "Alice"


def test_find_in_text_default_threshold_matches_multiline_after_normalization() -> None:
    normalized = OCRService.normalize_for_matching("Started\nby Alice")
    span = OCRService._find_in_text("Started by", normalized)
    assert span == (0, len("Started by"))


def test_find_in_text_threshold_sensitivity_across_supported_range() -> None:
    text = "P1ayer: Alice"

    assert OCRService._find_in_text("Player", text, threshold=0.60) is not None
    assert OCRService._find_in_text("Player", text, threshold=0.75) is not None
    assert OCRService._find_in_text("Player", text, threshold=0.95) is None


def test_find_in_text_ocr_substitutions_respect_thresholds() -> None:
    text = "P1ayed by Alice"

    assert OCRService._find_in_text("Played", text, threshold=0.60) is not None
    assert OCRService._find_in_text("Played", text, threshold=0.75) is not None
    assert OCRService._find_in_text("Played", text, threshold=0.95) is None


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
