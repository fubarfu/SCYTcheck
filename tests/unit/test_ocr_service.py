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
