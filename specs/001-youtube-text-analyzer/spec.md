# Feature Specification: YouTube Text Analyzer

**Feature Branch**: `001-youtube-text-analyzer`  
**Created**: April 11, 2026  
**Status**: Draft  
**Input**: User description: "Create a windows app that allows to specify a youtube video and analyzes the video for text strings that appear roughly at the same place in the video. The app shall output a file with the list of the strings found in the video. The goal is a lean and clean tool that is easy to use." Additional context: "The text appears in the video, the videos will be recordings of video game sessions and the text strings are the names of other players that appear in the party chat, or in player login and connection messages"

## Clarifications

### Session 2026-04-11

- Q: How should the app access the YouTube video for analysis? → A: Download video frames on-demand for real-time analysis without full video download
- **[Clarification Integration - April 11, 2026]**: FR-003 updated to reflect on-demand segment downloading strategy via yt-dlp. This provides real-time responsiveness while maintaining architecture simplicity.
- Q: What is the output file format? → A: CSV
- Q: What constitutes "roughly the same place"? → A: User-defined regions
- Q: How should the app be distributed to minimize setup for users? → A: Portable ZIP with bundled runtime and dependencies
- Q: Which Windows architectures must bundled builds support? → A: Separate x64 and x86 packages
- Q: How should OCR language data be provisioned? → A: Bundle English and German language data
- Q: How should video decoding dependencies be provided? → A: Bundle FFmpeg binaries
- Q: Should distributed bundles be code-signed? → A: Yes, sign bundled executables/packages
- Q: What filename scheme should the app use when creating CSV files in the selected folder? → A: scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv
- Q: How much control should users have over output filenames? → A: Folder-only selection with automatic filename generation
- Q: What should happen if the selected output folder is missing or not writable? → A: Abort export and show a clear error
- Q: What type of scrollbar should be used to navigate video frames for region selection? → A: Time-based horizontal scrollbar in seconds
- Q: Are additional fine-step navigation controls required during region selection? → A: No, scrollbar only
- Q: What should the output CSV contain when no text is detected in the video? → A: CSV file with headers only (no data rows), plus a user-facing message that no text was found
- Q: How should OCR accuracy (SC-002) be measured? → A: No formal measurement; 80% accuracy target is aspirational only
- Q: How should usability success (SC-003) be validated? → A: Aspirational target only; no formal user testing planned
- Q: How should the app handle text appearing in varying positions across frames? → A: Known limitation; display UI tooltip: "Define region where text appears consistently"
- Q: What matching mode should context patterns use against OCR text? → A: Case-insensitive substring match (e.g., "joined" matches "Joined", "JOINED", "PlayerName Joined the party")
- Q: Can a single context pattern rule specify both a before-text and after-text marker? → A: Yes; each pattern optionally defines before-text and/or after-text; when both are set, both must match (compound AND rule)
- Q: How should the app determine what text to extract as the player name when a context pattern matches? → A: Extract all trimmed text before the after-text marker, or after the before-text marker; when both are set, extract trimmed text between them
- Q: Does the context pattern filter toggle apply globally or per region? → A: Global toggle in Advanced Settings applies uniformly to all regions in the session
- Q: Should Advanced Settings (context patterns and filter toggle) persist between app sessions? → A: Persist to a local config file; loaded on startup; default patterns applied only on first launch

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1)

As a user, I want to input a YouTube video URL and have the app analyze the video to extract text strings that appear in user-defined regions across frames, so I can obtain a list of static text overlays or repeated subtitles.

**Why this priority**: This is the core functionality of the app, providing the primary value of extracting text from videos.

**Independent Test**: Can be fully tested by providing a YouTube URL with known text overlays and verifying the output file contains the expected strings.

**Acceptance Scenarios**:

1. **Given** a valid YouTube video URL with text overlays in similar positions, **When** the user inputs the URL and initiates analysis, **Then** the app creates an output file listing the detected text strings.
2. **Given** a YouTube video with no text overlays, **When** the user runs the analysis, **Then** the app creates a CSV file with column headers only (no data rows) and displays a message informing the user that no text was detected.
3. **Given** an invalid YouTube URL, **When** the user attempts to analyze, **Then** the app displays an error message and does not proceed.

---

### User Story 2 - Easy Input and Output Handling (Priority: P2)

As a user, I want a simple interface to enter the YouTube URL and specify the output file location, so the tool is easy to use without complex setup.

**Why this priority**: Enhances usability, making the tool accessible to non-technical users.

**Independent Test**: Can be tested by verifying the UI allows URL input and file path selection, and the app processes them correctly.

**Acceptance Scenarios**:

1. **Given** the app is launched, **When** the user enters a YouTube URL in the input field, **Then** the URL is accepted and stored for analysis.
2. **Given** the user has entered a URL, **When** they select an output folder, **Then** the folder is validated and stored.

---

### Edge Cases

- What happens when the YouTube video is unavailable or private?
- How does the system handle very long videos (e.g., over 1 hour)?
- What if the video has text in varying positions that are not "roughly the same"? → **Known limitation**: Regions are fixed per analysis session. The region selection UI MUST display a tooltip informing users: "Define your region where text appears consistently across the video." Users are responsible for choosing an appropriate fixed region.
- How to handle different video resolutions or frame rates?
- What happens if the network connection drops during streaming?
- What happens if the selected output folder is missing or not writable?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app MUST provide a user interface to input a YouTube video URL.
- **FR-002**: The app MUST validate the input URL as a valid YouTube video URL.
- **FR-003**: The app MUST download and process YouTube video frames on-demand for real-time analysis without requiring users to download the full video.
- **FR-004**: The app MUST analyze video frames to detect text strings appearing in user-defined regions.
- **FR-005**: The app MUST group similar text strings based on user-defined regions and content.
- **FR-006**: The app MUST output a CSV file containing the list of detected text strings with their positions in a user-selected output folder.
- **FR-007**: The app MUST provide feedback on analysis progress and completion.
- **FR-008**: The app MUST handle errors gracefully (e.g., invalid URL, network issues).
- **FR-009**: The app MUST allow users to define regions of interest on the video frame for text detection.
- **FR-010**: The app MUST be distributed as a portable ZIP package that bundles required runtime and OCR/video dependencies so users do not need separate package installations.
- **FR-011**: The release process MUST produce separate portable ZIP bundles for Windows x64 and Windows x86.
- **FR-012**: Bundled packages MUST include OCR language data for English and German so OCR works without first-run downloads.
- **FR-013**: Bundled packages MUST include FFmpeg binaries required for video streaming/decoding so analysis works without external installs.
- **FR-014**: Distributed executables and packages MUST be code-signed to reduce Windows trust warnings and improve user safety.
- **FR-015**: The app MUST create CSV filenames using the pattern `scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv` to ensure unambiguous output naming.
- **FR-016**: The output workflow MUST allow users to select only an output folder; the CSV filename MUST be generated automatically by the app.
- **FR-017**: If the selected output folder does not exist or is not writable, the app MUST abort export and show a clear error message.
- **FR-018**: During region selection, the app MUST provide a horizontal time scrollbar in seconds across the full video duration to let users navigate to a representative frame before drawing regions.
- **FR-019**: Region selection navigation MUST be implemented with the time scrollbar only; no additional frame-step or fixed-time-step controls are required.
- **FR-020**: The region selection UI MUST display a tooltip or helper text informing the user: "Define your region where text appears consistently across the video." to communicate the fixed-region limitation.
- **FR-021**: The app MUST allow users to define multiple context patterns in an Advanced Settings section of the UI; each pattern optionally specifies a before-text string, an after-text string, or both. When both are provided, both must match (compound AND rule) for the name to be extracted.
- **FR-022**: Context pattern matching MUST use case-insensitive substring matching against the full OCR text detected in the region.
- **FR-023**: The Advanced Settings section MUST provide a global toggle "Only extract names matching a context pattern"; when enabled, OCR text from all regions that does not match any defined context pattern MUST be excluded from the output.
- **FR-024**: The app MUST pre-configure two default context patterns on first launch: "joined" (position: after) and "connected" (position: after).
- **FR-025**: The Advanced Settings section MUST be accessible from the main UI as a distinct collapsible or separate settings area, separate from the primary workflow controls.
- **FR-026**: When a context pattern matches, the app MUST extract the player name as follows: if only after-text is set, extract all trimmed OCR text preceding the after-text match; if only before-text is set, extract all trimmed OCR text following the before-text match; if both are set, extract all trimmed text between the before-text match end and the after-text match start.
- **FR-027**: The app MUST persist Advanced Settings (context patterns and filter toggle state) to a local config file on the user's machine. Settings MUST be loaded automatically on startup. Default context patterns ("joined" after, "connected" after) MUST only be applied on first launch when no config file exists.

### Key Entities *(include if feature involves data)*

- **VideoAnalysis**: Represents the analysis session, containing the YouTube URL, list of detected text strings, and metadata like analysis timestamp.
- **TextString**: Represents player names detected in game chat or system messages, with attributes like content, position coordinates, and frequency of appearance.
- **ContextPattern**: Represents a user-defined surrounding-text rule used to identify and extract player names from OCR output. Attributes: `before_text` (string, optional), `after_text` (string, optional), `enabled` (bool). At least one of `before_text` or `after_text` must be set. When both are set, both must match (compound AND). Multiple ContextPatterns can be configured per session.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete video analysis for a 10-minute video in under 5 minutes.
- **SC-002**: *(Aspirational)* The app is expected to achieve at least 80% accuracy in detecting text strings in standard video resolutions. No formal measurement methodology is defined; this target guides implementation quality but is not a hard acceptance gate.
- **SC-003**: *(Aspirational)* 95% of users can successfully input a URL and initiate analysis without assistance. No formal user testing is planned; this target guides UX decisions but is not a hard acceptance gate.
- **SC-004**: The output CSV file is easily readable and contains all detected strings with their positions.

## Assumptions

- The app runs on Windows operating system.
- Users have stable internet access to stream YouTube videos.
- YouTube videos are publicly accessible and not restricted by copyright or region.
- Videos are recordings of video game sessions; text strings are player names appearing in party chat or login/connection messages.
- Videos contain text overlays or subtitles that are detectable by OCR technology.
- Standard video formats (MP4, etc.) are supported.
- The app has permissions to access the internet and write files to the user's chosen location.
- A local config file (e.g., `scytcheck_settings.json`) is written alongside the executable or in a user-writable app data folder to persist Advanced Settings across sessions.
