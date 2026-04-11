# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included. Tests are required by `RTR-001` and Constitution Principle III.

**Organization**: Tasks are grouped by user story to support independent implementation and verification.

## Format: `[ID] [P?] [Story] Description`

- `[P]`: Parallelizable (different files, no direct dependency)
- `[Story]`: User-story label (`[US1]`, `[US2]`) for story-phase tasks only
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare project-level dependencies, tooling, and release/build baseline.

- [X] T001 Update runtime dependencies in `requirements.txt`
- [X] T002 Align lint/test configuration in `pyproject.toml`
- [X] T003 [P] Prepare release bundling baseline in `scripts/release/build.ps1`
- [X] T004 [P] Prepare optional signing baseline in `scripts/release/sign.ps1`
- [X] T005 Configure portable build spec defaults in `build-config.spec`
- [X] T006 Establish application startup wiring baseline in `src/main.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain, service, and schema capabilities that block all user stories.

**CRITICAL**: No user-story work begins until this phase is complete.

- [X] T007 Extend core entities (`VideoAnalysis`, `TextDetection`, `AppearanceEvent`, `PlayerSummary`, `LogRecord`) in `src/data/models.py`
- [X] T008 Implement deterministic settings path resolution (`%APPDATA%` fallback local) in `src/config.py`
- [X] T009 Implement first-launch defaults (patterns, toggles, thresholds, quality) in `src/config.py`
- [X] T010 [P] Add timestamp formatter (`HH:MM:SS.mmm`) in `src/services/analysis_service.py`
- [X] T011 Implement deterministic output filename generation in `src/services/export_service.py`
- [X] T012 Implement two-stage YouTube URL validation in `src/services/video_service.py`
- [X] T013 Implement quality selection with fallback-to-lower and warning metadata in `src/services/video_service.py`
- [X] T014 Implement transient frame retrieval retries (max 3) in `src/services/video_service.py`
- [X] T015 [P] Implement OCR normalization (join text blocks, remove line breaks, collapse whitespace) in `src/services/ocr_service.py`
- [X] T016 [P] Implement fuzzy substring pattern matching utility in `src/services/ocr_service.py`
- [X] T017 [P] Implement boundary-clipped context acceptance utility in `src/services/ocr_service.py`
- [X] T018 Implement normalized-name utility (lowercase/trim/collapse spaces) in `src/services/analysis_service.py`
- [X] T019 Implement appearance-event merge utility (default gap 1.0s) in `src/services/analysis_service.py`
- [X] T020 Implement summary CSV writer (`PlayerName,StartTimestamp`) in `src/services/export_service.py`
- [X] T021 Implement sidecar log writer with fixed FR-049 schema including tested strings in `src/services/logging.py`
- [X] T022 [P] Add foundational settings/default persistence tests in `tests/unit/test_config.py`
- [X] T023 [P] Add foundational URL/quality/retry tests in `tests/unit/test_video_service.py`

**Checkpoint**: Foundation complete; user stories can proceed.

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze a YouTube video over confirmed regions and export robust deduplicated results.

**Independent Test**: Run full URL-to-analysis workflow and verify deduplicated summary output, no-text behavior, invalid URL handling, and log diagnostics when enabled.

### Tests for User Story 1

- [X] T024 [P] [US1] Add integration test for valid URL analysis to summary CSV in `tests/integration/test_us1_workflow.py`
- [X] T025 [P] [US1] Add integration test for invalid URL rejection in `tests/integration/test_us1_workflow.py`
- [X] T026 [P] [US1] Add integration test for header-only summary when no text found in `tests/integration/test_us1_workflow.py`
- [X] T027 [P] [US1] Add OCR normalization behavior tests in `tests/unit/test_ocr_service.py`
- [X] T028 [P] [US1] Add fuzzy substring matching tests in `tests/unit/test_ocr_service.py`
- [X] T029 [P] [US1] Add boundary-clipped matching tests in `tests/unit/test_ocr_service.py`
- [X] T030 [P] [US1] Add before/after extraction boundary tests in `tests/unit/test_ocr_service.py`
- [X] T031 [P] [US1] Add deterministic multi-pattern tie-break tests (FR-041) in `tests/unit/test_ocr_service.py`
- [X] T032 [P] [US1] Add recall-first context-matched preservation tests (FR-034) in `tests/unit/test_ocr_service.py`
- [X] T033 [P] [US1] Add normalization and deduplication tests (FR-028/FR-029) in `tests/unit/test_analysis_service.py`
- [X] T034 [P] [US1] Add event-gap merge tests (FR-030) in `tests/unit/test_analysis_service.py`
- [X] T035 [P] [US1] Add summary CSV schema/timestamp tests (SC-004/SC-005) in `tests/unit/test_export_service.py`
- [X] T036 [P] [US1] Add logging schema tests for `TestedStringRaw` and `TestedStringNormalized` in `tests/integration/test_log_schema_fr049.py`
- [X] T037 [P] [US1] Add analysis progress/completion feedback integration test in `tests/integration/test_us1_workflow.py`
- [X] T038 [P] [US1] Add export-retry without re-analysis integration test (FR-039) in `tests/integration/test_us1_workflow.py`
- [X] T039 [P] [US1] Add no-confirmed-region analysis abort integration test (FR-040) in `tests/integration/test_us1_workflow.py`
- [X] T040 [P] [US1] Add pattern-filter-disabled acceptance test (FR-042) in `tests/unit/test_analysis_service.py`

### Implementation for User Story 1

- [X] T041 [US1] Implement OCR candidate collection and region iteration in `src/services/analysis_service.py`
- [X] T042 [US1] Implement global pattern-filter toggle behavior in `src/services/analysis_service.py`
- [X] T043 [US1] Integrate fuzzy substring matching/extraction flow in `src/services/ocr_service.py`
- [X] T044 [US1] Implement deterministic tie-break resolution for competing matches in `src/services/ocr_service.py`
- [X] T045 [US1] Preserve non-empty context-matched candidates before aggregation in `src/services/analysis_service.py`
- [X] T046 [US1] Compute merged events and earliest `StartTimestamp` per normalized name in `src/services/analysis_service.py`
- [X] T047 [US1] Build and export summary CSV rows in `src/services/export_service.py`
- [X] T048 [US1] Build sidecar log records with tested-string diagnostics fields in `src/services/logging.py`
- [X] T049 [US1] Preserve in-memory results on export failure and support retry action in `src/main.py`
- [X] T050 [US1] Enforce analysis abort when no regions are confirmed in `src/main.py`
- [X] T051 [US1] Wire timed frame iteration and retry behavior in `src/services/video_service.py`

**Checkpoint**: US1 independently functional and testable.

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Provide simple, reliable UI/UX for URL input, output handling, region selection, and advanced settings.

**Independent Test**: Complete keyboard-driven workflow from URL input to analysis start with persisted settings and correct selector behavior.

### Tests for User Story 2

- [X] T052 [P] [US2] Add URL entry and output-folder workflow tests in `tests/unit/test_main_window.py`
- [X] T053 [P] [US2] Add auto-generated filename and folder-validation tests in `tests/unit/test_file_selector.py`
- [X] T054 [P] [US2] Add advanced settings persistence tests in `tests/unit/test_main_window.py`
- [X] T055 [P] [US2] Add default toggles/patterns/quality tests in `tests/unit/test_main_window.py`
- [X] T056 [P] [US2] Add OCR sensitivity controls and low-quality guidance tests in `tests/unit/test_main_window.py`
- [X] T057 [P] [US2] Add keyboard-only operability tests in `tests/unit/test_main_window.py`
- [X] T058 [P] [US2] Add region selector scrollbar-only navigation tests in `tests/unit/test_region_selector.py`
- [X] T059 [P] [US2] Add foreground + below-video instruction placement tests in `tests/unit/test_region_selector.py`
- [X] T060 [P] [US2] Add FR-037 legibility constraints tests in `tests/unit/test_region_selector.py`
- [X] T061 [P] [US2] Add helper-text visibility lifecycle tests (FR-020) in `tests/unit/test_region_selector.py`
- [X] T062 [P] [US2] Add logging-disabled no-prompt behavior tests (FR-052) in `tests/unit/test_main.py`
- [X] T063 [US2] Add integration test for persisted settings + keyboard workflow in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [X] T064 [US2] Implement URL input validation status wiring in `src/components/url_input.py`
- [X] T065 [US2] Implement folder-only output selector with actionable errors in `src/components/file_selector.py`
- [X] T066 [US2] Implement advanced settings UI (patterns/filter/logging/sensitivity) in `src/components/main_window.py`
- [X] T067 [US2] Implement quality selector UI with fixed levels in `src/components/main_window.py`
- [X] T068 [US2] Implement keyboard shortcuts and focus traversal in `src/components/main_window.py`
- [X] T069 [US2] Enforce non-overlapping labels/controls at minimum window size in `src/components/main_window.py`
- [X] T070 [US2] Implement region selector foreground + instruction panel + scrollbar-only navigation in `src/components/region_selector.py`
- [X] T071 [US2] Wire settings load/save lifecycle and startup defaults in `src/main.py`

**Checkpoint**: US2 independently functional and testable.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, release validation, and traceability checks.

- [X] T072 Add SC-001 performance validation test in `tests/integration/test_performance_sc001.py`
- [X] T073 [P] Add SC-004/SC-005 summary schema validation test in `tests/integration/test_output_schema_sc004_sc005.py`
- [X] T074 [P] Add FR-049 full sidecar schema validation test (incl. tested strings) in `tests/integration/test_log_schema_fr049.py`
- [X] T075 [P] Add FR-050 no-log-file-when-disabled validation test in `tests/integration/test_log_schema_fr049.py`
- [X] T076 [P] Add release bundle content validation test (FR-010..FR-013) in `tests/integration/test_release_bundle_fr010_fr013.py`
- [X] T077 [P] Add unsigned-release and optional-signing validation test (FR-014) in `tests/integration/test_release_signing_fr014.py`
- [X] T078 Validate quickstart walkthrough against implemented behavior in `specs/001-youtube-text-analyzer/quickstart.md`
- [X] T079 Run final gates (`pytest`, `ruff check`) and capture outcomes in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1: no dependencies.
- Phase 2: depends on Phase 1; blocks all story phases.
- Phase 3 and Phase 4: both depend on Phase 2.
- Phase 5: depends on selected story completion.

### User Story Dependencies

- US1 (P1): independent after foundational completion.
- US2 (P2): independent after foundational completion.
- US1 and US2 can proceed in parallel if file-level conflicts are managed.

### Within Each User Story

- Write tests first and confirm failure before implementation.
- Implement core service/domain logic before UI/controller wiring.
- Finish with integration validation.

---

## Parallel Execution Examples

### US1 Parallel Work

- Test batch: T024, T025, T026, T027, T028, T029, T030, T031, T032, T033, T034, T035, T036, T037, T038, T039, T040
- Implementation batch: T043 (`src/services/ocr_service.py`), T047 (`src/services/export_service.py`), T048 (`src/services/logging.py`), T051 (`src/services/video_service.py`)

### US2 Parallel Work

- Test batch: T052, T053, T054, T055, T056, T057, T058, T059, T060, T061, T062
- Implementation batch: T064 (`src/components/url_input.py`), T065 (`src/components/file_selector.py`), T070 (`src/components/region_selector.py`)

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tasks (Phase 3).
3. Validate US1 independently before expanding scope.

### Incremental Delivery

1. Deliver US1 core analysis/export.
2. Deliver US2 UX/settings flow.
3. Complete Phase 5 polish/release validation.

### Team Parallelization

1. Complete setup and foundational tasks together.
2. Split US1 and US2 across developers.
3. Rejoin for polish and release checks.

## FR to Test Traceability (RTR-001)

- FR-001: T052, T024
- FR-002: T023, T025
- FR-003: T051, T024
- FR-004: T041, T024
- FR-005: T045, T046, T074
- FR-006: T020, T035, T073
- FR-007: T037
- FR-008: T025, T026, T065
- FR-009: T070, T058
- FR-010: T076
- FR-011: T076
- FR-012: T076
- FR-013: T076
- FR-014: T077
- FR-015: T011, T053
- FR-016: T065, T052
- FR-017: T065, T053
- FR-018: T058, T070
- FR-019: T058, T070
- FR-020: T061, T059
- FR-021: T066, T054
- FR-022: T028, T043
- FR-023: T042, T055
- FR-024: T009, T055
- FR-025: T066, T054
- FR-026: T030, T043
- FR-027: T008, T009, T054, T071
- FR-028: T033, T046
- FR-029: T018, T033
- FR-030: T019, T034, T046
- FR-031: T010, T035, T073
- FR-032: T058, T070, T039
- FR-033: T069, T060
- FR-034: T032, T045
- FR-035: T056, T066
- FR-036: T059, T070
- FR-037: T060, T070
- FR-038: T014, T023, T051
- FR-039: T038, T049
- FR-040: T039, T050
- FR-041: T031, T044
- FR-042: T040, T042
- FR-043: T057, T068, T063
- FR-044: T072
- FR-045: T023, T025
- FR-046: T013, T055, T067
- FR-047: T055, T066
- FR-048: T074, T021, T048
- FR-049: T036, T074
- FR-050: T075
- FR-051: T059, T070
- FR-052: T062

## SC to Validation Traceability

- SC-001: T072
- SC-004: T035, T073
- SC-005: T010, T035, T073

## Non-FR Support Task Traceability

These tasks are intentionally not mapped to specific FR/SC items because they provide foundational setup, project hygiene, documentation verification, or release gating support required to execute and validate feature work.

- Infrastructure/setup: T001, T002, T003, T004, T005, T006, T007, T012, T015, T016, T017, T022, T027, T029, T047, T064
- Documentation/release validation: T078, T079
