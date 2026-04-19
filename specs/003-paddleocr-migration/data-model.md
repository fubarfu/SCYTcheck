# Data Model: PaddleOCR Migration

## Entity: OCRBackendConfig

- Purpose: Runtime configuration used to initialize the OCR engine inside the application.
- Fields:
  - `engine_id: str` (`paddleocr`)
  - `language_mode: str` (`en`, `de`, or configured parity mode)
  - `confidence_threshold: int`
  - `use_text_detection: bool`
  - `model_root: str`
  - `det_model_dir: str`
  - `rec_model_dir: str`
  - `runtime_available: bool`
- Validation:
  - `confidence_threshold` is clamped to `0..100`
  - model directories must resolve to local readable paths in packaged mode
  - engine initialization failure must surface a user-facing diagnostic

## Entity: BundledOCRAsset

- Purpose: Describes a PaddleOCR runtime/model asset expected in the portable release.
- Fields:
  - `asset_id: str`
  - `relative_path: str`
  - `asset_type: str` (`runtime`, `det_model`, `rec_model`, `support_file`)
  - `required_for_startup: bool`
  - `required_for_analysis: bool`
- Rules:
  - all required assets must be present in the release bundle for offline use
  - missing required assets block OCR startup and trigger a clear error

## Entity: OCRTextLine

- Purpose: Normalized OCR output unit passed into existing matching and export logic.
- Fields:
  - `text: str`
  - `normalized_text: str`
  - `confidence: int`
  - `bounding_box: object | None`
  - `source_region_id: str | None`
- Invariants:
  - `text` preserves human-readable OCR content
  - `normalized_text` follows existing whitespace normalization rules before matching
  - confidence values are mapped into the same thresholding semantics used by the app

## Entity: LegacyOCRSettingsPayload

- Purpose: Represents persisted settings originating from Tesseract-based releases.
- Fields:
  - `ocr_confidence_threshold: int | None`
  - `video_quality: str | None`
  - `logging_enabled: bool | None`
  - `context_patterns: list[dict[str, object]] | None`
  - `legacy_engine_fields: dict[str, object]`
- Rules:
  - relevant non-engine-specific fields remain preserved
  - obsolete engine-specific fields are ignored or migrated without causing load failure

## Entity: OCRBaselineComparisonResult

- Purpose: Captures release-gate comparison between the current baseline and the migrated OCR engine.
- Fields:
  - `sample_id: str`
  - `baseline_correct_names: int`
  - `candidate_correct_names: int`
  - `baseline_false_positives: int`
  - `candidate_false_positives: int`
  - `improvement_ratio: float`
  - `notes: str`
- Rules:
  - comparison records are repeatable across the maintained reference validation set
  - release readiness is judged from aggregate improvement, not isolated anecdotal wins
