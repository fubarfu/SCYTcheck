# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included. Tests are required by `RTR-001` and Constitution Principle III.

## Format: `[ID] [P?] [Story] Description`

- `[P]` indicates task can run in parallel (different files, no direct dependency)
- `[US1]`, `[US2]` map to user stories in `spec.md`
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Align dependencies, release scripts, and baseline project wiring.

- [X] T001 Update runtime dependency list for OCR/fuzzy matching/video stack in `requirements.txt`
- [X] T002 Align lint/test configuration and markers for unit/integration coverage in `pyproject.toml`
- [X] T003 [P] Prepare release build inputs for x64/x86 bundle flow in `scripts/release/build.ps1`
- [X] T004 [P] Prepare optional signing script behavior for post-build signing in `scripts/release/sign.ps1`
- [X] T005 Add release spec defaults for portable bundle layout in `build-config.spec`
- [X] T006 Add feature wiring checkpoints and startup guard rails in `src/main.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain/services that block all user stories until complete.

**CRITICAL**: No US1/US2 implementation starts until this phase is done.

- [X] T007 Extend domain entities for `VideoAnalysis`, `TextDetection`, `AppearanceEvent`, `PlayerSummary`, `LogRecord` in `src/data/models.py`
- [X] T008 Implement settings persistence path resolution (`%APPDATA%` then local fallback) in `src/config.py`
- [X] T009 Implement first-launch defaults for patterns/filter/logging/sensitivity/gap in `src/config.py`
- [X] T010 [P] Implement timestamp formatting helper (`HH:MM:SS.mmm`) in `src/services/analysis_service.py`
- [X] T011 Implement deterministic output filename generator (`scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv`) in `src/services/export_service.py`
- [X] T012 Implement two-stage URL validation (format then accessibility preflight) in `src/services/video_service.py`
- [X] T013 Implement quality selection and controlled fallback warning behavior in `src/services/video_service.py`
- [X] T014 Implement transient frame retrieval retry policy (max 3 tries) in `src/services/video_service.py`
- [X] T015 [P] Implement OCR text normalization utility (join region text, remove line breaks, collapse whitespace) in `src/services/ocr_service.py`
- [X] T016 [P] Implement fuzzy substring pattern locator with configurable threshold (default 0.75) in `src/services/ocr_service.py`
- [X] T017 [P] Implement boundary-clipped context acceptance helper in `src/services/ocr_service.py`
- [X] T018 Implement normalized-name key utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [X] T019 Implement appearance-event merge utility with default gap 1.0 seconds in `src/services/analysis_service.py`
- [X] T020 Implement summary CSV writer with exact header order `PlayerName,StartTimestamp` in `src/services/export_service.py`
- [X] T021 Implement sidecar log CSV writer with fixed FR-049 schema in `src/services/logging.py`
- [X] T022 [P] Add foundational tests for settings defaults/persistence in `tests/unit/test_config.py`
- [X] T023 [P] Add foundational tests for URL validation, retry policy, and quality behavior in `tests/unit/test_video_service.py`

**Checkpoint**: Foundation complete; user stories can proceed.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Deliver reliable analysis and summary export from URL + confirmed regions using robust OCR/context matching.

**Independent Test**: Run analysis for a known sample and verify deduplicated summary output, invalid URL handling, no-text behavior, and timestamp format.

### Tests for User Story 1

- [X] T024 [P] [US1] Add integration test for valid URL analysis end-to-end summary generation in `tests/integration/test_us1_workflow.py`
- [X] T025 [P] [US1] Add integration test for invalid URL rejection before frame analysis in `tests/integration/test_us1_workflow.py`
- [X] T026 [P] [US1] Add integration test for no-text header-only CSV plus user feedback message in `tests/integration/test_us1_workflow.py`
- [X] T075 [P] [US1] Add integration test for analysis progress and completion feedback in `tests/integration/test_us1_workflow.py`
- [X] T027 [P] [US1] Add OCR normalization tests for joined region text and line-break removal in `tests/unit/test_ocr_service.py`
- [X] T028 [P] [US1] Add fuzzy substring search tests for context location within longer OCR strings in `tests/unit/test_ocr_service.py`
- [X] T029 [P] [US1] Add boundary-clipped context matching tests for overlap and threshold paths in `tests/unit/test_ocr_service.py`
- [X] T030 [P] [US1] Add extraction boundary tests for before-only/after-only/both markers in `tests/unit/test_ocr_service.py`
- [X] T031 [P] [US1] Add deterministic pattern conflict resolution tests for FR-041 tie-break rules in `tests/unit/test_ocr_service.py`
- [X] T032 [P] [US1] Add recall-first candidate preservation tests for FR-034 in `tests/unit/test_ocr_service.py`
- [X] T077 [P] [US1] Add unit tests for FR-042 behavior when pattern filtering is disabled in `tests/unit/test_analysis_service.py`
- [X] T033 [P] [US1] Add normalization and deduplication tests for FR-028/FR-029 in `tests/unit/test_analysis_service.py`
- [X] T034 [P] [US1] Add appearance-event gap merge tests for FR-030 in `tests/unit/test_analysis_service.py`
- [X] T035 [P] [US1] Add summary CSV schema and timestamp format tests for SC-004/SC-005 in `tests/unit/test_export_service.py`
- [X] T078 [P] [US1] Add integration test for FR-040 no-confirmed-region analysis abort in `tests/integration/test_us1_workflow.py`
- [X] T079 [P] [US1] Add integration test for FR-039 export retry without re-analysis in `tests/integration/test_us1_workflow.py`

### Implementation for User Story 1

- [X] T036 [US1] Implement OCR candidate collection pipeline over selected regions in `src/services/analysis_service.py`
- [X] T037 [US1] Enforce global pattern filter toggle behavior for matching/non-matching candidates in `src/services/analysis_service.py`
- [X] T038 [US1] Enforce fuzzy substring matching + extraction flow integration in `src/services/ocr_service.py`
- [X] T039 [US1] Apply deterministic tie-break rules for multi-pattern matches in `src/services/ocr_service.py`
- [X] T040 [US1] Preserve non-empty context-matched candidates through pre-aggregation stage in `src/services/analysis_service.py`
- [X] T041 [US1] Compute merged events and earliest per-name `StartTimestamp` in `src/services/analysis_service.py`
- [X] T042 [US1] Wire summary CSV export and header-only output handling in `src/services/export_service.py`
- [X] T043 [US1] Wire optional sidecar log record creation on accepted/rejected candidates in `src/services/logging.py`
- [X] T044 [US1] Preserve in-memory results after export failure and expose retry-export path in `src/main.py`
- [X] T045 [US1] Abort analysis start when region selection closes without confirmed region in `src/main.py`
- [X] T046 [US1] Wire frame iteration/timestamps/retry into analysis loop in `src/services/video_service.py`

**Checkpoint**: US1 is independently functional and testable.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Provide a simple, accessible UI for URL entry, folder-only output, region workflow, and advanced settings persistence.

**Independent Test**: Complete keyboard-only workflow from URL entry through output folder selection and analysis start with persisted advanced settings.

### Tests for User Story 2

- [X] T047 [P] [US2] Add unit tests for URL entry and output-folder selection workflow in `tests/unit/test_main_window.py`
- [X] T048 [P] [US2] Add unit tests for auto-generated filename behavior and folder validation errors in `tests/unit/test_file_selector.py`
- [X] T049 [P] [US2] Add unit tests for advanced settings persistence across app restarts in `tests/unit/test_main_window.py`
- [X] T050 [P] [US2] Add unit tests for default settings state (filter on, logging off, default patterns) in `tests/unit/test_main_window.py`
- [X] T051 [P] [US2] Add unit tests for quality selector options/default/fallback warning messaging in `tests/unit/test_main_window.py`
- [X] T052 [P] [US2] Add unit tests for OCR sensitivity controls and low-quality reliability notice in `tests/unit/test_main_window.py`
- [X] T053 [P] [US2] Add unit tests for keyboard-only operation of core controls in `tests/unit/test_main_window.py`
- [X] T054 [P] [US2] Add unit tests for region selector scrollbar-only navigation in `tests/unit/test_region_selector.py`
- [X] T055 [P] [US2] Add unit tests for foreground popup and below-video instruction placement in `tests/unit/test_region_selector.py`
- [X] T056 [P] [US2] Add unit tests for FR-037 legibility constraints (font >=14px, contrast >=4.5:1, no overlap) in `tests/unit/test_region_selector.py`
- [X] T076 [P] [US2] Add unit test for FR-020 helper text visibility lifecycle in `tests/unit/test_region_selector.py`
- [X] T057 [P] [US2] Add unit test for FR-052 no logging-disabled warning/prompt behavior in `tests/unit/test_main.py`
- [X] T058 [US2] Add integration test for persisted settings + keyboard workflow in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [X] T059 [US2] Implement URL input + validation status wiring in `src/components/url_input.py`
- [X] T060 [US2] Implement folder-only selector with actionable error messaging in `src/components/file_selector.py`
- [X] T061 [US2] Implement advanced settings UI for context patterns/filter/logging/sensitivity in `src/components/main_window.py`
- [X] T062 [US2] Implement quality selector UI with fixed levels (`best`,`720p`,`480p`,`360p`) in `src/components/main_window.py`
- [X] T063 [US2] Implement keyboard shortcut/focus behavior for core workflow controls in `src/components/main_window.py`
- [X] T064 [US2] Enforce non-overlapping label/control layout at minimum supported size in `src/components/main_window.py`
- [X] T065 [US2] Implement region selector foreground behavior, dedicated instruction panel below video, and scrollbar-only navigation in `src/components/region_selector.py`
- [X] T066 [US2] Wire settings load/save lifecycle and startup defaults in `src/main.py`

**Checkpoint**: US2 is independently functional and testable.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, packaging, and traceability validations.

- [X] T067 Add integration performance validation for SC-001 in `tests/integration/test_performance_sc001.py`
- [X] T068 [P] Add integration validation for summary CSV schema/encoding/timestamp criteria in `tests/integration/test_output_schema_sc004_sc005.py`
- [X] T069 [P] Add integration validation for FR-049 sidecar log schema and acceptance/rejection constraints in `tests/integration/test_log_schema_fr049.py`
- [X] T070 [P] Add integration validation for FR-050 (no log file when logging disabled) in `tests/integration/test_log_schema_fr049.py`
- [X] T071 [P] Add integration validation for FR-010/FR-011/FR-012/FR-013 release bundle contents in `tests/integration/test_release_bundle_fr010_fr013.py`
- [X] T072 [P] Add integration validation for FR-014 unsigned packaging success and optional signing path in `tests/integration/test_release_signing_fr014.py`
- [X] T073 Validate quickstart walkthrough against implemented behavior in `specs/001-youtube-text-analyzer/quickstart.md`
- [X] T074 Run full regression and lint gates (`pytest`, `ruff check`) and record results in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup) has no dependencies.
- Phase 2 (Foundational) depends on Phase 1 and blocks all user stories.
- Phase 3 (US1) and Phase 4 (US2) depend on Phase 2.
- Phase 5 (Polish) depends on completion of selected user stories.

### User Story Dependencies

- US1 (P1) can start immediately after Phase 2.
- US2 (P2) can start immediately after Phase 2.
- US1 and US2 are independently testable and can proceed in parallel with coordination on shared files.

### Within Each User Story

- Write tests first; verify they fail before implementation.
- Implement service/data logic before UI/controller wiring.
- Complete integration tests before marking story complete.

---

## Parallel Execution Examples

### US1 Parallel Work

- Test batch: T024, T025, T026, T075, T027, T028, T029, T030, T031, T032, T077, T033, T034, T035, T078, T079
- Implementation batch: T038 (`src/services/ocr_service.py`), T042 (`src/services/export_service.py`), T043 (`src/services/logging.py`), T046 (`src/services/video_service.py`)

### US2 Parallel Work

- Test batch: T047, T048, T049, T050, T051, T052, T053, T054, T055, T056, T076, T057
- Implementation batch: T059 (`src/components/url_input.py`), T060 (`src/components/file_selector.py`), T065 (`src/components/region_selector.py`)

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (Phase 3).
3. Validate US1 independently with integration and schema checks.

### Incremental Delivery

1. Deliver US1 (core analysis/export).
2. Deliver US2 (usability/settings UX).
3. Finish Phase 5 release and cross-cutting validations.

### Traceability Note

- FR coverage is distributed across foundational, US1, US2, and polish tasks.
- SC coverage is explicit: T067 (SC-001), T068 (SC-004/SC-005), with SC-002/SC-003 supported by workflow and UX validation tasks.

## FR to Test Traceability (RTR-001)

- FR-001: T047, T024
- FR-002: T023, T025
- FR-003: T046, T024
- FR-004: T036, T024
- FR-005: T040, T041, T069
- FR-006: T020, T035, T068
- FR-007: T075
- FR-008: T025, T026, T060
- FR-009: T065, T054
- FR-010: T071
- FR-011: T071
- FR-012: T071
- FR-013: T071
- FR-014: T072
- FR-015: T011, T048
- FR-016: T060, T047
- FR-017: T060, T048
- FR-018: T054, T065
- FR-019: T054, T065
- FR-020: T076, T055
- FR-021: T061, T049
- FR-022: T028, T038
- FR-023: T037, T050
- FR-024: T009, T050
- FR-025: T061, T049
- FR-026: T030, T038
- FR-027: T008, T009, T049, T066
- FR-028: T033, T041
- FR-029: T018, T033
- FR-030: T019, T034, T041
- FR-031: T010, T035, T068
- FR-032: T054, T065, T078
- FR-033: T064, T056
- FR-034: T032, T040
- FR-035: T052, T063
- FR-036: T055, T065
- FR-037: T056, T065
- FR-038: T014, T023, T046
- FR-039: T079, T044
- FR-040: T078, T045
- FR-041: T031, T039
- FR-042: T077, T037
- FR-043: T053, T063, T058
- FR-044: T067
- FR-045: T023, T025
- FR-046: T013, T051, T062
- FR-047: T050, T061
- FR-048: T069, T021, T043
- FR-049: T021, T069
- FR-050: T070
- FR-051: T055, T065
- FR-052: T057

## SC to Validation Traceability

- SC-001: T067
- SC-004: T035, T068
- SC-005: T010, T035, T068
