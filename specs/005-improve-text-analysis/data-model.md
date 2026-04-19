# Data Model: Improve Text Analysis

**Phase**: Phase 1 (Design)  
**Date**: 2026-04-15

## Entity: AnalysisToleranceSetting

Represents one global user-selected fuzzy matching tolerance for all enabled context patterns.

### Fields

- `tolerance_value: float` (range 0.60-0.95, default 0.75)
- `source: str` (`default` | `user-configured`)

### Validation

- Reject values outside [0.60, 0.95] at settings load/apply boundaries.
- Missing value falls back to 0.75.

### Relationships

- Applied to all boundary matching operations in joined-text extraction.

## Entity: JoinedRegionText

Canonical matching input produced from OCR lines for a single frame-region pair.

### Fields

- `region_id: str` (`x:y:w:h`)
- `frame_time_sec: float`
- `raw_lines: list[str]`
- `joined_text: str` (single normalized text block)
- `line_count: int`

### Transformation

1. Filter empty OCR lines.
2. Join with spaces.
3. Normalize whitespace/newlines to single-space text.

### Validation

- `joined_text` must contain no newline characters.
- `line_count` must equal number of retained non-empty lines.

### Relationships

- Input to joined-only boundary extraction.

## Entity: BoundaryMatchWindow

Represents the selected nearest bounded candidate window between boundary matches on joined text.

### Fields

- `pattern_id: str`
- `before_span: tuple[int, int] | None`
- `after_span: tuple[int, int] | None`
- `candidate_text: str`
- `token_count_between_boundaries: int`
- `is_nearest_valid_span: bool`

### Validation

- `token_count_between_boundaries <= 6` for accepted windows.
- Window must be nearest valid span by configured tie-break rule.

### Relationships

- Produces a candidate extraction for acceptance/rejection.

## Entity: ExtractedCandidate

Represents a candidate name produced by joined-only matching with guardrails.

### Fields

- `raw_candidate: str`
- `normalized_candidate: str`
- `matched_pattern_id: str | None`
- `accepted: bool`
- `rejection_reason: str` (`no_pattern_match` | `span_too_long` | `invalid_token` | `empty_candidate`)

### Validation

- Reject if empty after normalization.
- Reject if no alphanumeric character exists.

### Relationships

- Accepted candidates are converted into `TextDetection` and aggregated summaries.

## Entity: FrameRegionChangeDecision

Per sampled frame-region gating decision.

### Fields

- `frame_index: int`
- `timestamp_sec: float`
- `region_id: str`
- `pixel_diff_value: float` (0.0-1.0)
- `decision_action: str` (`execute_ocr` | `skip_ocr`)
- `reason: str`

### Validation

- Pixel diff is clipped to [0.0, 1.0].

### Relationships

- Updates `GatingStats` counters.
- Determines whether joined-text extraction executes for a frame-region pair.

## Entity: GatingStats

Run-level aggregate telemetry for gating behavior.

### Fields

- `total_frame_region_pairs: int`
- `ocr_executed_count: int`
- `ocr_skipped_count: int`
- `gating_enabled: bool`
- `gating_threshold: float`

### Invariants

- `ocr_executed_count + ocr_skipped_count == total_frame_region_pairs`

### Derived

- `skip_percentage = (ocr_skipped_count / total_frame_region_pairs) * 100` when total > 0.

## State and Flow

1. Sample frame and region.
2. Compute/change gate decision.
3. If executed, produce `JoinedRegionText`.
4. Evaluate patterns on joined text only.
5. Select nearest valid bounded window.
6. Validate extracted token and accept/reject.
7. Aggregate accepted detections and gating stats.

