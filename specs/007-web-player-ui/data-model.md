# Data Model: Web Player UI (007)

## Entity: AnalysisSource
- Purpose: Represents user-selected input to run analysis.
- Fields:
  - `source_id` (string, required)
  - `source_type` (enum: `youtube_url` | `local_file`, required)
  - `source_value` (string, required)
  - `video_id` (string, optional; present for YouTube)
  - `display_name` (string, required)
- Validation:
  - `source_value` must be non-empty.
  - `youtube_url` must be parseable as supported YouTube URL format.
  - `local_file` path must exist and be readable.

## Entity: AnalysisSettings
- Purpose: Full parity settings model migrated from legacy Tkinter analysis controls.
- Fields:
  - `output_folder` (string, required)
  - `output_filename` (string, required)
  - `scan_region` (object `ScanRegion`, required before run)
  - `video_quality` (enum: `best` | `720p` | `480p` | `360p`, required)
  - `ocr_sensitivity` (integer 0-100, required)
  - `matching_tolerance` (integer 0-100, required)
  - `event_merge_gap_seconds` (number >= 0, required)
  - `gating_enabled` (boolean, required)
  - `gating_threshold` (integer 0-100, required when gating enabled)
  - `context_patterns` (array of `ContextPattern`, required)
  - `filter_non_matching` (boolean, required)
  - `detailed_sidecar_log` (boolean, required)
  - `theme` (enum: `dark` | `light`, required)
- Validation:
  - Must be persisted in existing settings file (`scytcheck_settings.json`).
  - Folder must be writable before analysis starts.

## Entity: ScanRegion
- Purpose: OCR bounding rectangle selected in browser over captured frame.
- Fields:
  - `x` (integer >= 0, required)
  - `y` (integer >= 0, required)
  - `width` (integer > 0, required)
  - `height` (integer > 0, required)
  - `frame_width` (integer > 0, required)
  - `frame_height` (integer > 0, required)
- Validation:
  - Region must remain inside frame bounds.

## Entity: AnalysisRun
- Purpose: Tracks in-progress or completed analysis execution from Analysis view.
- Fields:
  - `run_id` (string, required)
  - `status` (enum: `idle` | `running` | `stopping` | `completed` | `failed`, required)
  - `started_at` (datetime, optional)
  - `ended_at` (datetime, optional)
  - `frames_processed` (integer >= 0, required)
  - `frames_estimated_total` (integer >= 0, required)
  - `stage_label` (string, optional)
  - `output_csv_path` (string, optional)
- State transitions:
  - `idle -> running -> completed`
  - `idle -> running -> stopping -> completed`
  - `running -> failed`

## Entity: CandidateOccurrence
- Purpose: One OCR-detected candidate row shown in Review.
- Fields:
  - `candidate_id` (string, required)
  - `session_id` (string, required)
  - `raw_text` (string, required)
  - `corrected_text` (string, optional)
  - `normalized_text` (string, required)
  - `status` (enum: `unreviewed` | `confirmed` | `rejected`, required)
  - `removed` (boolean, required; hard delete marker)
  - `timestamp_seconds` (number >= 0, required)
  - `ocr_confidence` (number 0-1, optional)
  - `frame_path` (string, optional)
  - `thumbnail_path` (string, optional)
  - `youtube_deep_link` (string, optional)
  - `group_id` (string, required)
- Validation:
  - Effective text (`corrected_text` if present else `raw_text`) must be non-empty.
  - `youtube_deep_link` only allowed when source is YouTube.

## Entity: CandidateGroup
- Purpose: Group-level review container for near-identical candidate occurrences.
- Fields:
  - `group_id` (string, required)
  - `display_label` (string, required)
  - `member_ids` (array[string], required)
  - `text_similarity_score` (number 0-100, required)
  - `temporal_proximity_score` (number 0-100, required)
  - `recommendation_score` (number 0-100, required)
  - `recommendation_level` (enum: `low` | `medium` | `high`, required)
  - `order_index` (integer >= 0, required)
- Validation:
  - Group must contain at least one non-removed member.

## Entity: ReviewSession
- Purpose: Persistent state for one analysis CSV review lifecycle.
- Fields:
  - `session_id` (string, required)
  - `csv_path` (string, required)
  - `source_type` (enum: `youtube_url` | `local_file`, required)
  - `source_value` (string, required)
  - `schema_version` (string, required)
  - `similarity_threshold` (integer 50-100, required; default 80)
  - `recommendation_threshold` (integer 0-100, required; default 70)
  - `candidates` (array[`CandidateOccurrence`], required)
  - `groups` (array[`CandidateGroup`], required)
  - `undo_stack` (array[`ReviewAction`], required)
  - `updated_at` (datetime, required)
- Validation:
  - Persist sidecar after each mutating action.
  - Session creation blocked on CSV schema/version validation pass.

## Entity: ReviewAction
- Purpose: Immutable action log item for unlimited undo.
- Fields:
  - `action_id` (string, required)
  - `action_type` (enum: `confirm` | `reject` | `unconfirm` | `edit` | `remove` | `move_candidate` | `merge_groups` | `reorder_group`, required)
  - `target_ids` (array[string], required)
  - `before_state` (object, required)
  - `after_state` (object, required)
  - `created_at` (datetime, required)
- Validation:
  - `before_state` must be sufficient to restore prior state on undo.

## Entity: ExportBundle
- Purpose: Represents review export artifacts.
- Fields:
  - `session_id` (string, required)
  - `deduplicated_names_csv_path` (string, required)
  - `occurrences_csv_path` (string, required)
  - `exported_at` (datetime, required)
  - `confirmed_count` (integer >= 0, required)
  - `deduplicated_count` (integer >= 0, required)
- Validation:
  - Removed and rejected candidates must not appear in outputs.
  - Occurrence rows must retain timestamp and frame reference columns.

## Relationships
- One `AnalysisSource` + one `AnalysisSettings` produce one `AnalysisRun`.
- One completed `AnalysisRun` produces one CSV and can open one `ReviewSession`.
- One `ReviewSession` contains many `CandidateOccurrence` and many `CandidateGroup`.
- One `CandidateGroup` contains many `CandidateOccurrence`.
- One `ReviewSession` contains many `ReviewAction` entries for undo history.
- One `ReviewSession` can produce one or more `ExportBundle` records.
