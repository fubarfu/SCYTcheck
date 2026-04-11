# Data Model: YouTube Text Analyzer

**Date**: April 11, 2026
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
- `detections` (list[TextDetection]): Raw or pre-aggregated detections
- `log_records` (list[LogRecord]): Per-candidate audit records when logging is enabled
- `player_summaries` (list[PlayerSummary]): Deduplicated output rows

**Relationships**:
- Contains many `Region`, `ContextPattern`, `TextDetection`, and `PlayerSummary` records

### Region
Represents an ROI rectangle selected by the user.

**Attributes**:
- `id` (string)
- `x` (int)
- `y` (int)
- `width` (int)
- `height` (int)

### RegionSelectorPresentation
Represents display and focus behavior of the region-selection popup.

**Attributes**:
- `open_in_foreground` (bool): Popup is raised and visible over main window at launch
- `instruction_text` (string): Guidance text displayed in selection view
- `instruction_area_position` (string): Must be `below_video`
- `instruction_contrast_mode` (string): Contrast strategy for legibility in the dedicated instruction area
- `instruction_font_scale` (float): Effective text scaling for readability

**Validation Rules**:
- `open_in_foreground` must be true for workflow launch
- `instruction_area_position` must be `below_video`
- Instruction text must avoid overlap with selection controls and active selection rectangles
- Instruction text must never overlay the video canvas

### ContextPattern
Represents a user-defined surrounding-text extraction rule.

**Attributes**:
- `id` (string)
- `before_text` (string | null)
- `after_text` (string | null)
- `enabled` (bool)

**Validation Rules**:
- At least one of `before_text` or `after_text` must be present
- Matching is case-insensitive substring

### TextDetection
Represents one extracted candidate player detection from an analyzed frame.

**Attributes**:
- `raw_ocr_text` (string): OCR line used for extraction
- `extracted_name` (string): Trimmed extracted player name
- `normalized_name` (string): lowercase + trim + collapsed internal spaces
- `region_id` (string)
- `frame_time_sec` (float)
- `matched_pattern_id` (string | null)

**Relationships**:
- Belongs to `VideoAnalysis`; optionally references `ContextPattern`

### AppearanceEvent
Represents one merged appearance period for a normalized player name.

**Attributes**:
- `normalized_name` (string)
- `display_name` (string): Representative display form
- `start_time_sec` (float)
- `end_time_sec` (float)
- `region_ids` (set[string])

**State Transition**:
- New event begins on first detection
- Event is extended while next detection for same normalized name is within `event_gap_threshold_sec`
- Event closes when gap exceeds threshold

### LoggingSettings
Represents persisted settings for optional audit logging.

**Attributes**:
- `enabled` (bool): Default `false`
- `log_filename_suffix` (string): Fixed `_log.csv`

**Validation Rules**:
- If `enabled=false`, no log file is produced
- If `enabled=true`, log file must be created in output folder with output base name + suffix

### LogRecord
Represents one audit row written to the sidecar log CSV.

**Attributes**:
- `timestamp_sec` (string): `HH:MM:SS.mmm`
- `raw_string` (string)
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
- Column order is fixed: `TimestampSec`, `RawString`, `Accepted`, `RejectionReason`, `ExtractedName`, `RegionId`, `MatchedPattern`, `NormalizedName`, `OccurrenceCount`, `StartTimestamp`, `EndTimestamp`, `RepresentativeRegion`
- `rejection_reason` must be non-empty when `accepted=false`
- `extracted_name` must be non-empty when `accepted=true`

### PlayerSummary
Represents one deduplicated output row.

**Attributes**:
- `player_name` (string)
- `start_timestamp` (string): `HH:MM:SS.mmm`

## Data Flow

1. User inputs URL and regions, configures optional context patterns in Advanced Settings
2. User selects retrieval quality (default best), adjusts OCR sensitivity as needed, and optionally enables audit logging
3. Frames are analyzed and OCR text is matched against active patterns (recall-first for context-matched names)
4. Candidate detections are normalized and grouped by normalized name
5. Detections are merged into appearance events using gap threshold (default 1.0s)
6. Player summaries are emitted with one row per normalized name and earliest merged event start as `StartTimestamp`
7. Summary CSV is exported to selected folder using auto-generated filename
8. If logging is enabled, sidecar log CSV is written in fixed schema with one row per candidate plus aggregation context fields