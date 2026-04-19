# Feature Specification: Continuous Sidecar Log Writing

**Feature Branch**: `006-sidecar-log-streaming`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "the sidecar log is continuously filled if activated during analysis, rather than written at the end of analysis, so if the analysis is interrupted the log remains with the entries up to this point"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Partial Log Preserved on Interruption (Priority: P1)

A user starts an analysis run with the sidecar log feature activated. Midway through, the analysis stops unexpectedly — the user cancels it, the application closes, or the video stream drops. When the user opens the sidecar log file, it already contains every entry generated up to the moment of interruption, without any entries missing.

**Why this priority**: This is the core motivation for the feature. The entire value lies in never losing log data when a run does not finish. Without this, the feature does not exist in any meaningful form.

**Independent Test**: Can be fully tested by starting an analysis with sidecar log enabled, interrupting it partway through, and verifying the log file contains all entries recorded prior to interruption.

**Acceptance Scenarios**:

1. **Given** sidecar log is activated and an analysis is running, **When** the user cancels the analysis after some frames are processed, **Then** the log file on disk contains every entry that was generated before the cancellation.
2. **Given** sidecar log is activated and analysis is running, **When** the application terminates unexpectedly, **Then** the log file retains all entries written before the termination event.
3. **Given** sidecar log is activated and analysis is running, **When** the analysis reaches the end normally, **Then** the log file contains all entries — identical in content to the current behavior.

---

### User Story 2 - Log Visible in Real Time (Priority: P2)

A user monitoring the sidecar log file externally (for example, tailing the file in a text editor or another tool) can observe entries appearing as each frame is processed, not only after the full analysis completes.

**Why this priority**: Enables live monitoring and adds transparency to long-running analyses without depending on completing them first.

**Independent Test**: Can be fully tested by opening the log file in a tool that auto-refreshes and confirming new entries appear continuously during analysis.

**Acceptance Scenarios**:

1. **Given** sidecar log is activated and analysis has been running for several frames, **When** the user checks the log file mid-run, **Then** entries for already-processed frames are present in the file.
2. **Given** sidecar log is activated and analysis is running, **When** the user checks the log file at any point after the tenth frame, **Then** at least the first ten entries are present, regardless of whether analysis has completed.

---

### User Story 3 - No Regression When Sidecar Log Is Inactive (Priority: P3)

A user runs an analysis with the sidecar log feature deactivated. No log file is created or modified, exactly as today.

**Why this priority**: Existing behavior for users who do not use the sidecar log must be unchanged.

**Independent Test**: Can be fully tested by running a complete analysis with sidecar log deactivated and confirming no log file is written.

**Acceptance Scenarios**:

1. **Given** sidecar log is deactivated, **When** the user runs a full analysis, **Then** no sidecar log file is created or modified.

---

### Edge Cases

- What happens when the target disk is full while an incremental write is attempted mid-analysis?
- What happens if the log file is locked by another process when an entry write is attempted?
- What happens if the log file is deleted by the user while analysis is in progress?
- What happens when analysis completes with zero frames processed (empty log)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When the sidecar log is activated, each log entry MUST be written to the log file immediately upon generation, without waiting for analysis to complete.
- **FR-002**: The sidecar log file MUST be updated incrementally throughout analysis so that at any point during a run, the file on disk reflects all entries generated so far.
- **FR-003**: If analysis is interrupted at any point — by user cancellation, application termination, or any other cause — the sidecar log file MUST contain all entries recorded up to that point.
- **FR-004**: A failure to write an individual log entry MUST NOT stop analysis from continuing; entry write failures MUST be non-fatal to the analysis run.
- **FR-005**: The sidecar log file content, structure, and format MUST remain unchanged from the current specification; no schema or format changes are introduced by this feature.
- **FR-006**: When the sidecar log is deactivated, no log file MUST be created or written at any point during or after analysis.
- **FR-007**: Writing a log entry during analysis MUST NOT introduce a perceptible delay between the processing of consecutive frames.

### Key Entities

- **Sidecar Log File**: The output file written alongside analysis results when the sidecar log feature is active. Contains one entry per processed frame, in the existing defined format.
- **Log Entry**: A single record capturing the result of processing one frame or unit during analysis, written in the existing log format without modification.
- **Analysis Run**: The bounded execution of the frame-by-frame analysis process, from start to either normal completion or interruption.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When an analysis is interrupted at any point after at least one frame is processed, 100% of log entries generated before the interruption are present in the sidecar log file.
- **SC-002**: The time between consecutive frame analyses is not measurably increased compared to a run with sidecar log deactivated (within normal variance).
- **SC-003**: A fully completed analysis run produces a sidecar log file with identical content to the current behavior, verified by byte-level comparison.
- **SC-004**: An external observer checking the sidecar log file after frame N is processed finds at least N entries in the file, for any N greater than zero.

## Assumptions

- The sidecar log activation is an existing user-configurable setting; this feature does not change how it is activated or deactivated.
- The sidecar log file uses an existing, already-defined format; no format changes are in scope.
- Each frame produces exactly one log entry at the time it is processed.
- The existing export/logging infrastructure can be adapted to support per-entry writes without requiring a full redesign.
- Analysis interruption covers: user-initiated cancellation, unexpected application exit, and loss of the video source (for live streams).
- Running out of disk space during a log write is considered a rare edge case; non-fatal handling (skip the entry and continue) is an acceptable response.
