# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`

**Tests**: Included because the specification defines independent-test criteria and constitution requires tests for business logic.

**Organization**: Tasks are grouped by user story for independent implementation and validation.

**Note**: This task list was regenerated and checkbox states are intentionally reset to baseline.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare environment, tooling, and release-script baseline.

- [X] T001 Update dependency pins and runtime notes in `requirements.txt`
- [X] T002 Update project metadata and pytest tool config in `pyproject.toml`
- [X] T003 [P] Add Windows release build scaffold in `scripts/release/build.ps1`
- [X] T004 [P] Add Windows signing scaffold in `scripts/release/sign.ps1`
- [X] T005 Run baseline unit suite in `tests/unit/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared domain rules and service contracts required by all stories.

**⚠️ CRITICAL**: User-story work starts only after this phase is complete.

- [X] T006 Extend entities for `ContextPattern`, `TextDetection`, `AppearanceEvent`, and `PlayerSummary` in `src/data/models.py`
- [X] T007 [P] Add advanced settings persistence (`scytcheck_settings.json`) in `src/config.py`
- [X] T008 [P] Implement URL format + preflight accessibility validation helper in `src/services/video_service.py`
- [X] T009 Add normalized-name utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [X] T010 Add appearance-event merge utility with default 1.0s gap in `src/services/analysis_service.py`
- [X] T011 [P] Implement pattern validation + boundary extraction helpers in `src/services/ocr_service.py`
- [X] T012 [P] Add OCR candidate API per contract in `src/services/ocr_service.py`
- [X] T013 Add fixed summary CSV schema mapping in `src/services/export_service.py`
- [X] T014 [P] Add URL validation unit tests in `tests/unit/test_video_service.py`
- [X] T015 [P] Add normalization/event-merging unit tests in `tests/unit/test_analysis_service.py`

**Checkpoint**: Shared foundation complete; stories can proceed.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze on-demand frames, extract candidate player names with context rules, deduplicate by normalized name, and export fixed-schema summary CSV.

**Independent Test**:
1. Valid URL + confirmed regions runs analysis and exports fixed-schema CSV.
2. Output has one row per normalized player name with event-based `OccurrenceCount`.
3. Event merging respects configurable threshold (default 1.0s).
4. Region selector supports create/adjust/confirm + scrollbar-only navigation + fixed-region helper text.

### Tests for User Story 1

- [X] T016 [P] [US1] Add unit tests for before/after/both extraction boundaries in `tests/unit/test_ocr_service.py`
- [X] T017 [P] [US1] Add unit tests for deduplicated summary generation in `tests/unit/test_analysis_service.py`
- [X] T018 [P] [US1] Add unit tests for fixed summary export schema order in `tests/unit/test_export_service.py`
- [X] T019 [P] [US1] Add unit tests for region create/adjust/confirm flow in `tests/unit/test_region_selector.py`
- [X] T020 [P] [US1] Add unit tests for scrollbar-only navigation constraints in `tests/unit/test_region_selector.py`
- [X] T021 [P] [US1] Add unit test for fixed-region helper text visibility in `tests/unit/test_region_selector.py`
- [X] T022 [US1] Add integration test for end-to-end deduplicated analysis workflow in `tests/integration/test_us1_workflow.py`

### Implementation for User Story 1

- [X] T023 [P] [US1] Implement timestamped frame iteration for analysis pipeline in `src/services/video_service.py`
- [X] T024 [US1] Integrate URL two-stage validation before analysis start in `src/main.py`
- [X] T025 [US1] Implement region selector create/adjust/confirm interaction flow in `src/components/region_selector.py`
- [X] T026 [US1] Implement horizontal time scrollbar navigation in seconds in `src/components/region_selector.py`
- [X] T027 [US1] Enforce scrollbar-only navigation (no step controls) in `src/components/region_selector.py`
- [X] T028 [US1] Add fixed-region helper text in region selector UI in `src/components/region_selector.py`
- [X] T029 [US1] Integrate detection collection and dedup aggregation in `src/services/analysis_service.py`
- [X] T030 [US1] Integrate event-based occurrence computation in `src/services/analysis_service.py`
- [X] T031 [US1] Export fixed-schema deduplicated `PlayerSummary` rows in `src/services/export_service.py`
- [X] T032 [US1] Preserve no-text behavior (header-only CSV + user message) in `src/services/export_service.py`
- [X] T033 [US1] Wire updated analysis and export flow into controller in `src/main.py`
- [X] T034 [US1] Update progress stages for detect/aggregate/export in `src/components/progress_display.py`

**Checkpoint**: US1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Keep primary workflow simple (URL + output folder) while exposing advanced settings for context patterns, filtering, and threshold persistence.

**Independent Test**:
1. User enters URL, selects output folder only, and runs analysis with auto-generated filename.
2. Advanced Settings supports multiple patterns and global filter toggle.
3. Advanced settings persist across app restarts via `scytcheck_settings.json`.

### Tests for User Story 2

- [ ] T035 [P] [US2] Add unit tests for folder-only selection and validation messages in `tests/unit/test_file_selector.py`
- [ ] T036 [P] [US2] Add unit tests for advanced settings load/default persistence in `tests/unit/test_main_window.py`
- [ ] T037 [US2] Add integration test for advanced settings workflow persistence in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [ ] T038 [P] [US2] Add Advanced Settings section for context-pattern management in `src/components/main_window.py`
- [ ] T039 [P] [US2] Add global pattern-only toggle and threshold controls in `src/components/main_window.py`
- [ ] T040 [US2] Load/save advanced settings defaults and user updates in `src/main.py`
- [ ] T041 [US2] Display auto-generated filename preview in main workflow in `src/components/main_window.py`

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: Polish & Cross-Cutting (Packaging and Release)

**Purpose**: Validate performance and release readiness across packaging, signing, and documentation.

- [ ] T042 Create PyInstaller onedir configuration in `build-config.spec`
- [ ] T043 [P] Bundle FFmpeg artifacts in release build pipeline `scripts/release/build.ps1`
- [ ] T044 [P] Bundle Tesseract executable and tessdata (eng/deu) in `scripts/release/build.ps1`
- [ ] T045 Configure bundled Tesseract path bootstrap in `src/main.py`
- [ ] T046 Add development certificate creation step in `scripts/release/create-dev-cert.ps1`
- [ ] T047 Add executable signing automation (SHA-256 timestamp) in `scripts/release/sign.ps1`
- [ ] T048 [P] Produce x64 package in `scripts/release/build.ps1`
- [ ] T049 [P] Produce x86 package in `scripts/release/build.ps1`
- [ ] T050 Add 10-minute analysis performance validation script for SC-001 in `tests/integration/test_performance_sc001.py`
- [ ] T051 Validate packaged app behavior on clean Windows VM and document in `README.md`
- [ ] T052 Run full regression suite and record outcomes in `tests/integration/`
- [ ] T053 Update distribution and advanced-settings documentation in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1: No dependencies.
- Phase 2: Depends on Phase 1 and blocks all user stories.
- Phase 3 (US1): Depends on Phase 2 completion.
- Phase 4 (US2): Depends on Phase 2 completion and can overlap US1 where files do not conflict.
- Phase 5: Depends on completion of selected story scope.

### User Story Dependencies

- US1 (P1): No dependency on US2.
- US2 (P2): No dependency on US1 business logic, but shares UI/controller files.

### Within Each Story

- Tests for that story should fail before implementation.
- Service/domain logic before UI/controller wiring.
- Integration tests after core implementation.

---

## Task Count by Story

- Setup: 5 tasks (`T001`-`T005`)
- Foundational: 10 tasks (`T006`-`T015`)
- US1 (P1): 19 tasks (`T016`-`T034`)
- US2 (P2): 7 tasks (`T035`-`T041`)
- Polish: 12 tasks (`T042`-`T053`)
- Total: 53 tasks

---

## Parallel Execution Examples

### US1 Parallel Example

- T016, T017, T018, T019, T020, and T021 can run in parallel (separate test scopes/files).
- T023 and T029 can run in parallel (`src/services/video_service.py` and `src/services/analysis_service.py`).

### US2 Parallel Example

- T035 and T036 can run in parallel.
- T038 and T039 can run in parallel with coordinated edits in `src/components/main_window.py`.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 (Phase 3) and validate independently.
3. Release internal MVP from unpackaged dev build if needed.

### Incremental Delivery

1. Add US2 (Phase 4) and validate independently.
2. Complete release hardening and packaging (Phase 5).
3. Run final regression and update release documentation.
