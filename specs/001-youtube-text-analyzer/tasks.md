# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`  
**Prerequisites**: `plan.md` and `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included. Tests are required by the specification traceability rule (`RTR-001`) and constitution principle III.

**Organization**: Tasks are grouped by user story for independent implementation and validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare build/test baseline and shared scaffolding.

- [X] T001 Update runtime dependencies for current feature scope in `requirements.txt`
- [X] T002 Align lint/test tooling settings in `pyproject.toml`
- [X] T003 [P] Prepare release build script skeleton for packaging flow in `scripts/release/build.ps1`
- [X] T004 [P] Prepare release signing script skeleton in `scripts/release/sign.ps1`
- [X] T005 Add baseline logging service module scaffold in `src/services/logging.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared domain and service capabilities required before any user story work.

**⚠️ CRITICAL**: No user story tasks begin until this phase is complete.

- [X] T006 Extend core entities for `VideoAnalysis`, `LogRecord`, and minimal `PlayerSummary` in `src/data/models.py`
- [X] T007 Persist default settings (`video_quality`, `logging_enabled`, patterns/filter/sensitivity/gap) in `src/config.py`
- [X] T008 [P] Add timestamp formatting helper for `HH:MM:SS.mmm` in `src/services/analysis_service.py`
- [X] T009 Add deterministic output filename helper in `src/services/export_service.py`
- [X] T010 Implement URL format + accessibility preflight validation classification in `src/services/video_service.py`
- [X] T011 Implement retrieval quality plumbing with no automatic downgrade in `src/services/video_service.py`
- [X] T012 Implement transient retrieval retry policy (max 3) in `src/services/video_service.py`
- [X] T013 [P] Implement context-pattern boundary extraction helpers in `src/services/ocr_service.py`
- [X] T014 Implement normalized-name utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [X] T015 Implement appearance-event merge utility with default 1.0s gap in `src/services/analysis_service.py`
- [X] T016 Implement minimal summary CSV serializer (`PlayerName`, `StartTimestamp`) in `src/services/export_service.py`
- [X] T017 Implement sidecar log serializer with fixed expanded schema in `src/services/logging.py`
- [X] T018 [P] Add settings default/persistence unit tests in `tests/unit/test_config.py`
- [X] T019 [P] Add URL validation classification unit tests in `tests/unit/test_video_service.py`
- [X] T020 [P] Add timestamp-format helper unit tests in `tests/unit/test_analysis_service.py`

**Checkpoint**: Foundation is complete and user stories can proceed.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze valid YouTube input in user-confirmed regions and export deduplicated minimal summary output with robust detection/aggregation behavior.

**Independent Test**: Run analysis from URL to export and verify summary CSV headers are exactly `PlayerName,StartTimestamp`, rows are deduplicated by normalized name, and no-text/invalid-URL cases behave as specified.

### Tests for User Story 1

- [X] T021 [P] [US1] Add integration test for valid URL analysis to summary CSV in `tests/integration/test_us1_workflow.py`
- [X] T022 [P] [US1] Add integration test for no-text header-only summary output in `tests/integration/test_us1_workflow.py`
- [X] T023 [P] [US1] Add integration test for invalid URL rejection before analysis in `tests/integration/test_us1_workflow.py`
- [X] T024 [P] [US1] Add unit tests for before/after/both extraction boundaries in `tests/unit/test_ocr_service.py`
- [X] T025 [P] [US1] Add unit tests for deterministic multi-pattern conflict resolution in `tests/unit/test_ocr_service.py`
- [X] T026 [P] [US1] Add unit tests for recall-first context-matched candidate preservation in `tests/unit/test_ocr_service.py`
- [X] T027 [P] [US1] Add unit tests for normalization and dedup key generation in `tests/unit/test_analysis_service.py`
- [X] T028 [P] [US1] Add unit tests for event-gap merging at default 1.0s in `tests/unit/test_analysis_service.py`
- [X] T029 [P] [US1] Add unit tests for minimal summary schema + timestamp format in `tests/unit/test_export_service.py`
- [X] T030 [P] [US1] Add unit tests for export-retry without re-analysis in `tests/unit/test_main.py`

### Implementation for User Story 1

- [X] T031 [US1] Integrate OCR candidate collection pipeline in `src/services/analysis_service.py`
- [X] T032 [US1] Apply global filter toggle semantics for matching/non-matching lines in `src/services/analysis_service.py`
- [X] T033 [US1] Implement deterministic pattern tie-break logic in `src/services/ocr_service.py`
- [X] T034 [US1] Compute merged appearance events and earliest start timestamp by normalized name in `src/services/analysis_service.py`
- [X] T035 [US1] Build minimal player summary rows for export in `src/services/analysis_service.py`
- [X] T036 [US1] Export summary CSV with exact headers `PlayerName,StartTimestamp` in `src/services/export_service.py`
- [X] T037 [US1] Preserve header-only output + user message when no names detected in `src/services/export_service.py`
- [X] T038 [US1] Write sidecar log rows (when enabled) with expanded schema in `src/services/logging.py`
- [X] T039 [US1] Preserve in-memory results and support export retry in `src/main.py`
- [X] T040 [US1] Enforce analysis abort when no region is confirmed in `src/main.py`
- [X] T041 [US1] Integrate two-stage URL validation + error classification in `src/main.py`
- [X] T042 [US1] Implement frame iteration with timestamps, quality selection, and retry behavior in `src/services/video_service.py`
- [X] T043 [US1] Update progress phases for retrieval/detection/aggregation/export in `src/components/progress_display.py`

**Checkpoint**: US1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Provide simple primary workflow and advanced settings UX with persistence, keyboard accessibility, region-selection usability constraints, and optional logging controls.

**Independent Test**: Complete end-to-end flow using only URL + output folder with optional advanced settings adjustments; verify persistence across restart and keyboard-only operability.

### Tests for User Story 2

- [X] T044 [P] [US2] Add unit tests for URL input and output-folder workflow in `tests/unit/test_main_window.py`
- [X] T045 [P] [US2] Add unit tests for auto-generated filename pattern display in `tests/unit/test_main_window.py`
- [X] T046 [P] [US2] Add unit tests for advanced-settings persistence across sessions in `tests/unit/test_main_window.py`
- [X] T047 [P] [US2] Add unit tests for default-enabled pattern filter and default-disabled logging toggle in `tests/unit/test_main_window.py`
- [X] T048 [P] [US2] Add unit tests for video-quality selector default best and no auto-downgrade UI state in `tests/unit/test_main_window.py`
- [X] T049 [P] [US2] Add unit tests for OCR sensitivity controls and low-quality warning text in `tests/unit/test_main_window.py`
- [X] T050 [P] [US2] Add unit tests for keyboard-only operation of core controls in `tests/unit/test_main_window.py`
- [X] T051 [P] [US2] Add unit tests for region selector scrollbar-only navigation in `tests/unit/test_region_selector.py`
- [X] T052 [P] [US2] Add unit tests for region selector foreground + instruction placement below video in `tests/unit/test_region_selector.py`
- [X] T053 [P] [US2] Add unit tests for no-warning behavior when logging is disabled in `tests/unit/test_main.py`
- [X] T054 [US2] Add integration test for advanced-settings persistence workflow in `tests/integration/test_us2_settings_workflow.py`
- [X] T055 [US2] Add integration test for keyboard-only main workflow execution in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [X] T056 [US2] Add video-quality selector control (default best) in `src/components/main_window.py`
- [X] T057 [US2] Add logging toggle control (default off) in `src/components/main_window.py`
- [X] T058 [US2] Add OCR sensitivity controls and low-quality reliability notice in `src/components/main_window.py`
- [X] T059 [US2] Implement pattern management UI for before/after rules in `src/components/main_window.py`
- [X] T060 [US2] Implement keyboard shortcuts/focus order across workflow controls in `src/components/main_window.py`
- [X] T061 [US2] Enforce non-overlapping label/control layout constraints in `src/components/main_window.py`
- [X] T062 [US2] Implement region selector foreground behavior and below-video instruction area in `src/components/region_selector.py`
- [X] T063 [US2] Implement scrollbar-only navigation and remove step controls in `src/components/region_selector.py`
- [X] T064 [US2] Integrate output-folder validation error messaging (reason/path/next step) in `src/components/file_selector.py`
- [X] T065 [US2] Wire settings load/save lifecycle and defaults in `src/main.py`

**Checkpoint**: US1 and US2 are independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Packaging, release readiness, and success-criteria validation.

- [X] T066 Create PyInstaller onedir configuration for release bundles in `build-config.spec`
- [X] T067 [P] Bundle FFmpeg binaries in release pipeline in `scripts/release/build.ps1`
- [X] T068 [P] Bundle Tesseract binaries and eng/deu tessdata in `scripts/release/build.ps1`
- [X] T069 [P] Generate x64 portable ZIP package in `scripts/release/build.ps1`
- [X] T070 [P] Generate x86 portable ZIP package in `scripts/release/build.ps1`
- [X] T071 Implement executable/package signing automation in `scripts/release/sign.ps1`
- [X] T072 Add SC-001 performance validation test (10-minute target) in `tests/integration/test_performance_sc001.py`
- [X] T073 Add SC-004/SC-005 output schema validation test in `tests/integration/test_output_schema_sc004_sc005.py`
- [X] T074 Add log schema validation test for FR-049 in `tests/integration/test_log_schema_fr049.py`
- [X] T075 Validate quickstart scenario and update usage details in `specs/001-youtube-text-analyzer/quickstart.md`
- [X] T076 Update end-user documentation for summary-vs-log outputs in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion; blocks user stories.
- **Phase 3 (US1)**: Depends on Phase 2 completion.
- **Phase 4 (US2)**: Depends on Phase 2 completion; can proceed in parallel with US1 where files do not conflict.
- **Phase 5 (Polish)**: Depends on completion of desired user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after foundational completion.
- **US2 (P2)**: Independent after foundational completion; integrates shared UI/services without requiring US1 delivery.

### Within Each User Story

- Test tasks are created first and should fail before implementation.
- Service/domain tasks precede controller/UI wiring.
- Integration tests validate end-to-end behavior after core implementation.

---

## Parallel Execution Examples

### User Story 1

Run tests in parallel:
- T021, T022, T023, T024, T025, T026, T027, T028, T029, T030

Run implementation in parallel where possible:
- T033 (`src/services/ocr_service.py`) and T042 (`src/services/video_service.py`)
- T036 (`src/services/export_service.py`) and T038 (`src/services/logging.py`)

### User Story 2

Run tests in parallel:
- T044, T045, T046, T047, T048, T049, T050, T051, T052, T053

Run implementation in parallel where possible:
- T062 (`src/components/region_selector.py`) and T064 (`src/components/file_selector.py`)
- T056, T057, T058, T059 can be coordinated in `src/components/main_window.py`

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently via integration and schema tests.

### Incremental Delivery

1. Deliver US1 as MVP.
2. Deliver US2 usability/settings enhancements.
3. Complete Phase 5 packaging, signing, and success-criteria validation.

### Traceability Coverage Note

- FR coverage is addressed by unit/integration tasks in Phases 2-5, including URL validation, on-demand retrieval, region UX, settings persistence, minimal summary export, optional logging schema, and packaging/signing.
- SC coverage is addressed by T072 (SC-001), T073 (SC-004/SC-005), and supporting integration tests for workflow completion.
