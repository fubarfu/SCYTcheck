# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`

**Tests**: Included because the specification defines independent test criteria and this project enforces testing for business logic.

**Organization**: Tasks are grouped by user story so each story is independently implementable and testable.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align project baseline, tooling, and release scaffolding.

- [ ] T001 Update dependency pins and extras in `requirements.txt`
- [ ] T002 Update project metadata and tool config in `pyproject.toml`
- [ ] T003 [P] Add release script scaffold for Windows packaging in `scripts/release/build.ps1`
- [ ] T004 [P] Add signing script scaffold in `scripts/release/sign.ps1`
- [ ] T005 Validate baseline with current unit tests in `tests/unit/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models, settings persistence, and service contracts required by all stories.

**⚠️ CRITICAL**: No user story work should start before this phase is complete.

- [ ] T006 Extend domain models for `ContextPattern`, `TextDetection`, `AppearanceEvent`, and `PlayerSummary` in `src/data/models.py`
- [ ] T007 [P] Implement settings load/save for `scytcheck_settings.json` in `src/config.py`
- [ ] T008 [P] Add validation helpers for context-pattern rules in `src/services/analysis_service.py`
- [ ] T009 Implement name normalization utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [ ] T010 Implement event-merging utility with configurable gap threshold (default 1.0s) in `src/services/analysis_service.py`
- [ ] T011 [P] Add OCR extraction helpers for before/after/both pattern modes in `src/services/ocr_service.py`
- [ ] T012 Add CSV row schema support for deduplicated summaries in `src/services/export_service.py`

**Checkpoint**: Foundation complete; user stories can proceed.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze YouTube video frames in selected regions, extract player names via context patterns, and export deduplicated per-player results.

**Independent Test**:
1. Valid URL + selected region produces CSV output with one row per normalized player name.
2. Repeated frame detections for the same player do not create duplicate rows.
3. Occurrence counts represent merged appearance events using default 1.0s detection-gap threshold.
4. Pattern matching and extraction (before/after/both) behaves as specified.

### Tests for User Story 1

- [ ] T013 [P] [US1] Add unit tests for pattern matching and extraction boundaries in `tests/unit/test_ocr_service.py`
- [ ] T014 [P] [US1] Add unit tests for normalization and dedup key behavior in `tests/unit/test_analysis_service.py`
- [ ] T015 [P] [US1] Add unit tests for event merging with gap-threshold behavior in `tests/unit/test_analysis_service.py`
- [ ] T016 [P] [US1] Add unit tests for deduplicated CSV summary rows in `tests/unit/test_export_service.py`
- [ ] T017 [US1] Add integration test for end-to-end deduplicated analysis flow in `tests/integration/test_us1_workflow.py`

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement OCR candidate extraction API for context patterns in `src/services/ocr_service.py`
- [ ] T019 [P] [US1] Implement timestamped frame iteration support in `src/services/video_service.py`
- [ ] T020 [US1] Update analysis pipeline to collect `TextDetection` records in `src/services/analysis_service.py`
- [ ] T021 [US1] Integrate pattern-only filtering toggle in analysis flow in `src/services/analysis_service.py`
- [ ] T022 [US1] Integrate normalization and whole-video dedup aggregation in `src/services/analysis_service.py`
- [ ] T023 [US1] Integrate appearance event computation with default threshold in `src/services/analysis_service.py`
- [ ] T024 [US1] Update export pipeline to write `PlayerSummary` CSV rows in `src/services/export_service.py`
- [ ] T025 [US1] Wire updated analysis/export behavior into application controller in `src/main.py`
- [ ] T026 [US1] Surface analysis progress for detection and aggregation stages in `src/components/progress_display.py`
- [ ] T027 [US1] Ensure region-selection tooltip for fixed-region limitation remains visible in `src/components/region_selector.py`
- [ ] T028 [US1] Verify no-text-found behavior writes header-only CSV and user message in `src/services/export_service.py`

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Keep the workflow simple while exposing advanced settings for context patterns and filtering.

**Independent Test**:
1. User can enter URL, select output folder, and start analysis without manual filename entry.
2. Advanced Settings allows managing multiple context patterns and global filter toggle.
3. Settings persist across app restarts via `scytcheck_settings.json`.

### Tests for User Story 2

- [ ] T029 [P] [US2] Add unit tests for folder-only selection and validation messaging in `tests/unit/test_file_selector.py`
- [ ] T030 [P] [US2] Add unit tests for advanced settings persistence in `tests/unit/test_main_window.py`
- [ ] T031 [US2] Add integration test for advanced settings workflow and persistence in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [ ] T032 [P] [US2] Add Advanced Settings UI section for context-pattern management in `src/components/main_window.py`
- [ ] T033 [P] [US2] Add controls for global pattern-only toggle and event-gap threshold in `src/components/main_window.py`
- [ ] T034 [US2] Load/save advanced settings defaults and user changes in `src/main.py`

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: Polish & Cross-Cutting (Packaging and Release)

**Purpose**: Final validation, packaging, signing, and release readiness across stories.

- [ ] T035 Create PyInstaller configuration for onedir build in `build-config.spec`
- [ ] T036 [P] Bundle FFmpeg artifacts during build in `scripts/release/build.ps1`
- [ ] T037 [P] Bundle Tesseract executable and tessdata (eng/deu) during build in `scripts/release/build.ps1`
- [ ] T038 Configure bundled Tesseract path bootstrap in `src/main.py`
- [ ] T039 Add development certificate creation script in `scripts/release/create-dev-cert.ps1`
- [ ] T040 Add executable signing automation with SHA-256 timestamp in `scripts/release/sign.ps1`
- [ ] T041 [P] Build x64 release package in `scripts/release/build.ps1`
- [ ] T042 [P] Build x86 release package in `scripts/release/build.ps1`
- [ ] T043 Validate packaged app behavior on clean Windows VM and capture notes in `README.md`
- [ ] T044 Run full regression tests and record results in `tests/integration/`
- [ ] T045 Update distribution and advanced-settings documentation in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): No dependencies.
- Phase 2 (Foundational): Depends on Phase 1; blocks all user stories.
- Phase 3 (US1): Depends on Phase 2 completion.
- Phase 4 (US2): Depends on Phase 2 completion; can run in parallel with late US1 work where files do not overlap.
- Phase 5 (Polish): Depends on completion of the selected user stories.

### User Story Dependencies

- US1 (P1): No dependency on US2.
- US2 (P2): No dependency on US1 core logic, but shares UI/controller files.

### Within Each User Story

- Tests first for new business rules (expected to fail initially).
- Service/model logic before UI/controller integration.
- Integration tests after core implementation.

---

## Parallel Execution Examples

### US1 Parallel Example

- T013, T014, T015, T016 can run in parallel (different test files/sections).
- T018 and T019 can run in parallel (`src/services/ocr_service.py` and `src/services/video_service.py`).

### US2 Parallel Example

- T029 and T030 can run in parallel.
- T032 and T033 can run in parallel in different UI sections within `src/components/main_window.py` if coordinated by feature flags/branches.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Deliver Phase 3 (US1) and validate independently.
3. Ship dev/internal MVP if needed.

### Incremental Delivery

1. Add Phase 4 (US2 advanced settings UX + persistence).
2. Re-validate US1 and US2 independently.
3. Complete Phase 5 for production packaging and distribution.
