# Feature Specification: Video-Centric Review History

**Feature Branch**: `012-from-3c6f0ff`  
**Created**: 2026-04-27  
**Status**: Draft  
**Input**: User description: "create this new feature on the current branch 012-from. disregard the spec for 011 completely. The list of previous reviews that is currently kept in the top panel of the review view shall be reframed as an edit history..."

> For web UI features, the feature specification defines required behavior and user outcomes.
> Google Stitch remains authoritative for UI design decisions unless the spec explicitly
> overrides a design point.

## Clarifications

### Session 2026-04-27

- Q: What persistence model should history entries use for reliable state restore? -> A: Full snapshot per entry (append-only history file).
- Q: How should concurrent edits to the same video be handled? -> A: Single-writer lock; second editor is read-only with warning.
- Q: How should long-term history size be managed? -> A: Keep all snapshots; compress older entries in the same history file/container.
- Q: When should new history snapshots be created? -> A: On state-changing review mutations only.
- Q: How should per-video folder naming be keyed? -> A: Stable video_id folder name; display title stored in metadata.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reopen Prior Review State (Priority: P1)

As a reviewer, I can use a date-time stamped edit history at the bottom of the review view to reopen any previous review state for the currently opened video.

**Why this priority**: This is the core behavior change requested and directly replaces the current top-panel previous reviews interaction.

**Independent Test**: Can be fully tested by opening one video with multiple saved review states, selecting an older history entry, and confirming the review view restores that exact prior state.

**Acceptance Scenarios**:

1. **Given** a video with multiple saved review history entries, **When** the reviewer opens the review view, **Then** a bottom-panel edit history list is shown with date-time stamped entries.
2. **Given** a specific history entry, **When** the reviewer selects it, **Then** the review view restores the grouped/resolution state represented by that entry.
3. **Given** each history entry in the list, **When** it is displayed, **Then** it includes the number of groups and number of resolved/unresolved items for that saved state.

---

### User Story 2 - Keep Video-Centric Data Together (Priority: P2)

As a reviewer, I can rely on one video as the primary unit of work, where all review and analysis artifacts for that video are organized together and opened through video history.

**Why this priority**: Correct data ownership and structure prevent drift between artifacts and make state restoration reliable over time.

**Independent Test**: Can be fully tested by creating a new video workspace through the selected output location and verifying that all expected video-specific artifacts are placed in a single folder and loaded together when reopening from history.

**Acceptance Scenarios**:

1. **Given** a selected output folder in analysis view, **When** a video is analyzed/reviewed, **Then** the system creates or uses one dedicated folder for that video under the selected output location.
2. **Given** the dedicated video folder, **When** artifacts are persisted, **Then** review history is stored in one history file associated with that video rather than split across separate files.
3. **Given** a video reopened from history, **When** the review view is loaded, **Then** the system uses the video folder as the single source of truth for analysis runs, settings, grouping settings, selection region configuration, and reviewed player names.

---

### User Story 3 - Preserve Final Reviewed Names (Priority: P3)

As a reviewer, I can see and maintain one clean list of reviewed player names identified for a video, independent from intermediate grouping steps.

**Why this priority**: This produces the final durable outcome of the review process and reduces ambiguity caused by temporary grouping states.

**Independent Test**: Can be fully tested by completing a review workflow and verifying the stored final reviewed names list remains consistent after closing and reopening the same video.

**Acceptance Scenarios**:

1. **Given** a completed or partially completed review for a video, **When** reviewed names are finalized, **Then** one clean reviewed names list is persisted for that video.
2. **Given** the video is reopened later, **When** its state is loaded, **Then** the clean reviewed names list is available and consistent with the last saved review state.

### Edge Cases

- What happens when a video has no prior edit history entries? The review view shows an empty-state message and the current state remains active.
- How does system handle a missing or unreadable history file for a video? The system shows a non-fatal warning for that video, preserves access to other video data, blocks restore actions for the affected video until the history source is repaired or relinked, and writes diagnostic details to application logs.
- What happens when two history entries have the same timestamp value? The system still shows both entries in deterministic order and allows selecting either state.
- How does system handle a video folder moved or renamed outside the application? The video cannot be reopened until relinked, and no unrelated video folders are modified.
- What happens when a second editor opens the same video while one editor is actively writing? The second editor opens in read-only mode with a clear warning that editing is locked by another session.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST replace the top-panel previous reviews list with a bottom-panel edit history list in the review view.
- **FR-002**: The system MUST store each edit history entry with a date-time stamp and summary data including group count, resolved count, and unresolved count.
- **FR-003**: Users MUST be able to select any edit history entry and restore the review state represented by that entry.
- **FR-004**: The system MUST maintain exactly one canonical per-video history container file as the storage location for that video's review history.
- **FR-005**: The system MUST treat the video as the primary entity when opening from history and loading associated review context.
- **FR-006**: The system MUST maintain, per video, a set of analysis runs where each run contains found candidates.
- **FR-007**: The system MUST maintain, per video, one analysis settings set, one review grouping settings set, and one selection regions configuration.
- **FR-008**: The system MUST maintain, per video, one clean list of reviewed player names identified during review.
- **FR-009**: The system MUST organize all video-related files in one dedicated folder per video.
- **FR-010**: The system MUST place each video folder under the output location selected in the analysis view.
- **FR-011**: The system MUST reopen a video using only its associated video folder artifacts without requiring cross-video state files.
- **FR-012**: The system MUST preserve backward-safe behavior for videos without edit history entries by allowing review to continue and creating history on first save.
- **FR-013**: The system MUST persist each edit history entry as a full review-state snapshot in an append-only per-video history file to guarantee deterministic restore of any selected entry.
- **FR-014**: The system MUST enforce single-writer behavior per video workspace; if a second session opens the same video while a writer is active, that session MUST be read-only and display a lock warning.
- **FR-015**: The system MUST retain all history snapshots for a video while allowing older entries to be compressed within the same per-video history file/container without removing restore capability.
- **FR-016**: The system MUST create new history snapshots only for state-changing review mutations (including grouping changes, review decisions, review/grouping settings changes, recalculation outcomes, and explicit restore actions), and MUST NOT create snapshots for non-state-changing UI interactions.
- **FR-017**: The system MUST key each per-video workspace folder by a stable video_id and store display title separately in metadata so folder identity remains stable if display naming changes.

### Key Entities *(include if feature involves data)*

- **Video Workspace**: Represents one video and all persisted artifacts for that video, including review history, analysis runs, settings, configuration, and final reviewed names. Workspace identity is a stable video_id; display title is metadata.
- **Edit History Entry**: Represents a full saved review-state snapshot for a video, including timestamp and summary counts (groups, resolved, unresolved), written as an append-only record that can be restored directly.
- **History Container**: Represents the single per-video history file that stores all snapshots, including uncompressed recent entries and compressed older entries, while preserving deterministic restore for any entry.
- **Analysis Run**: Represents one analysis execution for a video, including the candidate items found during that run.
- **Video Review Settings Bundle**: Represents the video-specific settings set including analysis settings, review grouping settings, and selection region configuration.
- **Reviewed Name List**: Represents the clean, video-level list of reviewed player names identified by the reviewer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reviewed videos display edit history entries in the bottom review panel with timestamp, group count, resolved count, and unresolved count.
- **SC-002**: In validation tests, selecting a history entry restores the intended prior review state with no mismatches in at least 99% of restore attempts.
- **SC-003**: For newly created video workspaces, 100% of persisted review/analysis artifacts are stored under the corresponding per-video folder in the selected output location.
- **SC-004**: At least 95% of evaluators can successfully reopen a video from history and locate its final reviewed names list on first attempt.

## Assumptions

- Existing videos and review workflows continue to be supported, with migration or compatibility handling for prior persisted data formats.
- The selected output folder in analysis view is writable when a video workspace needs to be created or updated.
- Date-time stamps are generated in a consistent format suitable for chronological display and stable sorting.
- One video corresponds to one authoritative review history file and one final reviewed names list.
- Access control requirements are unchanged from current application behavior.
