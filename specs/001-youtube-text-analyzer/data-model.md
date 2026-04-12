# Data Model: YouTube Text Analyzer

**Date**: April 12, 2026
**Feature**: specs/001-youtube-text-analyzer/spec.md

## Entities

### VideoAnalysis
Represents a single video analysis session.

**Attributes**:
- `url` (string): YouTube video URL
- `timestamp` (datetime): When analysis was performed
- `regions` (list[Region]): User-selected regions of interest
- `context_patterns` (list[ContextPattern]): Active extraction rules
- `filter_non_matching` (bool): Global toggle for pattern-only output filtering
- `ocr_confidence_threshold` (int): Active OCR sensitivity setting used during detection
- `video_quality` (string): User-selected retrieval quality (default `best`)
- `logging_enabled` (bool): Whether sidecar audit log export is enabled
- `event_gap_threshold_sec` (float): Max OCR miss gap used to merge one appearance event
- `detections` (list[TextDetection]): Per-candidate detections
- `log_records` (list[LogRecord]): Per-candidate audit records when logging is enabled
- `player_summaries` (list[PlayerSummary]): Deduplicated output rows

### Region
Represents an ROI rectangle selected by the user.

**Attributes**:
- `id` (string)
- `x` (int)
- `y` (int)
- `width` (int)
- `height` (int)

### ContextPattern
Represents a user-defined surrounding-text extraction rule.

**Attributes**:
- `id` (string)
- `before_text` (string | null)
- `after_text` (string | null)
- `enabled` (bool)
- `similarity_threshold` (float): default `0.75` for fuzzy matching

**Validation Rules**:
- At least one of `before_text` or `after_text` must be present.
- Matching uses case-insensitive fuzzy **substring search** over normalized OCR region text.
- OCR normalization for matching joins line text, removes line breaks, and collapses repeated whitespace runs to single spaces.
- Boundary-clipped context can match when at least two contiguous boundary characters overlap or fuzzy similarity meets threshold.

### TextDetection
Represents one extracted candidate player detection from an analyzed frame.

**Attributes**:
- `raw_ocr_text` (string): OCR line used for extraction
- `extracted_name` (string): extracted player token for this candidate
- `normalized_name` (string): lowercase + trim + collapsed internal spaces (dedup key)
- `region_id` (string)
- `frame_time_sec` (float)
- `matched_pattern_id` (string | null)

**Validation Rules**:
- Single-token extraction policy applies:
  - after-only: keep last whitespace-delimited token before marker
  - before-only: keep first whitespace-delimited token after marker
  - both: keep first whitespace-delimited token between markers
- Empty token results are rejected as no extracted name.

### AppearanceEvent
Represents one merged appearance period for a normalized player name.

**Attributes**:
- `normalized_name` (string)
- `start_time_sec` (float)
- `end_time_sec` (float)
- `region_ids` (set[string])

### PlayerSummary
Represents one deduplicated output row.

**Attributes**:
- `player_name` (string): on-screen display form selected from earliest accepted detection in group
- `start_timestamp` (string): `HH:MM:SS.mmm`
- `normalized_name` (string): internal grouping key
- `occurrence_count` (int)
- `first_seen_sec` (float)
- `last_seen_sec` (float)
- `representative_region` (string)

**Validation Rules**:
- Deduplication uses `normalized_name` only.
- Exported `player_name` MUST preserve on-screen extracted form and must not be normalized/lowercased for display.
- For each normalized group, choose `player_name` from earliest accepted detection timestamp.

### LogRecord
Represents one audit row written to the sidecar log CSV.

**Attributes**:
- `timestamp_sec` (string): `HH:MM:SS.mmm`
- `raw_string` (string)
- `tested_string_raw` (string)
- `tested_string_normalized` (string)
- `accepted` (bool)
- `rejection_reason` (string)
- `extracted_name` (string)
- `region_id` (string)
- `matched_pattern` (string)
- `normalized_name` (string)
- `occurrence_count` (int)
- `start_timestamp` (string): `HH:MM:SS.mmm`
- `end_timestamp` (string): `HH:MM:SS.mmm`
- `representative_region` (string)

**Validation Rules**:
- Column order is fixed: `TimestampSec`, `RawString`, `TestedStringRaw`, `TestedStringNormalized`, `Accepted`, `RejectionReason`, `ExtractedName`, `RegionId`, `MatchedPattern`, `NormalizedName`, `OccurrenceCount`, `StartTimestamp`, `EndTimestamp`, `RepresentativeRegion`.
- `tested_string_raw` and `tested_string_normalized` must be present for accepted and rejected rows.
- `rejection_reason` must be non-empty when `accepted=false`.
- `extracted_name` must be non-empty when `accepted=true`.

## Data Flow

1. User inputs URL and regions, configures optional context patterns in Advanced Settings.
2. Frames are analyzed and OCR text is matched against active patterns.
3. Candidate detections apply single-token extraction policy.
4. Candidate tokens are normalized for deduplication grouping.
5. Detections are merged into appearance events using gap threshold (default 1.0s).
6. Player summaries emit one row per normalized group with earliest merged `StartTimestamp` and earliest accepted on-screen `PlayerName`.
7. Summary CSV is exported to selected folder using auto-generated filename.
8. If logging is enabled, sidecar CSV is written with deterministic schema and candidate-level diagnostics.
