# Contract: OCR Service

**Purpose**: Interface for OCR detection plus player-name extraction and normalization.

**Methods**:
- `detect_text(image: np.ndarray, region: tuple[int, int, int, int]) -> list[str]`
	- Detect text lines from one ROI.
- `set_confidence_threshold(value: int) -> None`
	- Updates OCR sensitivity used during detection.
- `preprocess_image(image: np.ndarray) -> np.ndarray`
	- Applies OCR preprocessing pipeline.
- `extract_player_name(line: str, pattern: ContextPattern) -> str | None`
	- Applies before/after matching and extraction rule:
		- after-only -> text before match
		- before-only -> text after match
		- both -> text between matches
- `normalize_name(name: str) -> str`
	- lowercase + trim + collapse repeated internal whitespace.
- `detect_player_candidates(image: np.ndarray, region: tuple[int, int, int, int], patterns: list[ContextPattern], filter_non_matching: bool) -> list[TextDetection]`
	- Performs OCR and returns extracted candidate detections.
- `build_log_record(detection: TextDetection, accepted: bool, rejection_reason: str, matched_pattern: str | None) -> dict[str, str]`
	- Builds one audit row for sidecar log CSV with fixed schema.

**Exceptions**:
- `OCRError`: When text detection fails
- `PatternValidationError`: Invalid context pattern definition (both before/after missing)

**Dependencies**: pytesseract, opencv-python

**Behavioral Guarantees**:
- Pattern matching is case-insensitive fuzzy substring matching on normalized OCR text with configurable threshold (default `0.75`), scanning for the best matching occurrence anywhere in the normalized text rather than performing a whole-block comparison.
- OCR text normalization for matching removes line breaks and collapses repeated whitespace runs to single spaces.
- If context text is clipped by region boundaries, matches are accepted when at least two contiguous boundary characters overlap or fuzzy similarity meets threshold.
- If `filter_non_matching` is true, lines that match no enabled pattern are excluded.
- For lines that do match configured patterns, extraction is recall-first and avoids additional suppression that would drop plausible context-matched names.
- Returned detections include `raw_ocr_text`, `extracted_name`, and `normalized_name`.
- Log row schema is deterministic when logging is enabled: `TimestampSec, RawString, TestedStringRaw, TestedStringNormalized, Accepted, RejectionReason, ExtractedName, RegionId, MatchedPattern, NormalizedName, OccurrenceCount, StartTimestamp, EndTimestamp, RepresentativeRegion`.
- `TestedStringRaw` and `TestedStringNormalized` are populated for accepted and rejected candidate rows to support false-negative debugging.
- `TimestampSec`, `StartTimestamp`, and `EndTimestamp` are formatted as `HH:MM:SS.mmm`.