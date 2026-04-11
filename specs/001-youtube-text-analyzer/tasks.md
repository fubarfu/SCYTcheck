# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), plus `research.md`, `data-model.md`, `contracts/`, `quickstart.md`  
**Last generated**: 2026-04-12 (incorporates single-token extraction clarification and on-screen display-name output rule)

**Tests**: Included. Tests are required by `RTR-001` and Constitution Principle III.

**Organization**: Tasks are grouped by user story to support independent implementation and verification.

## Format: `[ID] [P?] [Story] Description`

- `[P]`: Parallelizable (different files, no direct dependency)
- `[Story]`: User-story label (`[US1]`, `[US2]`) for story-phase tasks only
- Every task includes an exact file path

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare project-level dependencies, tooling, and release/build baseline.

- [X] T001 Update runtime dependencies in `requirements.txt`
- [X] T002 Align lint/test configuration in `pyproject.toml`
- [X] T003 [P] Prepare release bundling baseline in `scripts/release/build.ps1`
- [X] T004 [P] Prepare optional signing baseline in `scripts/release/sign.ps1`
- [ ] T005 Configure portable build spec defaults in `build-config.spec`
- [ ] T006 Establish application startup wiring baseline in `src/main.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core domain, service, and schema capabilities that block all user stories.

**⚠️ CRITICAL**: No user-story work begins until this phase is complete.

- [X] T007 Extend core entities (`VideoAnalysis`, `TextDetection`, `AppearanceEvent`, `PlayerSummary`, `LogRecord`) in `src/data/models.py`
- [ ] T008 Implement deterministic settings path resolution (`%APPDATA%` fallback local) in `src/config.py`
- [ ] T009 Implement first-launch defaults (patterns, toggles, thresholds, quality) in `src/config.py`
- [ ] T010 [P] Add timestamp formatter (`HH:MM:SS.mmm`) in `src/services/analysis_service.py`
- [ ] T011 Implement deterministic output filename generation (`scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv`) in `src/services/export_service.py`
- [ ] T012 Implement two-stage YouTube URL validation (format + accessibility preflight) in `src/services/video_service.py`
- [ ] T013 Implement quality selection with fallback-to-lower and non-blocking warning in `src/services/video_service.py`
- [ ] T014 Implement transient frame retrieval retries (max 3 per seek/read) in `src/services/video_service.py`
- [ ] T015 [P] Implement OCR line aggregation (group Tesseract tokens by line metadata into full-line strings) in `src/services/ocr_service.py`
- [X] T016 [P] Implement OCR normalization for matching (remove line breaks, collapse whitespace) in `src/services/ocr_service.py`
- [X] T017 [P] Implement fuzzy substring pattern matching utility (best-occurrence scan, configurable threshold default 0.75) in `src/services/ocr_service.py`
- [X] T018 [P] Implement boundary-clipped context acceptance utility (2-char overlap or threshold pass) in `src/services/ocr_service.py`
- [X] T019 [P] Implement single-token extraction helpers for after-only (last token before marker), before-only (first token after marker), and both-boundary (first token between markers) modes in `src/services/ocr_service.py`
- [ ] T020 Implement normalized-name utility (lowercase + trim + collapse internal spaces) in `src/services/analysis_service.py`
- [ ] T021 Implement appearance-event merge utility (max gap default 1.0 s) in `src/services/analysis_service.py`
- [ ] T022 Implement summary CSV writer with exact header order `PlayerName,StartTimestamp` in `src/services/export_service.py`
- [X] T023 Implement sidecar log writer with fixed FR-049 schema including `TestedStringRaw` and `TestedStringNormalized` in `src/services/logging.py`
- [ ] T024 [P] Add foundational settings, default persistence, and URL/retry unit tests in `tests/unit/test_config.py` and `tests/unit/test_video_service.py`

**Checkpoint**: Foundation complete; user stories can proceed in parallel.

---

## Phase 3: User Story 1 — Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Analyze a YouTube video across all confirmed regions for the full video duration, extract deduplicated player names using context-pattern rules with single-token extraction, and export a summary CSV plus optional sidecar log.

**Independent Test**: Run the full URL-to-analysis workflow and verify: deduplicated summary output with on-screen-form player names, header-only CSV when no text is found, invalid URL rejection, full-duration analysis coverage (0 to video duration), and correct log diagnostics (raw + normalized tested strings) when logging is enabled.

### Tests for User Story 1

- [ ] T025 [P] [US1] Add integration test for valid URL analysis producing deduplicated summary CSV in `tests/integration/test_us1_workflow.py`
- [ ] T026 [P] [US1] Add integration test for invalid URL rejection with distinct error classification in `tests/integration/test_us1_workflow.py`
- [ ] T027 [P] [US1] Add integration test for header-only summary CSV when no text is detected in `tests/integration/test_us1_workflow.py`
- [X] T028 [P] [US1] Add OCR line aggregation and normalization behavior tests in `tests/unit/test_ocr_service.py`
- [X] T029 [P] [US1] Add fuzzy substring matching tests (threshold, best-occurrence scan) in `tests/unit/test_ocr_service.py`
- [X] T030 [P] [US1] Add boundary-clipped matching tests (2-char overlap and threshold pass cases) in `tests/unit/test_ocr_service.py`
- [X] T031 [P] [US1] Add single-token extraction boundary tests for after-only, before-only, and both modes in `tests/unit/test_ocr_service.py`
- [ ] T032 [P] [US1] Add deterministic multi-pattern tie-break tests (longest span, earliest start, pattern order) per FR-041 in `tests/unit/test_ocr_service.py`
- [ ] T033 [P] [US1] Add recall-first context-matched candidate preservation tests per FR-034 in `tests/unit/test_analysis_service.py`
- [X] T034 [P] [US1] Add deduplication plus on-screen display-name selection tests per FR-028/FR-005 in `tests/unit/test_analysis_service.py`
- [ ] T035 [P] [US1] Add appearance-event gap merge tests per FR-030 in `tests/unit/test_analysis_service.py`
- [ ] T036 [P] [US1] Add summary CSV schema and `HH:MM:SS.mmm` timestamp format tests per SC-004/SC-005 in `tests/unit/test_export_service.py`
- [X] T037 [P] [US1] Add sidecar log schema tests verifying `TestedStringRaw` and `TestedStringNormalized` on accepted and rejected rows in `tests/integration/test_log_schema_fr049.py`
- [ ] T038 [P] [US1] Add analysis progress and completion feedback integration test in `tests/integration/test_us1_workflow.py`
- [ ] T039 [P] [US1] Add export-retry without re-analysis integration test per FR-039 in `tests/integration/test_us1_workflow.py`
- [ ] T040 [P] [US1] Add no-confirmed-region analysis abort integration test per FR-040 in `tests/integration/test_us1_workflow.py`
- [ ] T041 [P] [US1] Add full-video-duration analysis window unit test (start=0.0, end=video duration from `get_video_info`) in `tests/unit/test_main.py`

### Implementation for User Story 1

- [ ] T042 [US1] Implement OCR candidate collection and per-region frame iteration in `src/services/analysis_service.py`
- [ ] T043 [US1] Implement global pattern-filter toggle behavior (FR-023/FR-042) in `src/services/analysis_service.py`
- [ ] T044 [US1] Integrate fuzzy substring matching with single-token extraction flow in `src/services/ocr_service.py`
- [ ] T045 [US1] Implement deterministic tie-break resolution for competing pattern matches per FR-041 in `src/services/ocr_service.py`
- [ ] T046 [US1] Preserve every non-empty context-matched candidate through collection before aggregation per FR-034 in `src/services/analysis_service.py`
- [ ] T047 [US1] Implement normalized-key grouping with earliest on-screen `PlayerName` selection per FR-028/FR-005 in `src/services/analysis_service.py`
- [ ] T048 [US1] Build and export summary CSV rows with correct schema in `src/services/export_service.py`
- [X] T049 [US1] Build sidecar log records with `TestedStringRaw` and `TestedStringNormalized` diagnostics fields in `src/services/logging.py`
- [ ] T050 [US1] Preserve in-memory analysis results on export failure and support retry action without re-running detection per FR-039 in `src/main.py`
- [ ] T051 [US1] Enforce analysis abort and non-blocking message when no regions are confirmed per FR-040 in `src/main.py`
- [ ] T052 [US1] Wire full-duration analysis window (`start=0.0`, `end=get_video_info duration`), timed frame iteration, and 3-retry behavior in `src/services/video_service.py` and `src/main.py`

**Checkpoint**: US1 independently functional and testable.

---

## Phase 4: User Story 2 — Easy Input and Output Handling (Priority: P2)

**Goal**: Provide simple, reliable UI/UX for URL input, output folder selection, region selection, and advanced settings — all operable via keyboard with persisted configuration.

**Independent Test**: Complete a keyboard-driven workflow from URL entry through analysis start with persisted advanced settings, correctly placed non-overlapping controls, and expected region selector foreground/instruction behavior.

### Tests for User Story 2

- [ ] T053 [P] [US2] Add URL entry and output-folder workflow tests in `tests/unit/test_main_window.py`
- [ ] T054 [P] [US2] Add auto-generated filename and folder-validation tests in `tests/unit/test_file_selector.py`
- [ ] T055 [P] [US2] Add advanced settings persistence round-trip tests in `tests/unit/test_main_window.py`
- [ ] T056 [P] [US2] Add first-launch default toggles, patterns, and quality level tests in `tests/unit/test_main_window.py`
- [ ] T057 [P] [US2] Add OCR sensitivity controls and low-quality warning guidance tests per FR-035 in `tests/unit/test_main_window.py`
- [ ] T058 [P] [US2] Add keyboard-only operability tests for all primary workflow controls per FR-043 in `tests/unit/test_main_window.py`
- [ ] T059 [P] [US2] Add region selector scrollbar-only navigation tests per FR-019 in `tests/unit/test_region_selector.py`
- [ ] T060 [P] [US2] Add foreground launch and below-video instruction placement tests per FR-036/FR-051 in `tests/unit/test_region_selector.py`
- [ ] T061 [P] [US2] Add FR-037 legibility constraints tests (font size ≥14 px, contrast ratio ≥4.5:1) in `tests/unit/test_region_selector.py`
- [ ] T062 [P] [US2] Add helper-text visibility lifecycle tests (visible on open, not removed until close/explicit dismiss) per FR-020 in `tests/unit/test_region_selector.py`
- [ ] T063 [P] [US2] Add logging-disabled no-prompt/no-warning behavior tests per FR-052 in `tests/unit/test_main.py`
- [ ] T064 [US2] Add integration test for persisted settings and keyboard-driven workflow in `tests/integration/test_us2_settings_workflow.py`

### Implementation for User Story 2

- [ ] T065 [US2] Implement URL input validation status wiring (format + preflight feedback) in `src/components/url_input.py`
- [ ] T066 [US2] Implement folder-only output selector with actionable error messages per FR-017 in `src/components/file_selector.py`
- [ ] T067 [US2] Implement advanced settings UI (context patterns, filter toggle, logging toggle, OCR sensitivity, event-gap threshold) in `src/components/main_window.py`
- [ ] T068 [US2] Implement quality selector UI with exactly four levels (`best`, `720p`, `480p`, `360p`) per FR-046 in `src/components/main_window.py`
- [ ] T069 [US2] Implement keyboard shortcuts and focus traversal for all primary workflow controls per FR-043 in `src/components/main_window.py`
- [ ] T070 [US2] Enforce non-overlapping labels and controls at minimum window size 1024×768 per FR-033 in `src/components/main_window.py`
- [ ] T071 [US2] Implement region selector: foreground launch, scrollbar-only navigation, dedicated below-video instruction panel, minimum legibility rules per FR-036/FR-037/FR-051 in `src/components/region_selector.py`
- [ ] T072 [US2] Wire settings load/save lifecycle and first-launch startup defaults in `src/main.py`

**Checkpoint**: US2 independently functional and testable.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Final hardening, release packaging validation, and full RTR-001 traceability checks.

- [ ] T073 Add SC-001 performance validation test (10-minute video under 5 minutes) in `tests/integration/test_performance_sc001.py`
- [ ] T074 [P] Add SC-004/SC-005 summary CSV schema and timestamp format validation test in `tests/integration/test_output_schema_sc004_sc005.py`
- [ ] T075 [P] Add FR-005/FR-028 on-screen `PlayerName` consistency and FR-049 sidecar schema validation tests in `tests/integration/test_log_schema_fr049.py` and `tests/integration/test_us1_workflow.py`
- [ ] T076 [P] Add FR-050 no-log-file-when-disabled validation test in `tests/integration/test_log_schema_fr049.py`
- [ ] T077 [P] Add FR-010..FR-013 release bundle content validation test in `tests/integration/test_release_bundle_fr010_fr013.py`
- [ ] T078 [P] Add FR-014 unsigned-release and optional-signing validation test in `tests/integration/test_release_signing_fr014.py`
- [ ] T079 Validate quickstart walkthrough steps (including step 14: on-screen PlayerName preservation) against implemented behavior in `specs/001-youtube-text-analyzer/quickstart.md`
- [ ] T080 Run final quality gates (`pytest`, `ruff check`) and capture results in `README.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1: no dependencies.
- Phase 2: depends on Phase 1; blocks all story phases.
- Phase 3 (US1) and Phase 4 (US2): both depend on Phase 2 and can run in parallel.
- Phase 5: depends on all selected story completions.

### User Story Dependencies

- US1 (P1): independent after Phase 2 completion.
- US2 (P2): independent after Phase 2 completion.
- US1 and US2 may proceed in parallel when targeting different files.

### Within Each User Story

- Write tests first and confirm failure before implementation.
- Implement core service/domain logic before UI/controller wiring.
- Finish with integration validation.

---

## Parallel Execution Examples

### US1 Parallel Work

- Test batch (all target same or different files): T025–T041
- Implementation batch (different source files): T044 (`src/services/ocr_service.py`), T048 (`src/services/export_service.py`), T049 (`src/services/logging.py`), T052 (`src/services/video_service.py`)

### US2 Parallel Work

- Test batch: T053–T063
- Implementation batch (different component files): T065 (`src/components/url_input.py`), T066 (`src/components/file_selector.py`), T071 (`src/components/region_selector.py`)

---

## RTR-001 Traceability Summary

| Requirement | Covered by |
|-------------|-----------|
| FR-001 | T065 |
| FR-002 | T012, T024, T026 |
| FR-003 | T052 |
| FR-004 | T042 |
| FR-005 | T034, T047, T075 |
| FR-006 | T022, T036 |
| FR-007 | T038 |
| FR-008 | T026, T051 |
| FR-009 | T071 |
| FR-010..FR-013 | T077 |
| FR-014 | T078 |
| FR-015 | T011, T054 |
| FR-016 | T066 |
| FR-017 | T054, T066 |
| FR-018 | T059, T071 |
| FR-019 | T059 |
| FR-020 | T062, T071 |
| FR-021 | T067 |
| FR-022 | T017, T029, T030, T044 |
| FR-023 | T043, T055 |
| FR-024 | T056 |
| FR-025 | T067 |
| FR-026 | T019, T031, T044 |
| FR-027 | T008, T009, T072 |
| FR-028 | T034, T047, T075 |
| FR-029 | T020 |
| FR-030 | T021, T035 |
| FR-031 | T010, T036 |
| FR-032 | T071 |
| FR-033 | T070 |
| FR-034 | T033, T046 |
| FR-035 | T057, T067 |
| FR-036 | T060, T071 |
| FR-037 | T061, T071 |
| FR-038 | T014, T052 |
| FR-039 | T039, T050 |
| FR-040 | T040, T051 |
| FR-041 | T032, T045 |
| FR-042 | T043 |
| FR-043 | T058, T069 |
| FR-044 | T052 |
| FR-045 | T012, T026 |
| FR-046 | T013, T068 |
| FR-047 | T067 |
| FR-048 | T049 |
| FR-049 | T037, T049 |
| FR-050 | T076 |
| FR-051 | T060, T071 |
| FR-052 | T063 |
| SC-001 | T073 |
| SC-004 | T024, T036, T074 |
| SC-005 | T010, T036, T074 |

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 (Setup) and Phase 2 (Foundational).
2. Complete all US1 tasks in Phase 3.
3. Validate US1 independently before expanding to US2 scope.

### Incremental Delivery

1. Deliver US1 core analysis pipeline, extraction, deduplication, and export.
2. Deliver US2 UX, settings persistence, and advanced controls.
3. Complete Phase 5 polish/release validation.

### Team Parallelization

1. Complete setup and foundational tasks together.
2. Split US1 and US2 across developers.
3. Rejoin for polish and release checks.

## FR to Test Traceability (RTR-001)

- FR-001: T065
- FR-002: T012, T024, T025, T026
- FR-003: T052
- FR-004: T042
- FR-005: T034, T047, T075
- FR-006: T022, T036
- FR-007: T038
- FR-008: T025, T026
- FR-009: T059, T071
- FR-010: T003, T077
- FR-011: T003, T077
- FR-012: T077
- FR-013: T077
- FR-014: T004, T078
- FR-015: T011, T054
- FR-016: T054, T066
- FR-017: T053, T066
- FR-018: T059, T071
- FR-019: T059, T071
- FR-020: T062
- FR-021: T055, T067
- FR-022: T017, T018, T029, T030
- FR-023: T043, T055
- FR-024: T009, T056
- FR-025: T055, T067
- FR-026: T019, T031, T044
- FR-027: T008, T009, T055, T072
- FR-028: T034, T047
- FR-029: T020
- FR-030: T021, T035
- FR-031: T010, T036
- FR-032: T059, T071
- FR-033: T070
- FR-034: T033, T046
- FR-035: T057, T067
- FR-036: T060, T071
- FR-037: T061, T071
- FR-038: T014, T024
- FR-039: T039, T050
- FR-040: T040, T051
- FR-041: T032, T045
- FR-042: T043
- FR-043: T058, T069
- FR-044: T042
- FR-045: T012, T026
- FR-046: T013, T056, T068
- FR-047: T055, T067
- FR-048: T023, T037, T048
- FR-049: T037, T049
- FR-050: T076
- FR-051: T060, T071
- FR-052: T063

## SC to Validation Traceability

- SC-001: T073
- SC-004: T036, T074
- SC-005: T010, T036, T074

## Non-FR Support Task Traceability

These tasks are intentionally not mapped to specific FR/SC items because they provide foundational setup, project hygiene, documentation verification, or release gating support required to execute and validate feature work.

- Infrastructure/setup: T001, T002, T005, T006, T007, T015, T016, T017, T018
- Documentation/release validation: T079, T080
