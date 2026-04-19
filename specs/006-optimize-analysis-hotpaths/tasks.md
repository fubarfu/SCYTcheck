# Tasks: Optimize Analysis Hotpaths

**Input**: Design documents from `specs/006-optimize-analysis-hotpaths/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `quickstart.md`, `contracts/timing-output-contract.md`

**Tests**: Tests are required by spec (FR-018, FR-019, FR-020, SC-011, SC-013).

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Ensure deterministic fixture and validation scaffolding are present for parity and performance gates.

- [X] T001 Create fixture package marker in `tests/fixtures/__init__.py`
- [X] T002 [P] Implement synthetic frame fixtures in `tests/fixtures/gating_frames.py`
- [X] T003 [P] Implement normalization corpus fixtures in `tests/fixtures/normalization_corpus.py`
- [X] T004 [P] Ensure validation report target path handling in `scripts/validate_hotpaths.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared runtime metrics contracts used across all stories and final gates.

**CRITICAL**: No user story should be finalized before this phase is complete.

- [X] T005 Add timing metrics entities (`TimingBreakdown`, `AnalysisRuntimeMetrics`) in `src/data/models.py`
- [X] T006 [P] Add timing output formatting helper for logging-enabled mode in `src/services/export_service.py`
- [X] T007 [P] Add tests for new metrics model defaults/validation in `tests/unit/test_models.py`
- [X] T008 Wire additive timing fields into analysis result model contract in `src/data/models.py`

**Checkpoint**: Shared timing model and formatting contracts are stable.

---

## Phase 3: User Story 1 - Faster Region Gating With Decision Parity (Priority: P1) 🎯 MVP

**Goal**: Optimize frame-region gating compute path while preserving 100% decision parity.

**Independent Test**: Run baseline-vs-candidate parity and hotpath performance tests; decision mismatches must be 0 and SC-005 must pass.

### Tests for User Story 1

- [X] T009 [P] [US1] Add decision parity coverage for all gating fixture pairs in `tests/unit/test_hotpath_gating_parity.py`
- [X] T010 [P] [US1] Add threshold boundary parity tests in `tests/unit/test_hotpath_gating_parity.py`
- [X] T011 [P] [US1] Add SC-005 gating speed benchmark in `tests/integration/test_hotpath_performance.py`

### Implementation for User Story 1

- [X] T012 [US1] Replace NumPy diff math with OpenCV native diff in `src/services/analysis_service.py`
- [X] T013 [US1] Preserve shape-mismatch and gating reason semantics in `src/services/analysis_service.py`
- [X] T014 [US1] Verify existing gating behavior compatibility tests in `tests/unit/test_analysis_service.py`

**Checkpoint**: US1 works independently with parity and speed gates passing.

---

## Phase 4: User Story 2 - Single Grayscale Conversion Per Frame (Priority: P1)

**Goal**: Reuse one grayscale conversion per sampled frame across all regions without behavioral drift.

**Independent Test**: Conversion-count tests prove one conversion per frame when gating is enabled, and detection parity remains unchanged.

### Tests for User Story 2

- [X] T015 [P] [US2] Add grayscale conversion count instrumentation tests in `tests/unit/test_hotpath_gating_parity.py`
- [X] T016 [P] [US2] Add `_crop_region_gray` equivalence tests with/without `frame_gray` in `tests/unit/test_hotpath_gating_parity.py`
- [X] T017 [P] [US2] Add invalid/empty frame guard tests for grayscale reuse in `tests/unit/test_hotpath_gating_parity.py`

### Implementation for User Story 2

- [X] T018 [US2] Add optional `frame_gray` parameter handling in `_crop_region_gray` in `src/services/analysis_service.py`
- [X] T019 [US2] Compute and reuse `frame_gray` once per sampled frame in `AnalysisService.analyze` in `src/services/analysis_service.py`
- [X] T020 [US2] Keep gating-disabled path behavior unchanged in `src/services/analysis_service.py`

**Checkpoint**: US2 works independently and preserves output parity.

---

## Phase 5: User Story 3 - Precompiled Regex Normalization Without Semantic Drift (Priority: P1)

**Goal**: Remove repeated regex compile overhead while keeping normalization output exactly equivalent.

**Independent Test**: Corpus-based equivalence tests pass with zero mismatches; performance proxy confirms no compile calls in candidate path.

### Tests for User Story 3

- [X] T021 [P] [US3] Add `normalize_for_matching` corpus equivalence tests in `tests/unit/test_hotpath_normalization_parity.py`
- [X] T022 [P] [US3] Add `normalize_name` corpus equivalence tests in `tests/unit/test_hotpath_normalization_parity.py`
- [X] T023 [P] [US3] Add module-level precompile presence tests in `tests/unit/test_hotpath_normalization_parity.py`
- [X] T024 [P] [US3] Add normalization performance proxy test in `tests/integration/test_hotpath_performance.py`

### Implementation for User Story 3

- [X] T025 [US3] Add `_RE_WHITESPACE` module precompile in `src/services/ocr_service.py`
- [X] T026 [US3] Replace inline regex usage in `normalize_for_matching` in `src/services/ocr_service.py`
- [X] T027 [US3] Add `_RE_WHITESPACE` module precompile in `src/services/analysis_service.py`
- [X] T028 [US3] Replace inline regex usage in `normalize_name` in `src/services/analysis_service.py`

**Checkpoint**: US3 works independently with exact normalization parity.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Add per-stage timing output and enforce final validation/go-no-go gates.

- [X] T029 Implement stage timer accumulation (decode, gating, OCR, post-processing) in `src/services/analysis_service.py`
- [X] T030 Emit timing output only when detailed logging is enabled in `src/services/analysis_service.py`
- [X] T031 Surface timing summary formatting in completion/export paths in `src/main.py`
- [X] T032 [P] Add logging-enabled timing emission tests in `tests/integration/test_log_schema_fr049.py`
- [X] T033 [P] Add logging-disabled timing suppression tests in `tests/integration/test_log_schema_fr049.py`
- [X] T034 [P] Add SC-013 instrumentation overhead benchmark (<=2%) in `tests/integration/test_hotpath_performance.py`
- [X] T035 [P] Update validation matrix script to include per-stage timing and overhead checks in `scripts/validate_hotpaths.py`
- [X] T036 [P] Regenerate and verify validation report in `specs/006-optimize-analysis-hotpaths/validation_report.json`
- [X] T037 Run full unit suite gate in `tests/unit/`
- [X] T038 Run required integration/performance gate set in `tests/integration/`
- [X] T039 Update requirements checklist and FR/SC traceability matrix coverage for all FR items (including FR-025..FR-027) and SC-013 in `specs/006-optimize-analysis-hotpaths/checklists/requirements.md` and `specs/006-optimize-analysis-hotpaths/spec.md`
- [X] T040 Update documented risks/mitigations to include timing instrumentation drift and overhead-failure handling in `specs/006-optimize-analysis-hotpaths/spec.md`
- [X] T041 Define and verify objective rollback trigger matrix including SC-013 failure path in `specs/006-optimize-analysis-hotpaths/quickstart.md`
- [X] T042 Verify final go/no-go evidence pack includes rollback trigger evidence for parity, non-regression, and overhead gates in `specs/006-optimize-analysis-hotpaths/checklists/requirements.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): can start immediately.
- Foundational (Phase 2): depends on Setup; blocks finalization of all user stories.
- User Story phases (3-5): depend on completion of Foundational (Phase 2); then can proceed in parallel.
- Polish (Phase 6): depends on completion of Phases 2-5.

### User Story Dependencies

- User Story 1 (P1): independent after Setup.
- User Story 2 (P1): independent after Setup; shares analysis-service touchpoints.
- User Story 3 (P1): independent after Setup; touches normalization paths only.

### Within Each User Story

- Tests first, then implementation.
- Maintain parity contracts before moving to next story.

---

## Parallel Opportunities

- Phase 1: T002 and T003 can run in parallel.
- Phase 2: T006 and T007 can run in parallel after T005 starts model contract changes.
- US1 tests T009-T011 can run in parallel.
- US2 tests T015-T017 can run in parallel.
- US3 tests T021-T024 can run in parallel.
- Phase 6 tests/validation tasks T032-T036 can run in parallel once timing implementation (T029-T031) lands.

---

## Parallel Example: User Story 1

```bash
# Run US1 test tasks in parallel workstreams
Task: "T009 [US1] Add decision parity coverage in tests/unit/test_hotpath_gating_parity.py"
Task: "T010 [US1] Add threshold boundary parity tests in tests/unit/test_hotpath_gating_parity.py"
Task: "T011 [US1] Add SC-005 benchmark in tests/integration/test_hotpath_performance.py"
```

## Parallel Example: User Story 3

```bash
# Run US3 parity and performance tests in parallel workstreams
Task: "T021 [US3] Add normalize_for_matching corpus tests in tests/unit/test_hotpath_normalization_parity.py"
Task: "T022 [US3] Add normalize_name corpus tests in tests/unit/test_hotpath_normalization_parity.py"
Task: "T024 [US3] Add normalization performance proxy in tests/integration/test_hotpath_performance.py"
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Phase 1 and essential Phase 2 contracts.
2. Deliver User Story 1 and validate SC-002 + SC-005.
3. Stop and validate before expanding to US2/US3.

### Incremental Delivery

1. Ship US1 optimization with parity guarantees.
2. Add US2 grayscale reuse and validate SC-004.
3. Add US3 regex precompile and validate SC-006.
4. Add timing output + overhead gate and complete SC-013.

### Final Gate

Release GO requires SC-001, SC-002, SC-003, SC-006, SC-008, SC-009, SC-010, SC-011, and SC-013 passing together.
