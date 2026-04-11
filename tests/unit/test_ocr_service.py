from src.services.ocr_service import OCRService
from src.data.models import ContextPattern


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
