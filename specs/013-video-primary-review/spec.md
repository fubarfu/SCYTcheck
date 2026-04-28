# Feature Specification: Video-Primary Review Flow

**Feature Branch**: `013-create-spec-branch`  
**Created**: 2026-04-28  
**Status**: Draft  
**Input**: User description: "As all result files are combined together in review and the video is primary citizen, there is no need to let the user explicitly load a result file..."

> For web UI features, the feature specification defines required behavior and user outcomes.
> Google Stitch remains authoritative for UI design decisions unless the spec explicitly
> overrides a design point.

## Clarifications

### Session 2026-04-28

- Q: Should the Videos view keep using an app-level history record to track projects? -> A: No. Projects are derived directly from the configured project location; no separate app-level history is retained.
- Q: Must the user define a project location before first use? -> A: No. A default project location is defined in app-level settings and used automatically on first run.
- Q: How should merged review conflicts be resolved when a prior reviewed decision conflicts with a newly analyzed result? -> A: Prior human-reviewed status wins; the new run adds evidence but does not override reviewed decisions automatically.
- Q: How long should a candidate remain marked as new? -> A: Keep new until the user explicitly confirms, rejects, or edits that candidate.
- Q: Which candidates qualify for a new marker? -> A: Only candidates whose spelling differs from previously existing candidates qualify as new.
- Q: What should users see in the progress window during analysis regarding project status? -> A: The progress window shall show whether a new project is being created or results will be merged with an existing project. Review view opens automatically after analysis completes.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto-Load Video Review Context (Priority: P1)

As a reviewer, I can open review directly after analysis and see one combined review state for the analyzed video without manually choosing a result file.

**Why this priority**: This is the core workflow change and removes the current manual file-selection friction.

**Independent Test**: Can be fully tested by running analysis on a video with existing prior runs and verifying review opens with one combined data set for that video automatically.

**Acceptance Scenarios**:

1. **Given** a video has prior analysis runs and a new analysis run completes, **When** review opens, **Then** all available output data for that video is loaded as one combined review context.
2. **Given** review is opened from a completed analysis, **When** the page renders, **Then** no manual result-file load action is required before candidates and groups are available.
3. **Given** review header/source context is displayed, **When** the source is shown, **Then** the video URL is shown as read-only context instead of a result-file input.
4. **Given** a prior run contains a human-reviewed decision for a candidate and the latest run surfaces conflicting analysis evidence, **When** the merged review context is built, **Then** the prior human-reviewed decision remains effective until the user explicitly changes it.
5. **Given** analysis is in progress and results will be merged with an existing project, **When** the progress window is displayed, **Then** a message clearly indicates the results will be merged with the existing project.
6. **Given** analysis is in progress and the video has no prior project, **When** the progress window is displayed, **Then** a message clearly indicates a new project will be created.
7. **Given** analysis completes successfully, **When** the analysis process finishes, **Then** the review view for that video opens automatically without user intervention.

---

### User Story 2 - Emphasize Newly Found Candidates (Priority: P2)

As a reviewer, I can immediately identify which candidates came from the most recent analysis run.

**Why this priority**: Users need to quickly focus on newly discovered items while preserving continuity with existing reviewed data.

**Independent Test**: Can be fully tested by running two analyses for the same video and verifying candidates introduced only by the latest run are visibly marked as new.

**Acceptance Scenarios**:

1. **Given** a video already has historical candidates, **When** a new analysis adds candidates with spellings not previously present for that video, **Then** only those differently spelled candidates are marked as new.
2. **Given** the latest analysis re-detects candidates whose spelling already exists in prior video data, **When** review opens, **Then** those candidates are not marked as new.
3. **Given** a candidate is marked as new, **When** the user explicitly confirms, rejects, or edits that candidate, **Then** the new marker is cleared for that candidate.

---

### User Story 3 - Shift Project Controls To Video-Centric Navigation (Priority: P3)

As a user, I can manage video projects from a dedicated Videos view and configure the project location from a dedicated settings entry point, instead of changing output fields during analysis.

**Why this priority**: This makes video projects the primary unit and keeps analysis focused on running scans.

**Independent Test**: Can be fully tested by navigating to analysis, confirming output filename/project-location controls are absent there, opening settings via the top-row gear icon to set project location, and loading/managing projects from the Videos view.

**Acceptance Scenarios**:

1. **Given** I am on analysis view, **When** I inspect controls, **Then** output filename input is not shown.
2. **Given** I am on analysis view, **When** I inspect controls, **Then** project location is not directly editable there.
3. **Given** I need to change project location, **When** I click the small gear icon in the top row, **Then** I can access a dedicated settings view where project location is configured.
4. **Given** I need to open or manage existing video projects, **When** I open the former History area, **Then** it is presented as a Videos view focused on loading and managing video projects from the configured location.
5. **Given** the configured project location already contains video projects, **When** I open the Videos view, **Then** projects are discovered from that location directly without relying on a separate app-level history list.
6. **Given** this is the user's first run, **When** analysis is opened, **Then** a default project location from app-level settings is already in effect and the user is not blocked on defining one manually.

### Edge Cases

- What happens when review opens for a video with only one analysis run and no historical data? The system still auto-loads that single run and shows no historical merge conflicts.
- What happens when the configured project location is missing, unavailable, or not writable? The system shows a clear blocking message with recovery guidance and does not silently drop analysis/review data.
- What happens when the same spelling appears in both prior and latest runs? The candidate remains unmarked as new because the spelling already exists in prior video data.
- What happens when a candidate differs only by spelling from prior existing candidates? The candidate is marked as new because the new marker is based on different spelling, even if it may later merge into an existing reviewed context.
- What happens when prior reviewed status conflicts with a new analysis result for the same candidate? The prior human-reviewed status remains authoritative, and the new run contributes evidence without automatically changing that decision.
- What happens when the user leaves and reopens review before acting on a new candidate? The candidate remains marked as new until an explicit review action clears that status.
- What happens when a video URL is unavailable in metadata for an older project? The review source display uses a stable fallback label while remaining read-only.
- What happens when the configured project location has zero projects? The Videos view shows an empty state with clear next actions.
- What happens when app-level history data from older versions still exists? The system ignores it for project discovery and uses only the configured project location as the source of truth.
- What happens when the default project location is unavailable on first run? The system shows a clear recovery path to choose or repair the location before analysis or project loading continues.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST automatically open review context for the analyzed video after an analysis run without requiring manual result-file loading.
- **FR-002**: The system MUST combine all available output data for the selected video into one review context.
- **FR-003**: The system MUST scope review loading to the selected video and MUST NOT merge data across different videos.
- **FR-003a**: When merged review data contains a conflict between prior human-reviewed status and newly analyzed evidence for the same candidate, the system MUST preserve the prior human-reviewed status unless the user explicitly changes it.
- **FR-004**: The review UI MUST remove user-editable result-file input and load actions.
- **FR-005**: The review UI MUST show the video URL as a read-only source indicator.
- **FR-006**: The system MUST mark candidates introduced by the latest analysis run as new.
- **FR-007**: The system MUST preserve existing candidate states and MUST NOT relabel historical candidates as new.
- **FR-007a**: The system MUST keep a candidate marked as new until the user explicitly confirms, rejects, or edits that candidate.
- **FR-007b**: The system MUST assign the new marker only to candidates whose spelling differs from previously existing candidates for the same video.
- **FR-008**: The analysis UI MUST remove output filename input from user-facing controls.
- **FR-009**: The analysis UI MUST treat project location as a global/project setting rather than an in-form per-run control.
- **FR-010**: The application MUST provide a dedicated settings view reachable via a small gear icon in the top row for configuring project location.
- **FR-011**: The former History view MUST be replaced by a Videos view centered on loading and managing projects from the configured project location.
- **FR-012**: The Videos view MUST allow users to locate, open, and manage existing video projects without requiring file-path entry.
- **FR-013**: When project location configuration changes, the Videos view MUST reflect projects in the newly configured location.
- **FR-014**: The Videos view MUST discover available projects by scanning the configured project location directly.
- **FR-015**: The system MUST NOT require or maintain a separate app-level history list or app-level history setting for project discovery.
- **FR-016**: The system MUST define a default project location in app-level settings and use it automatically on first run.
- **FR-017**: The system MUST NOT require users to manually define a project location before starting analysis for the first time unless the default location is unavailable or unusable.
- **FR-018**: During analysis execution, the progress window MUST display whether the results will be written to a new project or merged with an existing project for the video.
- **FR-019**: After analysis completes successfully, the system MUST automatically transition to the review view for the analyzed video without waiting for user action.

### Key Entities *(include if feature involves data)*

- **Video Project**: Represents one video as the primary unit, with combined analysis/review artifacts and associated metadata.
- **Analysis Run Record**: Represents one completed analysis execution for a video, including run ordering relative to previous runs.
- **Review Context**: Represents the merged candidate/group state produced from all runs for one video.
- **Candidate Freshness Flag**: Represents whether a candidate is first introduced in the latest run for that video.
- **Project Location Setting**: Represents the configured filesystem location where video projects are discovered and managed.
- **Default Project Location**: Represents the initial app-level project location value applied automatically before the user customizes settings.
- **Project Discovery Source**: Represents the configured project location as the single authoritative source for which video projects appear in the Videos view.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In at least 95% of validation attempts, users can enter review for a newly analyzed video without performing any manual file-load step.
- **SC-002**: In at least 99% of validation comparisons, review data shown for a video matches the combined outputs of that video and excludes other videos.
- **SC-003**: In at least 95% of user tests, participants correctly identify new candidates from the latest run on first pass.
- **SC-004**: In at least 90% of usability checks, users can find and use project location settings through the top-row gear entry point without guidance.
- **SC-005**: In at least 95% of usability checks, users can open an existing project from the Videos view within 30 seconds.
- **SC-006**: In at least 95% of user tests, participants understand whether a new project is being created or results are being merged based solely on the progress window message during analysis.
- **SC-007**: In at least 95% of validation runs, the review view automatically opens within 2 seconds of analysis completion without manual user action.

## Assumptions

- Existing per-video storage conventions remain available so prior runs can be merged for the same video.
- Latest analysis run order can be determined consistently for each video project.
- Video URL metadata is available for most projects; if absent, a stable read-only fallback label is acceptable.
- Renaming History to Videos does not require changing unrelated analytics or audit logs, and any legacy app-level history data can be left unread for this workflow.
- The application can determine and persist a sensible default project location in app-level settings on first run.
- Users have permission to access the configured project location during normal operation.
