# Feature Specification: Managed Video Analysis History

**Feature Branch**: `008-manage-video-history`  
**Created**: 2026-04-25  
**Status**: Draft  
**Input**: User description: "The tool maintains a list of videos that have previously been analysed. All analysis of a video that has been previously analysed are merged. A third view allows the user maintain this list (delete, reopen). All settings, like the selected regions, output folder, context text patterns, and analysis settings are persistent when a video analysis is reopened. the review view load automatically the results. the result files in the review are automatically derived from the outputfolder."

> For web UI features, the feature specification defines required behavior and user outcomes.
> Google Stitch remains authoritative for UI design decisions unless the spec explicitly
> overrides a design point.

## Clarifications

### Session 2026-04-25

- Q: Which identity rule should drive automatic merge of repeat analyses? -> A: Merge by canonical video source URI/path plus duration (seconds).
- Q: How should merge behave when duration metadata is missing or malformed? -> A: Do not auto-merge; create a new entry flagged as potential duplicate.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reopen Prior Analysis Quickly (Priority: P1)

As an analyst, I want to reopen a previously analyzed video and immediately continue review so I can avoid repeating setup and reduce turnaround time.

**Why this priority**: Reopening prior work is the highest-value flow because it directly reduces repeated manual effort and accelerates decision making.

**Independent Test**: Can be fully tested by selecting a previously analyzed video, reopening it, and verifying that persisted settings and review results load without additional configuration.

**Acceptance Scenarios**:

1. **Given** a video exists in analysis history with saved settings and prior results, **When** the user chooses to reopen that video, **Then** the analysis context is restored and the review view loads available results automatically.
2. **Given** a reopened video has a previously used output folder, **When** the review view loads, **Then** result files are discovered from that output folder without manual file selection.

---

### User Story 2 - Merge Repeat Analyses by Video (Priority: P2)

As an analyst, I want analyses of the same video to be merged into a single combined history record so I can track one canonical result set per video.

**Why this priority**: Duplicate history records create confusion and increase review overhead; merging protects data continuity and simplifies navigation.

**Independent Test**: Can be fully tested by analyzing the same video multiple times and verifying that history shows one merged entry containing all relevant results.

**Acceptance Scenarios**:

1. **Given** a video has an existing history entry, **When** a new analysis of that same video completes, **Then** the system merges the new analysis into the existing entry instead of creating a duplicate history entry.
2. **Given** merged analyses exist for one video, **When** the user opens that video from history, **Then** the user can access the combined results associated with that video.

---

### User Story 3 - Maintain Analysis History List (Priority: P3)

As an analyst, I want a dedicated history-management view where I can reopen or delete history items so I can keep my workspace organized.

**Why this priority**: List maintenance improves long-term usability and storage hygiene but is lower priority than core reopen and merge behavior.

**Independent Test**: Can be fully tested by opening the history-management view, deleting a selected entry, and reopening another entry from the same view.

**Acceptance Scenarios**:

1. **Given** multiple videos are in history, **When** the user opens the history-management view, **Then** the user can see the list of previously analyzed videos.
2. **Given** a selected history entry, **When** the user chooses delete, **Then** that entry is removed from history and no longer appears in the list.
3. **Given** a selected history entry, **When** the user chooses reopen, **Then** the system restores that entry's context and opens review automatically.

---

### Edge Cases

- What happens when a history entry is reopened but the referenced output folder is missing or no longer accessible?
- How does the system behave when source URI/path matches but duration metadata is unavailable or malformed?
- What happens when a user deletes a history entry that has result files still present in the output folder?
- How does the system handle reopening an entry whose persisted settings are partially unavailable or invalid?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST maintain a persistent list of previously analyzed videos.
- **FR-002**: System MUST identify repeat analyses of the same video using canonical video source URI/path plus duration in seconds as the deterministic merge key, and merge them into the existing video history entry.
- **FR-003**: System MUST provide a dedicated third view for history management.
- **FR-004**: Users MUST be able to delete an entry from the history-management view.
- **FR-005**: Users MUST be able to reopen a selected history entry from the history-management view.
- **FR-006**: When reopening an analysis, system MUST restore persisted settings including selected regions, output folder, context text patterns, and analysis settings.
- **FR-007**: When an analysis is reopened, review view MUST load automatically.
- **FR-008**: Review results for a reopened analysis MUST be discovered automatically from the entry's output folder.
- **FR-009**: System MUST prevent duplicate history entries for the same video after merge.
- **FR-010**: If required result artifacts are missing from the derived output folder, system MUST notify the user and still allow access to the history entry metadata. Required artifacts are at least one CSV result file; sidecar review JSON is optional and its absence MUST NOT block metadata access.
- **FR-011**: If duration metadata is missing or malformed for a candidate merge, system MUST NOT auto-merge and MUST create a new history entry flagged as a potential duplicate for user review.

### Key Entities *(include if feature involves data)*

- **Video History Entry**: Represents one tracked video in history, including canonical source URI/path, duration (seconds), deterministic merge key, potential-duplicate flag, display metadata, and current merge state.
- **Analysis Run Record**: Represents one completed analysis event associated with a video history entry.
- **Persisted Analysis Context**: Represents saved user configuration needed to resume work (regions, output folder, context patterns, and analysis settings).
- **Derived Review Result Set**: Represents the review artifacts resolved from the stored output folder when reopening.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 95% of reopen actions load the review view with restored context in under 5 seconds under normal local workstation conditions.
- **SC-002**: 100% of repeat analyses with a valid deterministic merge key (canonical source URI/path plus valid duration seconds) produce a single visible history entry rather than multiple duplicates.
- **SC-003**: At least 90% of users can reopen a prior analysis and continue review without manually re-entering settings.
- **SC-004**: At least 95% of reopen attempts with valid output folders automatically load discoverable result files without user file browsing.

## Assumptions

- Video identity for merge is determined by canonical source URI/path combined with duration (seconds).
- Deleting a history entry removes it from the managed list but does not automatically delete output files from disk unless the user explicitly performs separate file cleanup.
- Reopen behavior is scoped to local historical analyses available to the current user profile.
- The existing review workflow remains the destination experience after reopen; this feature changes entry and restoration behavior, not review semantics.
