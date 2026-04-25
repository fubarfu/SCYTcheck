# Feature Specification: Collapsable Review Groups with Player Name Management

**Feature Branch**: `010-collapse-player-groups`  
**Created**: 2026-04-25  
**Status**: Draft  
**Input**: User description: "groups in the review view should be collapsable and show as collapsed as default when all candidates inside are identical. That player name is considered accepted for such a group. If candidates in a group are different they show as default open as this is an issue to be resolved. Groups with different spelled player names are collapsable and the issue is resolved, if only identical candidates in a group are confirmed, or all not rejected names are identical. Further there cannot be two groups with the same accepted player name."

> This feature enhances the review interface for video analysis results, allowing users to efficiently manage 
> player name disambiguation through collapsible grouping and visual prioritization of unresolved issues.

## Clarifications

### Session 2026-04-25

- Q: Are player names considered personally identifiable information that requires special handling? → A: Player names are public/non-sensitive data - treat like any other text
- Q: Where should confirmed player names and group resolution state be stored? → A: Auto-saved to local file system (CSV/JSON) - persistent locally, included in standard export workflow
- Q: What is the interaction pattern for confirming candidates? → A: Radio button per candidate - only one can be selected at a time per group (selecting a new one auto-deselects the old)
- Q: What is the rejection workflow for candidates? → A: Rejected candidates remain visible but visually marked (strikethrough, grayed out, X badge); user can undo rejection
- Q: How should confirmation feedback and validation errors be communicated? → A: Both inline + visual indicator - error displays inline in red below candidate; success shows inline green check; both persist until user takes next action

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Collapsed Groups with Consensus Names (Priority: P1)

A user opens the review view for a video analysis result and sees player name candidate groups. Groups where all candidates have identical spellings are already collapsed by default, with the consensus name displayed. This reduces visual clutter for resolved candidates.

**Why this priority**: Users need to quickly identify which player names are already consensus and which require manual review. This is the core workflow.

**Independent Test**: Can be fully tested by opening a review session with some identical candidate names and verifying they appear collapsed showing the consensus name, delivering immediate clarity on resolved candidates.

**Acceptance Scenarios**:

1. **Given** a group with three identical candidates "John Smith", **When** the review view loads, **Then** the group is collapsed and displays "John Smith" with a collapsed indicator
2. **Given** multiple consensus groups, **When** the user views the review panel, **Then** all consensus groups appear collapsed without user action
3. **Given** a collapsed group, **When** the user expands it, **Then** the group displays all identical candidate occurrences with their metadata (frame/timestamp)

---

### User Story 2 - View Expanded Groups with Conflicting Names (Priority: P1)

A user opens the review view and sees groups where candidates have different spellings are automatically expanded. This visually highlights decision points requiring user attention.

**Why this priority**: Users must immediately see which player names have conflicts and need resolution. This is essential for efficient review workflow.

**Independent Test**: Can be fully tested by loading a review with conflicting candidate spellings and verifying they appear expanded by default, delivering focus on issues that need resolution.

**Acceptance Scenarios**:

1. **Given** a group with different candidates "John Smith", "Jon Smith", "John Smyth", **When** the review view loads, **Then** the group is expanded and shows all variants
2. **Given** multiple conflicting groups, **When** the user views the review panel, **Then** all conflict groups appear expanded automatically
3. **Given** an expanded conflict group, **When** the user collapses it manually, **Then** the collapse state is remembered in the session

---

### User Story 3 - Confirm Candidates and Achieve Consensus (Priority: P1)

A user resolves a conflicting group by selecting/confirming one candidate name, or by rejecting all others to establish consensus. The system validates that the chosen name doesn't duplicate other groups' accepted names.

**Why this priority**: This is the core resolution action that moves issues from open to resolved state.

**Independent Test**: Can be fully tested by selecting a candidate in a conflict group, verifying it becomes the accepted name, and checking that the group collapses when only that name remains confirmed.

**Acceptance Scenarios**:

1. **Given** a conflict group with "John Smith" and "Jon Smith", **When** the user selects "John Smith" to accept it, **Then** that candidate is marked as confirmed
2. **Given** all other candidates are rejected leaving only one, **When** the group resolves to consensus, **Then** the group automatically collapses
3. **Given** a confirmed candidate, **When** the user views the group, **Then** the accepted name appears visually distinct (e.g., highlighted, checked)

---

### User Story 4 - Prevent Duplicate Accepted Names Across Groups (Priority: P1)

The system prevents the user from accepting the same player name in two different groups. If a conflict occurs, the system provides clear feedback about which other group already uses that name.

**Why this priority**: Data integrity and preventing ambiguous player references is critical for analysis results.

**Independent Test**: Can be fully tested by attempting to confirm a name that's already accepted in another group and verifying the system prevents the action with clear messaging.

**Acceptance Scenarios**:

1. **Given** Group A has accepted name "John Smith", **When** the user tries to confirm "John Smith" in Group B, **Then** the system blocks the action and displays an error indicating Group A already uses "John Smith"
2. **Given** a duplicate name conflict, **When** the error is displayed, **Then** the message includes a link/reference to the other group to help user resolve the conflict
3. **Given** the user sees a duplicate warning, **When** they select a different name instead, **Then** the confirmation succeeds

---

### User Story 5 - Manage Collapse State for Resolved Groups (Priority: P2)

Users can manually collapse/expand groups at any time. Collapsed groups remain visually compact but still show enough information to confirm they are resolved (e.g., showing the accepted name or a count of identical candidates).

**Why this priority**: Users should have control over UI layout while reviewing, enabling efficient scanning of large candidate lists.

**Independent Test**: Can be fully tested by manually toggling collapse/expand on resolved groups and verifying state persists during the session.

**Acceptance Scenarios**:

1. **Given** a collapsed group, **When** the user clicks the collapse toggle, **Then** the group expands showing all candidates and metadata
2. **Given** an expanded resolved group, **When** the user clicks the collapse toggle, **Then** the group collapses showing only the accepted name
3. **Given** multiple groups with mixed collapse states, **When** the user performs a collapse-all or expand-all action (if provided), **Then** all groups respond accordingly

---

### Edge Cases

- What happens when a group has only one candidate? (Should appear as consensus/collapsed by default)
- How does the system handle when all candidates in a group are rejected? (Requires user intervention to select at least one)
- What if a user undoes a confirmation after locking in an accepted name? (Allows changing to another candidate if it doesn't conflict)
- How does the system display groups during the confirmation workflow before any final decision is made?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display candidate groups in the review view where each group represents player instances detected at the same location/context
- **FR-002**: System MUST automatically collapse groups where 100% of candidates have identical spelling
- **FR-003**: System MUST automatically expand groups where candidates have different spellings
- **FR-004**: System MUST visually indicate the collapse/expand state with UI controls (e.g., chevron, arrow, expand icon)
- **FR-005**: System MUST allow users to manually toggle collapse/expand state on any group
- **FR-006**: System MUST persist collapse state during a review session
- **FR-007**: System MUST display the accepted player name prominently when a group is collapsed
- **FR-008**: System MUST display all candidate variants with occurrence metadata (frame number, timestamp, detection confidence) when a group is expanded
- **FR-009**: System MUST allow users to confirm/select one candidate as the accepted name for a group using a radio button interface (mutually exclusive selection within a group)
- **FR-010**: System MUST automatically deselect previous selection when user selects a new radio button (only one accepted name per group at any time)
- **FR-011**: System MUST allow users to reject individual candidates within a group (independent of radio button acceptance) by marking with explicit reject action
- **FR-012**: System MUST visually distinguish rejected candidates (strikethrough, grayed out, or X badge) while keeping them visible for context and potential undo
- **FR-013**: System MUST allow users to undo/un-reject a candidate that was previously marked as rejected
- **FR-014**: System MUST automatically resolve a group to consensus when only identical candidates remain (confirmed and not rejected)
- **FR-015**: System MUST enforce uniqueness constraint: prevent the same player name from being accepted in multiple groups
- **FR-016**: System MUST display a clear error message when a user attempts to confirm a duplicate player name, including reference to the conflicting group
- **FR-017**: System MUST mark a group as "resolved" when it achieves consensus (either all identical or all-but-one rejected)
- **FR-018**: System MUST mark a group as "unresolved" when conflicts remain (multiple different spellings with no clear consensus)
- **FR-019**: System MUST provide visual distinction between resolved and unresolved groups (e.g., color, badge, font styling)
- **FR-020**: System MUST support undoing a confirmation action within the session to allow changing the accepted name via radio button deselection
- **FR-021**: System MUST validate that at least one candidate remains accepted per group before allowing session completion
- **FR-022**: System MUST display inline validation feedback (green checkmark) when candidate selection succeeds, positioned directly below the selected radio button
- **FR-023**: System MUST display inline validation feedback (red error text) when candidate selection fails due to duplicate name conflict, positioned directly below the selected radio button
- **FR-024**: System MUST include in error message the name of the conflicting group when duplicate name detected
- **FR-025**: System MUST persist inline validation feedback (success or error) until user takes a subsequent action (e.g., selects different candidate, rejects candidate)

### Key Entities *(include if feature involves data)*

- **CandidateGroup**: Represents a collection of player name candidates detected together
  - `groupId`: Unique identifier
  - `candidates[]`: List of candidate names with metadata (frame, timestamp, confidence)
  - `acceptedName`: The player name confirmed as correct for this group
  - `rejectedCandidates[]`: Candidates explicitly rejected by user
  - `collapseState`: Boolean indicating current UI collapse state
  - `resolutionStatus`: RESOLVED | UNRESOLVED | IN_PROGRESS

- **Candidate**: Individual player name occurrence
  - `text`: The detected player name string
  - `frameNumber`: Frame where detected
  - `timestamp`: Video timestamp
  - `confidence`: OCR/detection confidence score

- **ReviewSession**: Manages the overall review workflow
  - `sessionId`: Unique identifier
  - `candidateGroups[]`: All groups being reviewed
  - `groupCollapseStates`: Map of groupId → collapse state
  - `status`: IN_PROGRESS | COMPLETED | ABANDONED

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Consensus groups (100% identical candidates) are collapsed by default on 100% of review sessions
- **SC-002**: Conflict groups (mixed spellings) are expanded by default on 100% of review sessions
- **SC-003**: Users can resolve a player name conflict and confirm selection in under 10 seconds per group (including reviewing candidates and selecting accepted name)
- **SC-003b**: Validation feedback (success or error) appears within 500ms of user confirming a candidate selection
- **SC-003c**: 100% of duplicate name conflicts are caught and communicated with inline error message before session can be saved
- **SC-004**: System prevents duplicate accepted names across groups on 100% of attempted conflicts with clear error feedback
- **SC-005**: Collapse/expand state persists across user interactions during a review session (until explicit state change)
- **SC-006**: Review session completion requires 100% of groups to have an accepted player name with no duplicates
- **SC-007**: Users report improved clarity and efficiency in review workflow compared to flat candidate list (via usability testing)
- **SC-008**: Zero data integrity issues: no duplicate player names in final exported results

## Assumptions

- Single video analysis result per review session (not batch review of multiple videos simultaneously)
- Player name candidates are pre-grouped by the analysis engine before review view is presented
- Users are familiar with confirm/reject/select UI patterns from the existing analysis application
- Internet connectivity is stable during review session
- Browser/UI supports common CSS transitions for collapse/expand animations
- Existing authentication and session management will be reused
- Player names use consistent character encoding (no special Unicode issues)
- Groups contain 1-50 candidates on average (performance tested within this range)
