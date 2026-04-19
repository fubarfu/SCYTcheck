# Tasks: Improve Text Analysis

**Input**: Design documents from `specs/005-improve-text-analysis/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Included (required by spec success criteria and constitution testing principle).  
**Organization**: Tasks are grouped by user story for independent implementation and validation.

## Phase 1: Setup (Project Initialization)

- [x] T001 Confirm feature baseline and affected files in `specs/005-improve-text-analysis/plan.md`
- [x] T002 Confirm dependency/runtime assumptions in `requirements.txt` and `pyproject.toml`
- [x] T003 [P] Prepare/update test input fixtures for multiline OCR and static/mixed frame scenarios in `tests/integration/`

---

## Phase 2: Foundational (Blocking Prerequisites)

- [x] T004 Add/verify `AdvancedSettings` fields (`tolerance_value`, `gating_enabled`, `gating_threshold`) in `src/config.py`
- [x] T005 Add/verify `GatingStats` and `VideoAnalysis.gating_stats` in `src/data/models.py`
- [x] T006 Wire settings load/save defaults and validation bounds for new fields in `src/config.py`
- [x] T007 [P] Extend analysis call plumbing to pass tolerance/gating values from UI to services in `src/main.py`
- [x] T008 [P] Add/update foundational config/model tests for settings persistence and `GatingStats` invariants in `tests/unit/test_config.py`
- [x] T009 [P] Add/update foundational model tests for `GatingStats` and `VideoAnalysis` fields in `tests/unit/test_models.py`

**Checkpoint**: Foundation complete; user story implementation can proceed.

---

## Phase 3: User Story 1 - Reliable Name Extraction from Multi-Line Text (Priority: P1)

**Goal**: Extract names reliably when context and names span multiple OCR lines using joined-text-only matching with guardrails.  
**Independent Test**: Multiline overlays produce expected names with >=95% recall.

### Tests (US1)

- [x] T010 [P] [US1] Add unit tests for joined region text normalization and newline/whitespace collapse in `tests/unit/test_ocr_service.py`
- [x] T011 [P] [US1] Add unit tests verifying joined-only matching path (no standalone per-line acceptance path) in `tests/unit/test_ocr_service.py`
- [x] T012 [P] [US1] Add unit tests for nearest bounded span extraction (max 6 tokens) in `tests/unit/test_ocr_service.py`
- [x] T013 [P] [US1] Add unit tests for extracted token validation (reject empty/non-alphanumeric) in `tests/unit/test_ocr_service.py`
- [x] T014 [P] [US1] Add integration test for multiline end-to-end extraction on joined text in `tests/integration/test_us1_multiline_extraction.py`
- [x] T015 [P] [US1] Add SC-001 validation test (>=95% recall) for multiline overlays in `tests/integration/test_performance_sc001.py`

### Implementation (US1)

- [x] T016 [US1] Implement/adjust joined region text builder helper in `src/services/ocr_service.py`
- [x] T017 [US1] Refactor candidate extraction to evaluate patterns against joined text only in `src/services/ocr_service.py`
- [x] T018 [US1] Implement nearest valid bounded span guardrail (`<= 6` tokens) in `src/services/ocr_service.py`
- [x] T019 [US1] Implement extracted token validation and rejection reasons in `src/services/ocr_service.py`
- [x] T020 [US1] Update analysis flow to consume joined-only OCR matching results in `src/services/analysis_service.py`

**Checkpoint**: US1 independently functional and testable.

---

## Phase 4: User Story 2 - User-Controlled Matching Tolerance (Priority: P1)

**Goal**: User can control one global tolerance (0.60-0.95) to improve recovery on OCR character errors.  
**Independent Test**: Relaxed tolerance improves true positives by >=20% versus strict on the same dataset.

### Tests (US2)

- [x] T021 [P] [US2] Add unit tests for tolerance thresholds (0.60, 0.75, 0.95) in fuzzy boundary matching in `tests/unit/test_ocr_service.py`
- [x] T022 [P] [US2] Add unit tests for OCR substitution tolerance behavior (for example `1` vs `l`) in `tests/unit/test_ocr_service.py`
- [x] T023 [P] [US2] Add UI settings tests for tolerance control bounds and persistence in `tests/unit/test_main_window.py`
- [x] T024 [P] [US2] Add integration test for strict vs relaxed tolerance recovery behavior in `tests/integration/test_us2_tolerance_recovery.py`
- [x] T025 [P] [US2] Add SC-002 validation test (>=20% true-positive improvement) in `tests/integration/test_performance_sc002.py`

### Implementation (US2)

- [x] T026 [US2] Add/adjust tolerance control behavior and help text in advanced settings UI in `src/components/main_window.py`
- [x] T027 [US2] Ensure tolerance setting load/save wiring in runtime flow in `src/main.py`
- [x] T028 [US2] Apply global tolerance consistently to joined boundary matching calls in `src/services/ocr_service.py`
- [x] T029 [US2] Preserve default strict behavior (`0.75`) when user does not change settings in `src/config.py`

**Checkpoint**: US2 independently functional and testable.

---

## Phase 5: User Story 3 - Faster Analysis on Static Adjacent Frames (Priority: P2)

**Goal**: Use frame-change gating to skip redundant OCR and improve throughput with bounded detection variance.  
**Independent Test**: Gated run is >=30% faster with <=1% detection variance vs non-gated run.

### Tests (US3)

- [x] T030 [P] [US3] Add/adjust unit tests for normalized MAD pixel-diff calculation and action decisions in `tests/unit/test_analysis_service.py`
- [x] T031 [P] [US3] Add unit tests for per-region gating independence and counter invariants in `tests/unit/test_analysis_service.py`
- [x] T032 [P] [US3] Add integration performance test for SC-003 (>=30% runtime reduction) in `tests/integration/test_us3_gating_performance.py`
- [x] T033 [P] [US3] Add integration accuracy test for SC-004 (<=1% variance) in `tests/integration/test_us3_gating_accuracy.py`
- [x] T034 [P] [US3] Add integration throughput test for SC-005 (>=15% logging-off improvement) in `tests/integration/test_us3_logging_throughput.py`
- [x] T045 [P] [US3] Add integration test that verifies analysis completion summary includes total evaluated, OCR executed, and OCR skipped counters in `tests/integration/test_gating_stats_schema.py`
- [x] T046 [P] [US3] Add integration test for detailed logging mode data completeness (no dropped frame-region gating records) in `tests/integration/test_log_schema_fr049.py`

### Implementation (US3)

- [x] T035 [US3] Finalize gating decision path and thresholds in `src/services/analysis_service.py`
- [x] T036 [US3] Track and expose `GatingStats` counters for all runs in `src/services/analysis_service.py`
- [x] T037 [US3] Emit detailed per-frame-region gating records only when detailed logging is enabled in `src/services/logging.py`
- [x] T038 [US3] Ensure gating UI toggle behavior and persistence wiring in `src/components/main_window.py`
- [x] T044 [US3] Render gating counters in the analysis completion summary UI/export summary payload in `src/services/analysis_service.py` and `src/components/progress_display.py`

**Checkpoint**: US3 independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting

- [x] T039 [P] Update feature docs and user guidance for joined-only matching, tolerance, and gating in `README.md`
- [x] T040 [P] Update/verify quickstart commands and validation steps in `specs/005-improve-text-analysis/quickstart.md`
- [x] T041 Add requirement-to-test traceability checklist updates in `specs/005-improve-text-analysis/checklists/`
- [x] T042 Run full validation suite and fix regressions in `tests/`
- [x] T043 [P] Run lint/type checks and resolve issues in `src/` and `tests/`

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 -> Phase 2 -> Phase 3/4/5 -> Phase 6
- User stories begin only after Phase 2 checkpoint.

### User Story Dependencies

- US1: Starts after Phase 2; independent.
- US2: Starts after Phase 2; independent.
- US3: Starts after Phase 2; independent.

### Within Each Story

- Tests first (must fail before implementation changes).
- Service/model logic before UI wiring where applicable.
- Story checkpoint validation before moving to polish.

---

## Parallel Opportunities

- [P] tasks in setup/foundational can run concurrently.
- Once Phase 2 is complete, US1/US2/US3 can be implemented in parallel.
- Test tasks marked [P] can run concurrently across separate files.

### Parallel Example: US1

```bash
# Parallel test work
T010, T011, T012, T013, T014, T015

# Parallel implementation where safe
T016 and T020 can be split across OCR and analysis service files
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 and validate SC-001.
3. Demo/review multiline reliability improvement.

### Incremental Delivery

1. Add US2 and validate SC-002.
2. Add US3 and validate SC-003/SC-004/SC-005.
3. Complete polish and full suite checks.

### Team Parallel Strategy

1. One engineer handles OCR joined-only extraction + guardrails (US1).
2. One engineer handles tolerance UI/settings + persistence (US2).
3. One engineer handles gating + telemetry/logging path (US3).
4. Shared ownership on Phase 6 validation and docs.
