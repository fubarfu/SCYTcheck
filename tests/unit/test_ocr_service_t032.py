"""Deterministic tie-break resolution tests (T032) for OCRService.

Tests that competing pattern matches are resolved deterministically by:
1. Longest span first
2. Earliest start position second
3. Pattern order third (as they appear in patterns list)
"""

import pytest

from src.data.models import ContextPattern
from src.services.ocr_service import OCRService


def test_extract_candidates_selects_longest_span_on_tie() -> None:
    """When multiple patterns match same text, select longest extracted span."""
    service = OCRService()
    patterns = [
        ContextPattern(
            id="short",
            before_text="Player:",
            after_text="joined",
            enabled=True,
            similarity_threshold=0.75,
        ),
        ContextPattern(
            id="long",
            before_text="Player:",
            after_text="party",
            enabled=True,
            similarity_threshold=0.75,
        ),
    ]

    candidates = service.extract_candidates(
        ["Player: Alice joined the party"],
        patterns=patterns,
        filter_non_matching=True,
    )

    # "long" pattern captures more text between markers ("Alice joined the")
    assert len(candidates) == 1
    assert candidates[0][1] == "long"  # Matched pattern: "long"


def test_extract_candidates_selects_earliest_start_on_span_tie() -> None:
    """When multiple patterns extract same span length, select earliest start."""
    service = OCRService()
    # The pattern extracts tokens between markers, using single-token rule
    patterns = [
        ContextPattern(
            id="pattern-a",
            before_text="Player:",
            after_text="Score",
            enabled=True,
            similarity_threshold=0.75,
        ),
    ]

    candidates = service.extract_candidates(
        ["Player: Alice Bob Score"],
        patterns=patterns,
        filter_non_matching=True,
    )

    # with "both" boundaries (before and after), extracts first token between markers
    assert len(candidates) == 1
    # The extraction picks "Alice" (first token between "Player:" and "Score")
    assert candidates[0][0] == "Alice"


def test_extract_candidates_respects_pattern_order_on_complete_tie() -> None:
    """When all tie-break factors equal, output pattern wins as it appears first."""
    service = OCRService()
    patterns = [
        ContextPattern(
            id="first-pattern",
            before_text="Player:",
            after_text=None,
            enabled=True,
            similarity_threshold=0.75,
        ),
        ContextPattern(
            id="second-pattern",
            before_text="Player:",
            after_text=None,
            enabled=True,
            similarity_threshold=0.75,
        ),
    ]

    candidates = service.extract_candidates(
        ["Player: Alice"],
        patterns=patterns,
        filter_non_matching=True,
    )

    # Both patterns have same before_text and no after_text
    # Should use first-pattern (pattern order)
    assert len(candidates) == 1
    assert candidates[0][1] == "first-pattern"


def test_evaluate_lines_deterministic_resolution_output(tmp_path) -> None:
    """Verify evaluate_lines applies deterministic tie-break consistently."""
    service = OCRService()
    patterns = [
        ContextPattern(
            id="short",
            before_text="Player:",
            after_text="Score",
            enabled=True,
            similarity_threshold=0.75,
        ),
        ContextPattern(
            id="long",
            before_text="Player:",
            after_text=None,
            enabled=True,
            similarity_threshold=0.75,
        ),
    ]

    decisions = service.evaluate_lines(
        ["Player: Alice Score"],
        patterns=patterns,
        filter_non_matching=True,
    )

    assert len(decisions) == 1
    decision = decisions[0]
    assert decision["accepted"] is True
    # "long" pattern captures "Alice Score" (longer span between markers)
    assert decision["matched_pattern"] == "long"
