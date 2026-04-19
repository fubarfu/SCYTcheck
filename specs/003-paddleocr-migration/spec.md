# Feature Specification: PaddleOCR Migration

**Feature Branch**: `003-paddleocr-migration`  
**Created**: 2026-04-14  
**Status**: Draft  
**Input**: User description: "We use PaddleOCR instead of tesseract as OCR engine. All functionality remains inplace, specifically the portable packaging has to be considered"

## Clarifications

### Session 2026-04-14

- Q: How should the portable package provide PaddleOCR models and runtime assets? → A: Bundle all required PaddleOCR runtime files and models inside the portable ZIP so the app works fully offline after extraction.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Better Name Extraction Accuracy (Priority: P1)

A user analyzes Star Citizen or other supported gameplay recordings and gets more correct player names from the same selected regions than with the current release, without needing to change their normal workflow.

**Why this priority**: Accuracy is the entire reason for changing the OCR engine. If recognition quality does not improve on real gameplay footage, the feature has no value.

**Independent Test**: Can be fully tested by running the same reference recordings through the current release and the new release, then comparing missed names and false positives in the exported summary and detailed log outputs.

**Acceptance Scenarios**:

1. **Given** a reference gameplay recording that contains player names in the selected UI region, **When** the user runs analysis with the replacement OCR engine, **Then** the exported results contain more correctly recognized player names than the current release on the same recording.
2. **Given** a recording with visually noisy or compressed UI text, **When** the user runs analysis, **Then** the replacement OCR engine recognizes names that the current release misses while avoiding an increase in obvious false positives.

---

### User Story 2 - No Workflow Regression For Existing Users (Priority: P2)

A user upgrades to the new release and continues using the same URL entry, region selection, advanced settings, progress display, and CSV export workflow without learning a new process.

**Why this priority**: The application is intentionally lean and simple. Engine replacement must not force users to relearn the product or lose existing functionality.

**Independent Test**: Can be tested by executing the normal end-to-end workflow from URL input through export and verifying that user-visible steps, settings persistence, and output files remain available and behave consistently.

**Acceptance Scenarios**:

1. **Given** an existing user familiar with the current app, **When** they upgrade and run analysis, **Then** they can complete the same end-to-end workflow without any new mandatory setup steps.
2. **Given** an analysis session with logging enabled, **When** analysis completes, **Then** the app still produces the same output file types and schemas expected by existing users.
3. **Given** saved application settings from a prior release, **When** the new release starts, **Then** settings that are still relevant remain usable and the app handles obsolete OCR-engine-specific settings without breaking the session.

---

### User Story 3 - Portable Package Remains Self-Contained (Priority: P2)

A user downloads the Windows portable ZIP and can run the app on a supported machine without separately installing OCR software, model files, or command-line dependencies.

**Why this priority**: The current product promise is a portable Windows package with minimal setup. Replacing the OCR engine is not acceptable if it shifts installation burden onto users.

**Independent Test**: Can be tested by extracting the release ZIP onto a clean Windows machine and verifying that the application starts, analyzes a supported recording, and exports results without requiring external OCR installation.

The portable ZIP is expected to ship with all required PaddleOCR runtime files and model assets already included so first-run analysis works fully offline after extraction.

**Acceptance Scenarios**:

1. **Given** a clean supported Windows machine, **When** the user extracts the portable ZIP and launches the application, **Then** OCR-based analysis works without installing additional OCR runtimes or downloading extra assets manually.
2. **Given** the packaged application is launched from the extracted folder, **When** the user analyzes a recording, **Then** all OCR functionality required for the feature is available from the bundled release contents.

---

### Edge Cases

- What happens when the replacement OCR engine cannot initialize on startup or in the packaged build?
- How does the system handle recordings where the replacement OCR engine produces no text for a region that previously yielded low-confidence text?
- What happens when older saved settings reference tuning options that no longer apply to the replacement OCR engine?
- How does the packaged app behave when bundled OCR assets are missing, corrupted, or blocked by security software?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST replace the current OCR engine used for text recognition during video analysis with the approved replacement engine for this feature.
- **FR-002**: System MUST preserve the existing end-to-end user workflow for URL entry, region selection, analysis, progress reporting, and export.
- **FR-003**: System MUST continue to produce the existing summary export and optional detailed log export so existing consumers of those files do not need to change workflows.
- **FR-004**: System MUST improve recognition outcomes on the project’s reference gameplay recordings compared with the current release baseline.
- **FR-005**: System MUST allow analysis from the portable Windows package without requiring any separate OCR installation or manual setup by end users.
- **FR-006**: System MUST bundle all required PaddleOCR runtime and model assets inside the release package so first-run analysis works fully offline after extraction.
- **FR-007**: System MUST detect and report OCR-engine initialization failures with a clear user-facing message instead of failing silently or crashing.
- **FR-008**: System MUST preserve existing settings and migrate or ignore obsolete OCR-engine-specific settings safely so upgrades do not block analysis.
- **FR-009**: System MUST preserve existing behavior for region-based analysis, including support for the same selected regions and downstream matching logic.
- **FR-010**: System MUST keep analysis entirely usable without any paid service, usage-based billing, or account-based OCR dependency for development or end users.
- **FR-011**: System MUST provide maintainers with a repeatable way to validate recognition quality against the current release baseline before publishing a release.

### Key Entities *(include if feature involves data)*

- **OCR Engine Configuration**: The set of persisted application settings and packaged assets required to initialize and run the replacement OCR engine within normal analysis flows.
- **Reference Validation Set**: The curated recordings, crops, or expected outputs used to compare recognition quality between the current release and the replacement engine.
- **Portable Release Bundle**: The Windows ZIP distribution that contains the executable and every dependency required for offline analysis.
- **Bundled OCR Assets**: The PaddleOCR runtime files and model files that are shipped inside the portable ZIP and loaded locally by the packaged application.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the maintained reference validation set, the new release reduces the combined count of missed player-name detections and false-positive detections by at least 20% compared with the current release.
- **SC-002**: At least 90% of reference recordings that are successfully processed by the current release are also processed successfully by the new release with no workflow-breaking errors.
- **SC-003**: A first-time user can download, extract, launch, and complete a successful analysis from the portable ZIP on a supported Windows machine without any separate OCR installation steps.
- **SC-004**: Existing summary CSV and optional detailed log outputs remain consumable by the project’s current validation checks with no schema regressions.
- **SC-005**: During first-run OCR analysis from the extracted portable ZIP, the application performs no model downloads and requires no network-dependent OCR setup.

## Assumptions

- The application remains Windows-first and continues to be distributed primarily as a portable ZIP.
- Existing region selection, matching, export, and settings concepts remain in scope and should not be redesigned as part of this feature.
- The project team will maintain a representative reference set of gameplay recordings or frame crops to judge whether recognition quality has actually improved.
- Any OCR-engine-specific tuning surface that no longer makes sense may be simplified, as long as upgrades remain safe and the user workflow stays intact.
- Paid OCR APIs and cloud-hosted OCR services are out of scope for this feature.
