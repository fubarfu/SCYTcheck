# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`

**Tests**: Included because the spec has explicit independent-test criteria and constitution requires tests for business logic.

**Organization**: Tasks are grouped by user story for independent implementation and validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare environment, tooling, and release-script baseline.

- [ ] T001 Update dependency pins and runtime notes in `requirements.txt`
- [ ] T002 Update project metadata and test tool config in `pyproject.toml`
- [ ] T003 [P] Add Windows release build scaffold in `scripts/release/build.ps1`
- [ ] T004 [P] Add Windows signing scaffold in `scripts/release/sign.ps1`
- [ ] T005 Run current baseline unit suite in `tests/unit/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build shared domain rules and services needed by all stories.

**⚠️ CRITICAL**: User-story implementation starts only after this phase.

- [ ] T006 Extend entities for `ContextPattern`, `TextDetection`, `AppearanceEvent`, and `PlayerSummary` in `src/data/models.py`
- [ ] T007 [P] Add settings persistence for `scytcheck_settings.json` in `src/config.py`
- [ ] T008 [P] Add URL format + preflight accessibility validation helper in `src/services/video_service.py`
- [ ] T009 Add normalization utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [ ] T010 Add event-merging utility with configurable threshold defaulting to 1.0s in `src/services/analysis_service.py`
- [ ] T011 [P] Add pattern-rule validation and extraction boundaries in `src/services/ocr_service.py`
- [ ] T012 Add fixed CSV schema mapping (`PlayerName`, `NormalizedName`, `OccurrenceCount`, `FirstSeenSec`, `LastSeenSec`, `RepresentativeRegion`) in `src/services/export_service.py`
- [ ] T013 [P] Add URL validation unit tests in `tests/unit/test_video_service.py`
- [ ] T014 [P] Add normalization/event-merging unit tests in `tests/unit/test_analysis_service.py`

**Checkpoint**: Foundation complete; stories can proceed.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze on-demand video frames, extract player names using context rules, deduplicate by normalized name, and export fixed-schema summary CSV.

**Independent Test**:
1. Valid URL + preflight check + confirmed regions runs analysis and exports fixed-schema CSV.
2. Output has one row per normalized player name with event-based `OccurrenceCount`.
3. Event merging respects configurable threshold (default 1.0s).
4. Region selector supports create/adjust/confirm and time-scroll navigation only.

### Tests for User Story 1

- [ ] T015 [P] [US1] Add unit tests for before/after/both extraction behavior in `tests/unit/test_ocr_service.py`
- [ ] T016 [P] [US1] Add unit tests for dedup summary generation in `tests/unit/test_analysis_service.py`
- [ ] T017 [P] [US1] Add unit tests for fixed export schema columns and order in `tests/unit/test_export_service.py`
- [ ] T018 [P] [US1] Add unit tests for region selector create/adjust/confirm behavior in `tests/unit/test_region_selector.py`
- [ ] T019 [P] [US1] Add unit tests for scrollbar-only navigation constraints in `tests/unit/test_region_selector.py`
- [ ] T020 [US1] Add integration test for end-to-end deduplicated analysis flow in `tests/integration/test_us1_workflow.py`

### Implementation for User Story 1

- [ ] T021 [P] [US1] Implement OCR candidate extraction API with context pattern matching in `src/services/ocr_service.py`
- [ ] T022 [P] [US1] Implement timestamped frame iteration for analysis pipeline in `src/services/video_service.py`
- [ ] T023 [US1] Integrate URL two-stage validation before analysis start in `src/main.py`
- [ ] T024 [US1] Implement region selector create/adjust/confirm interaction flow in `src/components/region_selector.py`
- [ ] T025 [US1] Implement horizontal time scrollbar navigation in seconds in `src/components/region_selector.py`
- [ ] T026 [US1] Enforce scrollbar-only navigation (no frame-step controls) in `src/components/region_selector.py`
- [ ] T027 [US1] Integrate detection collection and dedup aggregation in `src/services/analysis_service.py`
- [ ] T028 [US1] Integrate event-based occurrence computation in `src/services/analysis_service.py`
- [ ] T029 [US1] Export fixed-schema deduplicated `PlayerSummary` rows in `src/services/export_service.py`
- [ ] T030 [US1] Preserve no-text behavior (header-only CSV + user message) in `src/services/export_service.py`
- [ ] T031 [US1] Wire updated analysis and export flow into controller in `src/main.py`
- [ ] T032 [US1] Update progress stages for detect/aggregate/export in `src/components/progress_display.py`

**Checkpoint**: US1 is fully functional and testable independently.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Keep the main workflow simple while exposing advanced settings for context patterns, filtering, and threshold persistence.

**Independent Test**:
1. User can enter URL, select output folder only, and run analysis with auto-generated filename.
2. Advanced Settings supports multiple patterns and global filter toggle.
3. Advanced settings persist across app restarts via `scytcheck_settings.json`.

### Tests for User Story 2

- [ ] T033 [P] [US2] Add unit tests for folder-only selection and validation messages in `tests/unit/test_file_selector.py`
- [ ] T034 [P] [US2] Add unit tests for advanced settings persistence/load defaults in `tests/unit/test_main_window.py`
- [ ] T035 [US2] Add integration test for advanced settings workflow and persistence in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [ ] T036 [P] [US2] Add Advanced Settings section for context-pattern management in `src/components/main_window.py`
- [ ] T037 [P] [US2] Add global pattern-only toggle and threshold controls in `src/components/main_window.py`
- [ ] T038 [US2] Load/save advanced settings defaults and user updates in `src/main.py`
- [ ] T039 [US2] Display auto-generated filename preview in main workflow in `src/components/main_window.py`

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: Polish & Cross-Cutting (Packaging and Release)

**Purpose**: Final validation, packaging, signing, and release readiness.

- [ ] T040 Create PyInstaller onedir configuration in `build-config.spec`
- [ ] T041 [P] Bundle FFmpeg artifacts in release build pipeline `scripts/release/build.ps1`
- [ ] T042 [P] Bundle Tesseract executable and tessdata (eng/deu) in `scripts/release/build.ps1`
- [ ] T043 Configure bundled Tesseract path bootstrap in `src/main.py`
- [ ] T044 Add development certificate creation step in `scripts/release/create-dev-cert.ps1`
- [ ] T045 Add executable signing automation (SHA-256 timestamp) in `scripts/release/sign.ps1`
- [ ] T046 [P] Produce x64 package in `scripts/release/build.ps1`
- [ ] T047 [P] Produce x86 package in `scripts/release/build.ps1`
- [ ] T048 Validate packaged app behavior on clean Windows VM and document in `README.md`
- [ ] T049 Run full regression suite and record outcomes in `tests/integration/`
- [ ] T050 Update distribution and advanced-settings documentation in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1: no dependencies.
- Phase 2: depends on Phase 1 and blocks all stories.
- Phase 3 (US1): depends on Phase 2 completion.
- Phase 4 (US2): depends on Phase 2 completion; can overlap US1 tasks where files do not conflict.
- Phase 5: depends on completion of desired story scope.

### User Story Dependencies

- US1 (P1): no dependency on US2.
- US2 (P2): no dependency on US1 core logic, but shares UI/controller files.

### Within Each Story

- Tests for the story should fail first, then implementation.
- Service/domain logic before UI/controller wiring.
- Integration test after core story implementation.

---

## Task Count by Story

- Setup: 5 tasks (`T001`-`T005`)
- Foundational: 9 tasks (`T006`-`T014`)
- US1 (P1): 18 tasks (`T015`-`T032`)
- US2 (P2): 7 tasks (`T033`-`T039`)
- Polish: 11 tasks (`T040`-`T050`)
- Total: 50 tasks

---

## Parallel Execution Examples

### US1 Parallel Example

- T015, T016, T017, T018, T019 can run in parallel (separate test scopes/files).
- T021 and T022 can run in parallel (`src/services/ocr_service.py` and `src/services/video_service.py`).

### US2 Parallel Example

- T033 and T034 can run in parallel.
- T036 and T037 can run in parallel with coordinated edits in `src/components/main_window.py`.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 (Phase 3) and validate independently.
3. Release internal MVP from unpackaged/dev build if needed.

### Incremental Delivery

1. Add US2 (Phase 4) and validate independently.
2. Complete packaging and release hardening (Phase 5).
3. Final regression and release documentation update.
