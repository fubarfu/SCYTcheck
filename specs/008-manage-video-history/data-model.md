# Data Model: Managed Video Analysis History

## Entity: VideoHistoryEntry
- Purpose: Canonical persistent record for a analyzed video across one or more runs.

### Fields
- `history_id` (string, required): Stable local UUID.
- `canonical_source` (string, required): Canonicalized URI/path used for merge identity.
- `source_type` (enum, required): `youtube_url` | `local_file`.
- `duration_seconds` (integer, optional): Non-negative integer when metadata is valid.
- `merge_key` (string, optional): Deterministic key composed from canonical source + duration.
- `potential_duplicate` (boolean, required): True when merge could not be evaluated deterministically.
- `display_name` (string, required): User-facing label (derived from source metadata/path).
- `output_folder` (string, required): Root folder for derived review artifacts.
- `last_result_csv` (string, optional): Most recent result CSV path.
- `run_count` (integer, required): Number of associated runs.
- `created_at` (ISO datetime, required)
- `updated_at` (ISO datetime, required)
- `deleted` (boolean, required): Soft-delete marker for index integrity.

### Validation Rules
- `canonical_source` must be non-empty after normalization.
- `duration_seconds` must be integer >= 0 when present.
- `merge_key` required when `duration_seconds` is valid.
- `potential_duplicate` must be true when `duration_seconds` is missing/malformed.

## Entity: AnalysisRunRecord
- Purpose: One completed analysis event linked to a canonical history entry.

### Fields
- `run_id` (string, required)
- `history_id` (string, required, FK -> VideoHistoryEntry.history_id)
- `completed_at` (ISO datetime, required)
- `result_csv_path` (string, required)
- `sidecar_review_path` (string, optional)
- `frame_count_processed` (integer, optional)
- `settings_snapshot_id` (string, required, FK -> PersistedAnalysisContext.context_id)

### Validation Rules
- `result_csv_path` must be absolute path and readable at persist time.
- `history_id` must reference active (non-deleted) entry.

## Entity: PersistedAnalysisContext
- Purpose: Restorable user analysis context for reopen.

### Fields
- `context_id` (string, required)
- `history_id` (string, required, FK -> VideoHistoryEntry.history_id)
- `scan_region` (object, required): `{x,y,width,height}`
- `output_folder` (string, required)
- `context_patterns` (array, required): Context pattern definitions and enabled state
- `analysis_settings` (object, required): OCR sensitivity, matching tolerance, merge gap, gating flags, etc.
- `saved_at` (ISO datetime, required)

### Validation Rules
- Region bounds must be non-negative with width/height > 0.
- `output_folder` must be non-empty and path-normalized.
- Pattern entries require stable IDs.

## Entity: DerivedReviewResultSet
- Purpose: Computed artifact resolution from a reopened history entry output folder.

### Fields
- `history_id` (string, required)
- `resolved_csv_paths` (array[string], required)
- `resolved_sidecar_paths` (array[string], optional)
- `primary_csv_path` (string, optional)
- `resolution_status` (enum, required): `ready` | `missing_results` | `missing_folder` | `partial`
- `resolution_messages` (array[string], required)
- `resolved_at` (ISO datetime, required)

### Validation Rules
- `resolution_status=ready` requires at least one valid CSV path.
- `missing_folder` when output folder is not accessible.

## Relationships
- One `VideoHistoryEntry` has many `AnalysisRunRecord`.
- One `VideoHistoryEntry` has many `PersistedAnalysisContext` snapshots (latest used for reopen).
- One `VideoHistoryEntry` maps to one transient `DerivedReviewResultSet` per reopen action.

## State Transitions

### VideoHistoryEntry
1. `new` -> `active`: First analysis complete and persisted.
2. `active` -> `active` (merged update): Repeat analysis matches merge key; append run and update latest context.
3. `active` -> `potential_duplicate`: New run without valid duration metadata stored as separate flagged entry.
4. `active|potential_duplicate` -> `deleted`: User deletes from History view; metadata removed from visible list.

### Reopen Flow
1. `selected` -> `context_restored`: Latest `PersistedAnalysisContext` loaded.
2. `context_restored` -> `results_resolved`: Derived result set built from output folder.
3. `results_resolved` -> `review_loaded`: Review session opened automatically when `ready` or `partial`.
4. `results_resolved` -> `review_warning`: Non-blocking warning when `missing_results` or `missing_folder` while retaining metadata access.
