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
- `event_gap_threshold_sec` (float): Max OCR miss gap used to merge one appearance event
- `detections` (list[TextDetection]): Raw or pre-aggregated detections
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
- `instruction_contrast_mode` (string): Contrast strategy for legibility over video content
- `instruction_font_scale` (float): Effective text scaling for readability

**Validation Rules**:
- `open_in_foreground` must be true for workflow launch
- Instruction text placement must avoid overlap with selection controls and active selection rectangles

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

### PlayerSummary
Represents one deduplicated output row.

**Attributes**:
- `player_name` (string)
- `normalized_name` (string)
- `occurrence_count` (int): Number of merged appearance events
- `first_seen_sec` (float)
- `last_seen_sec` (float)
- `representative_region` (string)

## Data Flow

1. User inputs URL and regions, configures optional context patterns in Advanced Settings
2. User adjusts OCR sensitivity when needed for lower-quality videos and receives reliability guidance
3. Frames are analyzed and OCR text is matched against active patterns (recall-first for context-matched names)
4. Candidate detections are normalized and grouped by normalized name
5. Detections are merged into appearance events using gap threshold (default 1.0s)
6. Player summaries are emitted with one row per normalized name and event-based occurrence count
7. CSV is exported to selected folder using auto-generated filename