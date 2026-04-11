# Contract: OCR Service

**Purpose**: Interface for OCR detection plus player-name extraction and normalization.

**Methods**:
- `detect_text(image: np.ndarray, region: tuple[int, int, int, int]) -> list[str]`
	- Detect text lines from one ROI.
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

**Exceptions**:
- `OCRError`: When text detection fails
- `PatternValidationError`: Invalid context pattern definition (both before/after missing)

**Dependencies**: pytesseract, opencv-python

**Behavioral Guarantees**:
- Pattern matching is case-insensitive substring.
- If `filter_non_matching` is true, lines that match no enabled pattern are excluded.
- Returned detections include `raw_ocr_text`, `extracted_name`, and `normalized_name`.