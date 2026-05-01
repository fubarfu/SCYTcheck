# Data Model: Video-Centric Review History

**Feature**: 012-video-review-history | **Phase**: Phase 1 Design | **Date**: 2026-04-27

## Entity 1: VideoWorkspace

Represents the primary persisted container for one analyzed/reviewed video.

Fields:
- `video_id: str` (stable identity; folder key)
- `display_title: str` (mutable metadata for UI display)
- `workspace_path: str` (absolute path under selected output location)
- `analysis_runs: list[AnalysisRun]`
- `review_settings: VideoReviewSettingsBundle`
- `reviewed_names: ReviewedNameList`
- `history_container_path: str`
- `active_lock: WorkspaceLock | None`

Validation rules:
- `video_id` must be non-empty and filesystem-safe.
- `workspace_path` must resolve under selected output root.
- `history_container_path` must belong to workspace.

## Entity 2: EditHistoryEntry

Represents one append-only full snapshot of review state.

Fields:
- `entry_id: str` (unique within container)
- `created_at: str` (ISO-8601 timestamp)
- `trigger_type: str` (mutation category, e.g., confirm/reject/restore/settings-change)
- `summary: EntrySummary`
- `snapshot: ReviewStateSnapshot`
- `compressed: bool`

Validation rules:
- Snapshot must be complete and self-sufficient for direct restore.
- `summary` counts must match derived counts from `snapshot`.
- `created_at` ordering must be deterministic for ties (`entry_id` fallback).

State transitions:
- Created on eligible state mutation.
- Optionally marked `compressed=true` during retention optimization.
- Never deleted by routine retention.

## Entity 3: HistoryContainer

Represents the single per-video append-only history file.

Fields:
- `schema_version: str`
- `video_id: str`
- `entries: list[EditHistoryEntry]`
- `compression_index: dict[str, str]` (entry_id to compression metadata)

Validation rules:
- Container `video_id` must equal workspace `video_id`.
- Entries remain append-ordered by write sequence.
- Any compressed entry must remain restorable.

## Entity 4: ReviewStateSnapshot

Represents full restorable review-state payload.

Fields:
- `groups: list[ReviewGroupState]`
- `resolved_count: int`
- `unresolved_count: int`
- `group_count: int`
- `reviewed_names: list[str]`
- `analysis_context_ref: str`
- `settings_bundle_ref: str`

Validation rules:
- `group_count == len(groups)`
- `resolved_count + unresolved_count == group_count`
- Group IDs are unique.

## Entity 5: WorkspaceLock

Represents single-writer concurrency control for a workspace.

Fields:
- `lock_id: str`
- `video_id: str`
- `owner_session_id: str`
- `acquired_at: str`
- `expires_at: str | None`
- `mode: str` (`writer`)

Validation rules:
- Maximum one active writer lock per `video_id`.
- Non-owner sessions load workspace in read-only mode.

## Entity 6: AnalysisRun

Represents one OCR/analysis execution associated with workspace.

Fields:
- `run_id: str`
- `created_at: str`
- `candidate_rows_ref: str`
- `source_video_path: str`

## Entity 7: VideoReviewSettingsBundle

Represents persisted settings relevant to restoring behavior.

Fields:
- `analysis_settings: dict`
- `grouping_settings: dict`
- `selection_region_config: dict`

## Entity 8: ReviewedNameList

Represents durable final reviewed names outcome.

Fields:
- `names: list[str]`
- `updated_at: str`

## Relationships

- `VideoWorkspace (1)` -> `(1) HistoryContainer`
- `HistoryContainer (1)` -> `(*) EditHistoryEntry`
- `EditHistoryEntry (1)` -> `(1) ReviewStateSnapshot`
- `VideoWorkspace (1)` -> `(*) AnalysisRun`
- `VideoWorkspace (1)` -> `(1) VideoReviewSettingsBundle`
- `VideoWorkspace (1)` -> `(1) ReviewedNameList`
- `VideoWorkspace (0..1)` -> `(1) WorkspaceLock`

## Snapshot Trigger Matrix

Snapshots are created for:
- Confirm/reject/unreject/deselect mutations
- Grouping and review decision mutations
- Settings mutations affecting review behavior
- Recalculation outcomes that alter review state
- Explicit restore actions

Snapshots are not created for:
- Pure navigation/filtering/sorting
- Expand-collapse UI changes with no state mutation
- Read-only inspection actions

## Restore Semantics

Selecting a history entry restores exactly `entry.snapshot` into active review state and writes a new snapshot capturing restore action provenance.