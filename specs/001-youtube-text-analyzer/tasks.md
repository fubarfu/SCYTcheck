# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`
**Prerequisites**: `plan.md` and `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included. Tests are required by the specification traceability rule (`RTR-001`) and constitution principle III.

**Organization**: Tasks are grouped by user story for independent implementation and validation.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare baseline dependencies, tooling, and release scaffolding.

- [X] T001 Update runtime dependencies for feature scope in `requirements.txt`
- [X] T002 Align lint/test tooling settings in `pyproject.toml`
- [X] T003 [P] Prepare release build script baseline in `scripts/release/build.ps1`
- [X] T004 [P] Prepare optional signing script baseline in `scripts/release/sign.ps1`
- [X] T005 Add baseline logging service scaffold in `src/services/logging.py`
- [X] T006 Add task traceability notes for FR/SC mapping in `specs/001-youtube-text-analyzer/tasks.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared domain and service capabilities required before any user story work.

**⚠️ CRITICAL**: No user story tasks begin until this phase is complete.

- [X] T007 Extend entities for `VideoAnalysis`, `TextDetection`, `LogRecord`, and `PlayerSummary` in `src/data/models.py`
- [X] T008 Persist defaults (video quality, logging, patterns, filter, sensitivity, gap) in `src/config.py`
- [X] T009 [P] Add timestamp helper for `HH:MM:SS.mmm` in `src/services/analysis_service.py`
- [X] T010 Add deterministic output filename helper (`scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv`) in `src/services/export_service.py`
- [X] T011 Implement URL format + accessibility preflight validation classification in `src/services/video_service.py`
- [X] T012 Implement quality selection plumbing with no auto-downgrade in `src/services/video_service.py`
- [X] T013 Implement transient retrieval retry policy (max 3 attempts) in `src/services/video_service.py`
- [X] T014 [P] Implement OCR normalization helper (line-break removal + whitespace collapse) in `src/services/ocr_service.py`
- [X] T015 [P] Implement fuzzy context matching helper with configurable threshold default `0.75` in `src/services/ocr_service.py`
- [X] T016 [P] Implement boundary-clipped context acceptance helper in `src/services/ocr_service.py`
- [X] T017 Implement normalized-name utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [X] T018 Implement appearance-event merge utility with default 1.0s gap in `src/services/analysis_service.py`
- [X] T019 Implement minimal summary CSV serializer (`PlayerName`, `StartTimestamp`) in `src/services/export_service.py`
- [X] T020 Implement sidecar log serializer with fixed schema in `src/services/logging.py`
- [X] T021 [P] Add foundational settings persistence unit tests in `tests/unit/test_config.py`
- [X] T022 [P] Add foundational video validation/retry unit tests in `tests/unit/test_video_service.py`

**Checkpoint**: Foundational services and shared rules are complete; user stories can proceed independently.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze a valid YouTube input using confirmed regions and export deduplicated summary output with robust OCR matching and aggregation behavior.

**Independent Test**: Execute URL-to-export flow and verify summary CSV header is exactly `PlayerName,StartTimestamp`, names are deduplicated by normalized key, and invalid/no-text cases match spec behavior.

### Tests for User Story 1

- [X] T023 [P] [US1] Add integration test for valid URL analysis to summary CSV in `tests/integration/test_us1_workflow.py`
- [X] T024 [P] [US1] Add integration test for no-text header-only summary output in `tests/integration/test_us1_workflow.py`
- [X] T025 [P] [US1] Add integration test for invalid URL rejection before analysis in `tests/integration/test_us1_workflow.py`
- [X] T026 [P] [US1] Add unit tests for OCR normalization (line-break removal + whitespace collapse) in `tests/unit/test_ocr_service.py`
- [X] T027 [P] [US1] Add unit tests for fuzzy threshold matching behavior in `tests/unit/test_ocr_service.py`
- [X] T028 [P] [US1] Add unit tests for boundary-clipped context matching acceptance in `tests/unit/test_ocr_service.py`
- [X] T029 [P] [US1] Add unit tests for before/after/both extraction boundaries in `tests/unit/test_ocr_service.py`
- [X] T030 [P] [US1] Add unit tests for deterministic multi-pattern conflict resolution in `tests/unit/test_ocr_service.py`
- [X] T031 [P] [US1] Add unit tests for recall-first context-matched candidate preservation in `tests/unit/test_ocr_service.py`
- [X] T032 [P] [US1] Add unit tests for normalization and dedup key generation in `tests/unit/test_analysis_service.py`
- [X] T033 [P] [US1] Add unit tests for event-gap merging at default 1.0s in `tests/unit/test_analysis_service.py`
- [X] T034 [P] [US1] Add unit tests for summary CSV schema + timestamp format in `tests/unit/test_export_service.py`

### Implementation for User Story 1

- [X] T035 [US1] Integrate OCR candidate collection pipeline in `src/services/analysis_service.py`
- [X] T036 [US1] Apply global filter toggle semantics for matching/non-matching lines in `src/services/analysis_service.py`
- [X] T037 [US1] Implement deterministic pattern tie-break logic in `src/services/ocr_service.py`
- [X] T038 [US1] Enforce fuzzy normalized matching with default threshold handling in `src/services/ocr_service.py`
- [X] T039 [US1] Enforce boundary-clipped context acceptance in matching flow in `src/services/ocr_service.py`
- [X] T040 [US1] Compute merged appearance events and earliest start timestamp by normalized name in `src/services/analysis_service.py`
- [X] T041 [US1] Build minimal player summary rows for export in `src/services/analysis_service.py`
- [X] T042 [US1] Export summary CSV with exact headers `PlayerName,StartTimestamp` in `src/services/export_service.py`
- [X] T043 [US1] Preserve header-only output + user message when no names are detected in `src/services/export_service.py`
- [X] T044 [US1] Write sidecar log rows (when enabled) with fixed schema in `src/services/logging.py`
- [X] T045 [US1] Preserve in-memory results and support export retry in `src/main.py`
- [X] T046 [US1] Enforce analysis abort when no region is confirmed in `src/main.py`
- [X] T047 [US1] Integrate two-stage URL validation + error classification in `src/main.py`
- [X] T048 [US1] Implement frame iteration with timestamps, quality selection, and retry behavior in `src/services/video_service.py`

**Checkpoint**: US1 is fully functional and independently testable.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Provide a simple workflow for URL + output folder with robust advanced settings, region selector usability, persistence, and keyboard operability.

**Independent Test**: Complete the end-to-end workflow using keyboard-only controls, persisted settings, and region selection UX constraints, then confirm output and logging behavior.

### Tests for User Story 2

- [X] T049 [P] [US2] Add unit tests for URL input and output-folder workflow in `tests/unit/test_main_window.py`
- [X] T050 [P] [US2] Add unit tests for auto-generated filename pattern display in `tests/unit/test_main_window.py`
- [X] T051 [P] [US2] Add unit tests for advanced-settings persistence across sessions in `tests/unit/test_main_window.py`
- [X] T052 [P] [US2] Add unit tests for default-enabled pattern filter and default-disabled logging toggle in `tests/unit/test_main_window.py`
- [X] T053 [P] [US2] Add unit tests for video-quality selector default best and no auto-downgrade state in `tests/unit/test_main_window.py`
- [X] T054 [P] [US2] Add unit tests for OCR sensitivity controls and low-quality reliability notice in `tests/unit/test_main_window.py`
- [X] T055 [P] [US2] Add unit tests for keyboard-only operation of core controls in `tests/unit/test_main_window.py`
- [X] T056 [P] [US2] Add unit tests for region selector scrollbar-only navigation in `tests/unit/test_region_selector.py`
- [X] T057 [P] [US2] Add unit tests for region selector foreground + below-video instruction placement in `tests/unit/test_region_selector.py`
- [X] T058 [P] [US2] Add unit tests for FR-037 measurable legibility constraints (minimum font size 14 px, minimum contrast ratio 4.5:1, no overlap with active selection rectangles/required controls) in `tests/unit/test_region_selector.py`
- [X] T059 [US2] Add integration test for settings persistence + keyboard workflow in `tests/integration/test_us2_settings_workflow.py`
- [X] T060 [P] [US2] Add unit test for FR-052 no-warning/no-confirmation/no-info prompt behavior when logging is disabled in `tests/unit/test_main.py`

### Implementation for User Story 2

- [X] T061 [US2] Add video-quality selector control (default best) in `src/components/main_window.py`
- [X] T062 [US2] Add logging toggle control (default off) in `src/components/main_window.py`
- [X] T063 [US2] Add OCR sensitivity controls and low-quality reliability notice in `src/components/main_window.py`
- [X] T064 [US2] Implement context-pattern management UI for before/after rules in `src/components/main_window.py`
- [X] T065 [US2] Implement keyboard shortcuts and focus order across workflow controls in `src/components/main_window.py`
- [X] T066 [US2] Enforce non-overlapping label/control layout constraints in `src/components/main_window.py`
- [X] T067 [US2] Implement region selector foreground behavior and dedicated below-video instruction area in `src/components/region_selector.py`
- [X] T068 [US2] Implement scrollbar-only navigation and remove step controls in `src/components/region_selector.py`
- [X] T069 [US2] Implement FR-037 legibility enforcement (font size floor, contrast-safe styling/backplate, overlap avoidance with selection rectangles/controls) in `src/components/region_selector.py`
- [X] T070 [US2] Integrate output-folder validation error messaging (reason/path/next step) in `src/components/file_selector.py`
- [X] T071 [US2] Wire settings load/save lifecycle and defaults in `src/main.py`

**Checkpoint**: US1 and US2 are independently functional.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Finalize packaging, release readiness, documentation, and success-criteria validation.

- [X] T072 Create PyInstaller onedir release configuration in `build-config.spec`
- [X] T073 [P] Bundle FFmpeg binaries in release pipeline in `scripts/release/build.ps1`
- [X] T074 [P] Bundle Tesseract binaries and eng/deu tessdata in `scripts/release/build.ps1`
- [X] T075 [P] Generate x64 and x86 portable unsigned ZIP packages in `scripts/release/build.ps1`
- [X] T076 Implement optional post-build signing behavior without certificate requirement in `scripts/release/sign.ps1`
- [X] T077 Add SC-001 performance validation test (10-minute target) in `tests/integration/test_performance_sc001.py`
- [X] T078 Add SC-004/SC-005 summary schema validation test in `tests/integration/test_output_schema_sc004_sc005.py`
- [X] T079 Add FR-049 log schema validation test in `tests/integration/test_log_schema_fr049.py`
- [X] T080 Add FR-050 validation test to assert no sidecar log file is created when logging is disabled in `tests/integration/test_log_schema_fr049.py`
- [X] T081 Add FR-044 memory-behavior validation test to assert streaming processing does not retain full-frame history in `tests/integration/test_performance_sc001.py`
- [X] T082 Add release integration test to validate portable ZIP outputs for x64/x86 and required runtime bundling (FR-010, FR-011, FR-012, FR-013) in `tests/integration/test_release_bundle_fr010_fr013.py`
- [X] T083 Add release integration test to validate unsigned packaging succeeds without certificate and optional signing remains post-build (FR-014) in `tests/integration/test_release_signing_fr014.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 completion; blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 completion.
- **Phase 4 (US2)**: Depends on Phase 2 completion; can proceed in parallel with US1 where files do not conflict.
- **Phase 5 (Polish)**: Depends on completion of desired user stories.

### User Story Dependencies

- **US1 (P1)**: Independent after foundational completion.
- **US2 (P2)**: Independent after foundational completion and integrates shared UI/services without requiring US1 delivery.

### Within Each User Story

- Tests are authored first and expected to fail before implementation.
- Service/domain changes precede controller/UI wiring.
- Integration tests validate end-to-end behavior after core implementation.

---

## Parallel Execution Examples

### User Story 1

Run tests in parallel:
- T023, T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034

Run implementation in parallel where possible:
- T038 (`src/services/ocr_service.py`) and T048 (`src/services/video_service.py`)
- T042 (`src/services/export_service.py`) and T044 (`src/services/logging.py`)

### User Story 2

Run tests in parallel:
- T049, T050, T051, T052, T053, T054, T055, T056, T057, T058, T060

Run implementation in parallel where possible:
- T067 (`src/components/region_selector.py`) and T070 (`src/components/file_selector.py`)
- T061, T062, T063, T064 can be coordinated in `src/components/main_window.py`

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US1).
3. Validate US1 independently via integration and schema tests.

### Incremental Delivery

1. Deliver US1 as MVP.
2. Deliver US2 usability/settings enhancements.
3. Complete Phase 5 packaging and validation (unsigned bundles by default, optional signing).

### Traceability Coverage Note

- FR coverage is addressed by unit/integration tasks across Phases 2-5, including fuzzy context matching, line-break normalization, boundary-clipped matching, URL validation, on-demand retrieval, streaming memory behavior constraints, region UX, settings persistence, export behavior, unsigned portable packaging, and release bundle validation.
- SC coverage is addressed by T077 (SC-001), T078 (SC-004/SC-005), and supporting integration tests for workflow completion.

