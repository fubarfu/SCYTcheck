# Feature Specification: Web-Based Player Name Verification UI

**Feature Branch**: `feature/007-web-based-player-ui`  
**Created**: 2026-04-19  
**Status**: Draft  
**Input**: User description: "A modern sleek web-based UI, that supports the user in his workflow of identifying and verifying player names."
**Clarification addendum (session 2)**: In the Review view, candidates are shown grouped by visual/textual similarity. Names found close together in time are treated as stronger candidates for being the same player. Each name occurrence shows a small clickable video frame thumbnail (enlarges on click) and a direct YouTube deep link to the exact timestamp. Additional contextual information per name may also be shown.

## User Scenarios & Testing *(mandatory)*

### User Story 0 - Launch the App and Land on the Web UI (Priority: P0)

The user double-clicks the portable executable. The app starts a local HTTP server and automatically opens the user's default browser to `localhost`. The web UI loads and presents the main application interface. No installation, configuration, or manual browser navigation is needed.

**Why this priority**: This is the entry point for all other stories. If launch fails, nothing else works.

**Independent Test**: Can be fully tested by running the portable exe and verifying that the browser opens to a functional UI page without any manual steps.

**Acceptance Scenarios**:

1. **Given** the user runs the portable executable, **When** it starts, **Then** the local HTTP server starts and the default browser opens to the **Analysis** view within 5 seconds.
2. **Given** the browser is already open to the UI and the user closes and re-runs the exe, **When** the server is already running, **Then** a new browser tab opens (or the existing tab is focused) rather than showing a port conflict error.
3. **Given** the browser tab is closed while the server is still running, **When** the user re-opens the URL manually, **Then** the UI loads on the **Analysis** view and all previous review state is intact.
4. **Given** the user is on the Analysis view, **When** they click the Review navigation item, **Then** the Review view is displayed without a page reload.

---

### User Story 1 - Configure and Run Video Analysis (Priority: P1)

From the web UI, the user enters a YouTube URL or selects a local video file, configures analysis settings (such as the on-screen region to scan), and starts the analysis. The UI displays real-time progress. When analysis completes, the results are immediately available for review without any additional steps.

**Why this priority**: The web UI replaces the existing Tkinter UI entirely; analysis must be initiatable from within it.

**Independent Test**: Can be fully tested by entering a video source, starting analysis, and verifying that a result set appears in the review view upon completion.

**Acceptance Scenarios**:

1. **Given** the user is on the main screen, **When** they enter a YouTube URL or select a local video file, **Then** the UI validates the input and enables the "Start Analysis" action.
2. **Given** analysis is running, **When** frames are processed, **Then** the UI displays a live progress indicator (frames processed / total estimated).
3. **Given** analysis completes, **When** results are ready, **Then** the UI transitions directly to the candidate review view for that result set.
4. **Given** analysis is running, **When** the user clicks "Stop", **Then** analysis halts gracefully and partial results (if any) are available for review.

---

### User Story 2 - Review Detected Player Name Candidates (Priority: P2)

After analysis completes (or when loading a previously saved result), the user is presented with a list of all text strings detected by OCR that are candidates for player names. The user goes through each candidate and marks it as either a confirmed player name or rejects it as irrelevant text (e.g., scoreboard labels, numbers, artefacts). The user can also correct OCR transcription errors inline before confirming.

**Why this priority**: This is the core review workflow the feature is designed to support.

**Independent Test**: Can be fully tested by loading a sample analysis result (CSV), reviewing candidates in the UI, confirming/rejecting each, and exporting the final verified list — without involving any other user stories.

**Acceptance Scenarios**:

1. **Given** an analysis result has been loaded, **When** the user opens the Review view, **Then** all detected text candidates are listed grouped by similarity, each showing: the detected text, timestamp, a small video frame thumbnail, and a YouTube deep link to that timestamp.
2. **Given** a candidate occurrence is displayed, **When** the user clicks the thumbnail, **Then** a larger version of the video frame is shown (e.g., in an overlay or modal).
3. **Given** a candidate is displayed, **When** the user marks it as "Confirmed", **Then** the candidate is visually distinguished from unreviewed and rejected candidates.
4. **Given** a candidate is displayed, **When** the user marks it as "Rejected", **Then** the candidate is removed from the confirmed list without being deleted, so the decision can be reversed.
5. **Given** a candidate has an OCR transcription error, **When** the user edits the displayed text inline, **Then** the corrected name is used in the final export instead of the raw OCR value.
6. **Given** the user has reviewed all candidates, **When** the user triggers export, **Then** a file is produced containing only the confirmed (and optionally corrected) player names.

---

### User Story 3 - Search and Filter Candidates (Priority: P3)

The user needs to quickly locate a specific player name or a group of similar-looking candidates across a long list of detections. The user types into a search field to filter the displayed list in real time, reducing the visible set to only matching entries.

**Why this priority**: Analysis sessions on longer videos may yield hundreds of text candidates. Without filtering, the review workflow becomes impractical.

**Independent Test**: Can be fully tested by loading a result set and typing into the search field; verified when the displayed list updates to show only matching entries.

**Acceptance Scenarios**:

1. **Given** a list of candidates is displayed, **When** the user types a partial name into the search field, **Then** only candidates containing that substring (case-insensitive) remain visible.
2. **Given** an active search filter is applied, **When** the user clears the search field, **Then** all candidates are visible again.
3. **Given** a filter is active, **When** the user confirms or rejects a visible candidate, **Then** the action applies only to that candidate and does not affect hidden candidates.

---

### User Story 4 - Bulk Confirmation of Similar Names (Priority: P4)

The user wants to confirm all occurrences of the same player name with a single action. The UI groups visually similar text detections together (based on approximate matching) so the user can confirm or reject the whole group at once.

**Why this priority**: In a typical analysis session, the same player's name may appear in dozens of frames. Reviewing each occurrence individually is inefficient.

**Independent Test**: Can be fully tested by loading a result set that contains repeated occurrences of the same text, grouping them, and confirming the group in one action.

**Acceptance Scenarios**:

1. **Given** multiple candidates with identical or near-identical text are present, **When** the list is displayed, **Then** they are visually grouped under a shared heading.
2. **Given** a group is displayed, **When** the user confirms the group, **Then** all candidates in the group are marked as confirmed.
3. **Given** a group is displayed, **When** the user expands the group, **Then** individual candidates within the group are shown with their individual timestamps, and each can be individually overridden.

---

### User Story 5 - Load and Navigate Multiple Analysis Sessions (Priority: P5)

The user has multiple analysis result files (from different videos or runs). The user can open any of them from within the web UI, switch between sessions, and the review state for each session is preserved between visits.

**Why this priority**: Users commonly analyze multiple videos in one sitting; the ability to manage sessions in one place reduces context-switching.

**Independent Test**: Can be fully tested by loading two separate result files in the same UI session and verifying that confirming a candidate in one does not affect the other.

**Acceptance Scenarios**:

1. **Given** the user opens the UI, **When** they select a result file, **Then** its candidates are loaded and displayed.
2. **Given** the user has partially reviewed session A and switches to session B, **When** the user returns to session A, **Then** all previously confirmed/rejected decisions are still present.

---

### Edge Cases

- What happens when the loaded result file contains zero text candidates?
- If the user clears a candidate's corrected name, the UI must reject the empty value inline, preserve the previous non-empty value, and require either a valid replacement or edit cancellation.
- If inline editing changes a candidate's normalized text so it now matches a different group better, grouping must be recomputed immediately, the candidate must move automatically to the best-matching group, and the UI must show a clear notice explaining the move.
- Result files that are malformed or from an incompatible format version must be rejected before the review session opens; the UI shows a clear error state and does not create a partial session.
- If the user closes the browser tab mid-review, all accepted changes up to the most recent mutating action must already be persisted and restored when the session is reopened.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The UI MUST provide an in-browser folder picker control that allows the user to select a directory; the server then scans that directory and lists all CSV result files found within it for the user to choose from.
- **FR-002**: The UI MUST display all detected text candidates from the loaded result. Each occurrence MUST show: the detected (or corrected) text, the source frame timestamp, a small clickable thumbnail of the video frame at that timestamp (enlarges to a larger view on click), and a direct YouTube deep link to the video at that exact timestamp.
- **FR-003**: Users MUST be able to mark any candidate as "Confirmed" (verified player name) or "Rejected" (not a player name).
- **FR-004**: Users MUST be able to reverse a confirm or reject decision at any time before export.
- **FR-005**: Users MUST be able to edit the displayed text of a candidate inline to correct OCR errors; the corrected text is used in place of the original in exports. Empty corrected values MUST be rejected inline; the prior non-empty value remains in effect until the user enters a valid replacement or cancels the edit.
- **FR-006**: The UI MUST provide a real-time search/filter input that narrows the visible candidate list to entries matching a user-supplied substring.
- **FR-007**: The UI MUST visually group candidates by similarity using two signals: (1) fuzzy text similarity (threshold ≥ 80% by default, user-adjustable 50–100%), and (2) temporal proximity — occurrences found close together in time are treated as stronger candidates for belonging to the same group. The similarity threshold MUST be user-adjustable via a UI control; changing it re-computes groupings immediately. Inline text edits that change grouping eligibility MUST also trigger immediate regrouping.
- **FR-008**: Users MUST be able to confirm or reject an entire group of near-identical candidates in a single action. Users MUST also be able to select one or more specific candidates within a group as correct (confirmed); non-selected group members MUST remain unchanged unless explicitly actioned by the user.
- **FR-009**: Users MUST be able to expand a group to review and individually override individual candidates within it.
- **FR-010**: The UI MUST allow users to export two output files upon completing a review: (1) a deduplicated player names CSV — one row per unique confirmed name (using corrected text where edited), and (2) a full occurrences CSV — one row per confirmed candidate occurrence, retaining timestamp and source frame reference columns.
- **FR-011**: The review state (confirmed, rejected, edited values) MUST be persisted by the Python server as a JSON sidecar file written alongside the source CSV; state is restored automatically when the same result file is loaded in a future session. Persistence MUST occur immediately after each user action that mutates session state so no explicit save step is required.
- **FR-012**: The UI MUST visually differentiate between unreviewed, confirmed, and rejected candidates at a glance.
- **FR-013**: The UI MUST display a progress indicator showing how many candidates have been reviewed vs. total.
- **FR-014**: The UI MUST support loading multiple result files and switching between them without losing review state.
- **FR-015**: The UI MUST be accessible and functional on a standard desktop browser without requiring installation of any browser extension.
- **FR-016**: The portable executable MUST start the local HTTP server automatically on launch and open the user's default browser to the UI without any manual steps.
- **FR-017**: The web UI MUST provide controls to enter a YouTube URL or select a local video file as the analysis source.
- **FR-018**: The web UI MUST expose all analysis configuration options and operational controls available in the former Tkinter UI (full parity — no existing setting or legacy workflow control may be dropped). Additional settings may be introduced in this feature if they naturally arise during implementation.
- **FR-019**: The web UI MUST display real-time analysis progress (frames processed vs. estimated total) while analysis is running.
- **FR-020**: Users MUST be able to stop a running analysis from within the web UI; any partial results produced up to that point MUST be preserved and reviewable.
- **FR-021**: The web UI MUST read and write user preferences (analysis settings) using the existing `scytcheck_settings.json` file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, with local fallback). No new settings file is introduced.
- **FR-022**: The web UI MUST provide an interactive region selector: the Python server captures a representative frame from the selected video source and serves it to the browser; the user clicks and drags on the displayed frame to draw a rectangle defining the on-screen area to scan for text. The selected region is persisted in `scytcheck_settings.json`.
- **FR-023**: The web UI MUST be structured as two distinct named views — **Analysis** (video source input, settings configuration, region selector, run/stop controls, live progress) and **Review** (candidate list, search/filter, grouping, export) — accessible at all times via a persistent top-level navigation bar.
- **FR-024**: For each candidate occurrence in the Review view, the UI MUST display a small thumbnail image of the video frame at the detection timestamp. The thumbnail MUST be clickable and enlarge to a readable size on click (e.g., in a modal or overlay). The analysis pipeline MUST capture and save the relevant video frame image to disk at the moment each detection occurs; frames are written to a sibling folder alongside the result CSV (e.g., `result_frames/` next to `result.csv`). For local video sources, on-demand server-side extraction (with caching to the same sibling folder) is acceptable as a fallback when saved frames are unavailable.
- **FR-025**: For each candidate occurrence in the Review view, the UI MUST display a direct link to the YouTube video at the exact detection timestamp (deep link with `?t=` parameter). This link MUST only be shown when the analysis source was a YouTube URL; it MUST be omitted for local video file sources.
- **FR-026**: The Review view MUST visually indicate when candidate occurrences within the same group were detected in temporal proximity to each other, making it easy for the user to assess how strongly the grouping is supported.
- **FR-027**: The Review view MUST provide an unlimited undo mechanism that allows the user to reverse any review action (confirm, reject, remove, edit, reorder, regroup) by walking back through the full session action history in order.
- **FR-028**: The user MUST be able to reorder group cards in the Review view (drag-and-drop or equivalent). Reordering of individual candidates within a group is out of scope.
- **FR-029**: The user MUST be able to manually regroup candidates by (1) moving a candidate from one group to another and (2) merging two groups into one. Manual group split operations are out of scope.
- **FR-030**: The user MUST be able to permanently remove a candidate from the Review view. Removal is a hard delete from the session (distinct from "Rejected" which is reversible); the only recovery path is undo (FR-027). Removed candidates are not included in exports.
- **FR-031**: The Review view MUST provide system recommendations indicating which candidate names are most likely correct, displayed as non-blocking suggestions to assist user decisions. Recommendations MUST NOT auto-confirm, auto-reject, or otherwise change candidate state unless the user explicitly performs an action. Recommendation scores MUST be computed from a combined signal including occurrence frequency, OCR confidence, temporal consistency, and text-quality heuristics. Recommendations MUST be surfaced at both levels: (1) group-level ranking/prioritization, and (2) candidate-level confidence badges within each group. The user MUST be able to adjust a recommendation threshold in the Review UI (0-100, default 70) and see recommendation ranking/badges update immediately.
- **FR-032**: The web UI MUST support both dark mode and light mode. Dark mode MUST be the default theme on first launch. The selected theme MUST be persisted in the existing `scytcheck_settings.json` settings file; dark mode is only used when no prior user preference exists. On first run with no saved preference, the UI MUST ignore OS/browser color-scheme preference and start in dark mode. Theme switching MUST be available through a single global toggle in the persistent top navigation and apply across all views. Theme changes MUST apply immediately across the active UI without page reload. Both themes MUST meet WCAG AA contrast requirements for text and interactive controls.
- **FR-033**: The web UI MUST validate every loaded result CSV against the required schema and supported format version before opening a review session. Malformed or incompatible files MUST be rejected as a whole with a clear error state; the system MUST NOT load partial candidate data from such files.
- **FR-034**: When an inline text edit changes a candidate's normalized text sufficiently to affect grouping, the system MUST recompute grouping immediately, move the candidate to the best-matching group automatically, and display a clear non-blocking UI notice describing the regrouping change.

### Legacy UI Parity Inventory

All legacy Tkinter capabilities MUST remain available in the Stitch-designed web UI. The legacy surface maps to the **Analysis** view unless explicitly noted otherwise.

- **LP-001 Analysis**: YouTube URL input.
- **LP-002 Analysis**: Output folder picker with the same validation expectations (selected, exists, is a directory, writable).
- **LP-003 Analysis**: Auto-generated output filename preview derived from the source video identity.
- **LP-004 Analysis**: Primary analysis action that launches region selection and starts analysis.
- **LP-005 Analysis**: Export retry action when export fails after analysis.
- **LP-006 Analysis**: Live progress display including stage label, percent/progress indicator, and status text.
- **LP-007 Analysis**: Context pattern editor supporting one pattern per line with before/after/enabled semantics.
- **LP-008 Analysis**: Toggle to extract only names matching a context pattern.
- **LP-009 Analysis**: Video quality selector.
- **LP-010 Analysis**: Detailed sidecar log toggle.
- **LP-011 Analysis**: Matching tolerance control.
- **LP-012 Analysis**: Frame-change gating enable/disable toggle.
- **LP-013 Analysis**: Frame-change gating threshold control.
- **LP-014 Analysis**: Event merge gap control (seconds).
- **LP-015 Analysis**: OCR confidence/sensitivity control (0-100).
- **LP-016 Review**: No legacy-only controls originate in the former UI; the Review view is net-new functionality added by this feature and must coexist with, not replace, Analysis parity obligations.

### Key Entities

- **Analysis Result**: A set of OCR-detected text entries produced by a single video analysis run, each entry carrying detected text, a frame timestamp, and optional confidence metadata.
- **Candidate**: A single detected text entry within an Analysis Result, with review status (unreviewed / confirmed / rejected), an optional user-corrected text value, a frame timestamp, a reference to the captured thumbnail image for that frame, and (where applicable) a YouTube deep link URL.
- **Candidate Group**: A logical grouping of Candidates with identical or near-identical text, treated as a unit for bulk review actions.
- **Scan Region**: A user-defined rectangular area within the video frame, defined interactively by clicking and dragging on a captured preview frame in the browser. Stored in `scytcheck_settings.json` and applied by the analysis engine to restrict OCR to that area.
- **Review Session**: The persistent review state for one Analysis Result file, including all confirm/reject decisions and inline edits.
- **Verified Player List**: The output of a completed Review Session, produced as two export files: a deduplicated names CSV (one unique confirmed name per row) and a full occurrences CSV (one row per confirmed candidate occurrence with timestamp and frame reference metadata).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can complete full review and verification of a typical analysis result (up to 200 candidates) in under 5 minutes.
- **SC-002**: 100% of candidates present in the loaded result file are surfaced in the review UI — no candidates are silently omitted.
- **SC-003**: A user can perform confirm, reject, and edit actions without any page reload or navigation away from the current list.
- **SC-004**: Review state is never lost due to accidental page refresh — a user can return to the same session and resume exactly where they left off.
- **SC-005**: The UI responds to search input and confirm/reject actions within 200 milliseconds for result sets of up to 500 candidates. The candidate list MUST use plain DOM rendering with lazy-loaded thumbnails (images fetched only when scrolled into view via `IntersectionObserver` or `loading="lazy"`) to meet this target.
- **SC-006**: 90% of first-time users can complete the core review workflow (load → review → export) without requiring instructions.
- **SC-007**: The portable executable starts the local server and opens the browser to a functional UI within 5 seconds on a standard Windows desktop machine.

## Assumptions

- The web UI completely replaces the existing Tkinter UI; it is the sole user-facing interface for the entire application.
- The app is distributed as a portable PyInstaller executable. On launch, the exe starts a local HTTP server and automatically opens the user's default browser to `localhost`. No internet access or remote server is required.
- The existing analysis engine (video processing, OCR pipeline) is preserved unchanged; the web UI replaces only the frontend layer.
- The result file format produced by analysis is the CSV format already produced by the existing export service.
- Desktop browsers (latest stable Chrome, Firefox, or Edge) are the target environment; mobile browser support is out of scope.
- User preferences and analysis settings are persisted using the existing `scytcheck_settings.json` file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, with local fallback). The web UI reads and writes this same file; no new settings file is introduced.
- Review state per analysis result is persisted as a server-written JSON sidecar file in the same directory as the source CSV (e.g., `result.csv` → `result.review.json`). Browser storage is not used for persistence.
- Captured video frame thumbnails are stored in a sibling folder next to the result CSV (e.g., `result_frames/` alongside `result.csv`), keeping the full session (CSV, review JSON, frame images) self-contained in one directory.
- Near-identical text grouping uses two signals: fuzzy string similarity (default threshold 80%, user-adjustable 50–100%) and temporal proximity (occurrences close in time are treated as stronger grouping candidates). The combined signal is used to sort and visually rank groups.

## Clarifications

### Session 2026-04-19

- Statement: The web UI replaces the existing Tkinter UI entirely — the web UI is the full application interface, not a separate post-analysis review layer.
- Statement: The user launches the app via the existing portable (PyInstaller) executable; on launch, the exe starts a local HTTP server and opens the default browser to `localhost` automatically.
- Q: How is the web UI served and accessed? → A: Lightweight local Python HTTP server embedded in the portable exe; browser opens `localhost` automatically on launch.
- Q: How is review state persisted? → A: Server-side JSON sidecar file written alongside the source CSV (e.g., `result.review.json`); survives browser clears and server restarts.
- Q: What does the verified player name export contain? → A: Two files — (1) deduplicated names CSV (one unique name per row) and (2) full occurrences CSV (one row per confirmed candidate with timestamp/frame reference).
- Q: What is the fuzzy grouping similarity threshold and is it configurable? → A: Default 80%, user-adjustable via a UI slider or input field (range 50–100%); changing the value re-computes groupings immediately.
- Q: How does the user point the UI at their result CSV files? → A: In-browser folder picker control; the server scans the selected directory and lists all CSV files found.
- Q: Which Tkinter analysis settings must the web UI expose? → A: Full parity — every setting from the former Tkinter UI must be present; additional settings may be added if they arise naturally during implementation.
- Q: Where are user preferences/analysis settings persisted in the web UI? → A: Reuse the existing `scytcheck_settings.json` file (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, local fallback); no new settings file introduced.
- Q: How is the scan region selector implemented in the browser? → A: Server captures a representative frame and serves it to the browser; user clicks and drags on the displayed frame to draw the scan rectangle (mirrors current Tkinter behaviour).
- Q: What is the top-level navigation structure of the web UI? → A: Two distinct views — "Analysis" (configure + run) and "Review" (candidates + export) — switchable at any time via a persistent navigation bar.

### Session 2026-04-19 (continued)

- Statement: In the Review view, candidates are grouped by similarity; names found close in time are considered more likely to be the same player (temporal proximity is a grouping signal).
- Statement: Each candidate occurrence in the Review view shows a small clickable thumbnail of the video frame at that timestamp; clicking enlarges it.
- Statement: Each candidate occurrence shows a direct YouTube deep link to the video at the exact detection timestamp (only when the source was YouTube).
- Statement: Additional contextual information per name may be shown to help the user verify decisions.
- Q: What kind of additional contextual information is shown per candidate in the Review view? → A: External player lookup (name matched against a player database/roster) — desired direction, deferred to a later update; out of scope for this feature.
- Q: How are video frame thumbnails generated for the Review view? → A: On-demand — server generates and caches the thumbnail the first time the UI requests it for a given timestamp; not pre-generated during analysis.
- Q: How are thumbnails sourced when the video is a YouTube stream? → A: Captured and saved to disk during analysis — at each detection the frame is written to a cache folder alongside the result CSV; on-demand re-seeking into the stream is not required.
- Q: How should the candidate list be rendered in the Review view? → A: Plain DOM with lazy-loaded thumbnails — all rows rendered in DOM, thumbnail images fetched only when scrolled into view (IntersectionObserver / loading="lazy").
- Q: Where should captured frame thumbnail images be stored on disk? → A: Sibling folder next to the result CSV (e.g., `result_frames/` alongside `result.csv`), so the full session is self-contained in one directory.

### Session 2026-04-19 (continued 2)

- Statement: In the Review view, user can select one or multiple specific candidates within a group as correct; remaining group members keep their current state.
- Statement: The Review view has an undo mechanism for review actions.
- Statement: The user can reorder groups in the Review view.
- Statement: The user can manually regroup candidates by move and merge operations.
- Statement: The user can remove a candidate as a hard delete distinct from reject.
- Q: Is "remove a candidate" distinct from "reject"? → A: Yes — remove is a permanent hard delete from the session (distinct from reject, which is reversible); undo is the only recovery path.
- Q: How deep is the undo stack? → A: Unlimited — full session history; undo walks back through all actions in order.
- Q: What is the scope of reordering in the Review view? → A: Groups only — the user can drag group cards up/down; reordering individual candidates within a group is out of scope.
- Q: Which manual regroup operations are supported? → A: Move candidate between groups + merge two groups; manual split is out of scope.
- Q: When confirming one or multiple names in a similar-name group, what happens to non-selected names? → A: Non-selected names remain unchanged unless explicitly actioned.

### Session 2026-04-19 (continued 3)

- Statement: The system provides recommendations in the Review section for which names are most likely correct.
- Q: What should recommendation do in the Review UI? → A: Non-blocking suggestion only (confidence/rank indicator); no automatic state changes.
- Q: What inputs drive recommendation scoring? → A: Combined signal — occurrence frequency, OCR confidence, temporal consistency, and text-quality heuristics.
- Q: Where should recommendations appear in the Review UI? → A: Both — group-level ranking and candidate-level badges.
- Q: Should recommendation sensitivity be user-adjustable? → A: Yes — add adjustable threshold control in the Review UI with live updates.
- Q: What is the default recommendation threshold? → A: 70 (balanced default).

### Session 2026-04-19 (continued 4)

- Statement: The UI provides both dark mode and light mode, with dark mode as the default.
- Q: Should the selected theme be persisted across app restarts? → A: Yes — persist theme choice in existing `scytcheck_settings.json`; default to dark only when no preference exists.
- Q: Where should theme switching be exposed? → A: Single global toggle in the persistent top navigation across all views.
- Q: Should dark and light themes meet a specific contrast accessibility target? → A: Yes — require WCAG AA contrast compliance for text and interactive controls in both themes.
- Q: If no saved theme preference exists, should the app follow OS/browser scheme? → A: No — always start in dark mode on first run; ignore OS/browser scheme until user changes theme.
- Q: Should theme changes apply immediately without page reload? → A: Yes — apply theme instantly across the active UI.

### Session 2026-04-21

- Q: How should parity with the former UI be captured in the spec? → A: Add an explicit legacy parity inventory that lists every old UI capability/control and maps it to Analysis or Review.
- Q: When should review-state changes be persisted? → A: Persist review-state changes immediately after each user action that changes session state.
- Q: How should malformed or incompatible result files be handled? → A: Reject them entirely with a clear error state; do not create a partial review session.
- Q: What should happen if a user edits a candidate name to an empty string? → A: Reject the empty value inline and keep the previous value until the user enters a non-empty replacement or cancels.
- Q: What should happen when an inline edit makes a candidate fit another group better? → A: Recompute grouping immediately, move the candidate automatically to the best-matching group, and show a clear UI notice.
