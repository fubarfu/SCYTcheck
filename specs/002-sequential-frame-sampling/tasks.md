# Tasks: Sequential Video Frame Decode Sampling Optimization

**Input**: Design documents from `/specs/002-sequential-frame-sampling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are required by this feature specification (SC-005, SC-006, SC-008, SC-009, SC-010, SC-011, SC-012, SC-013, SC-014).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare repeatable fixtures and helpers for performance, codec, and memory validation.

- [X] T001 Create feature fixture source list for long-video validation in tests/integration/fixtures/video_sources.json
- [X] T002 Create frame-iteration benchmark helper utilities in tests/integration/helpers/perf_helpers.py
- [X] T003 [P] Create RSS memory checkpoint helper utilities in tests/integration/helpers/memory_helpers.py
- [X] T004 [P] Create codec test input helper utilities for H.264/VP9 runs in tests/integration/helpers/codec_helpers.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared iteration strategy scaffolding required by all user stories.

**CRITICAL**: No user story implementation starts until this phase is complete.

- [X] T005 Add internal iteration strategy state and constants in src/services/video_service.py
- [X] T006 Add guarded fallback decision helper (`decode_error` / `performance_probe`) in src/services/video_service.py
- [X] T007 [P] Add structured debug logging helper methods for iteration telemetry in src/services/video_service.py
- [X] T008 Add startup performance probe helper for sequential-vs-legacy decisioning in src/services/video_service.py
- [X] T009 [P] Add parity assertion helpers for timestamp/frame-count comparisons in tests/integration/helpers/parity_helpers.py
- [X] T010 Add baseline stubs and reusable mocks for sequential/fallback paths in tests/unit/test_video_service.py

**Checkpoint**: Foundation complete; user stories can proceed.

---

## Phase 3: User Story 1 - Analyze Multi-Hour Sessions Faster (Priority: P1) 🎯 MVP

**Goal**: Replace per-sample random seeking with sequential decode sampling to reduce long-video analysis time.

**Independent Test**: Run performance scenarios and verify >=50% speedup for 1-hour videos while maintaining successful completion for 2-hour videos.

### Tests for User Story 1

- [X] T011 [P] [US1] Add unit test ensuring no per-sample random seek in iteration loop in tests/unit/test_video_service.py
- [X] T012 [P] [US1] Add integration test for 1-hour iteration speed target in tests/integration/test_performance_sc001.py
- [X] T013 [P] [US1] Add integration test for 2-hour iteration scaling target in tests/integration/test_performance_sc001.py
- [X] T014 [P] [US1] Add network-stream stability integration test (no repeated re-seek behavior, no timeout regressions) in tests/integration/test_video_service_network_stream.py
- [X] T015 [P] [US1] Add 2-hour RSS checkpoint assertion test (0/50/100, +-10%) in tests/integration/test_video_service_memory_stability.py

### Implementation for User Story 1

- [X] T016 [US1] Implement sequential decode traversal in iterate_frames_with_timestamps in src/services/video_service.py
- [X] T017 [US1] Implement sample-step frame selection during sequential traversal in src/services/video_service.py
- [X] T018 [US1] Wire startup probe to enable guarded fallback activation in src/services/video_service.py
- [X] T019 [US1] Emit sequential performance and fallback telemetry events in src/services/video_service.py
- [X] T020 [US1] Update performance test scenarios and add assertions for sequential-path targets in tests/integration/test_performance_sc001.py

**Checkpoint**: User Story 1 is independently testable and delivers measurable performance gains.

---

## Phase 4: User Story 2 - Preserve Exact Timestamp Fidelity (Priority: P1)

**Goal**: Keep timestamp and frame selection behavior identical to baseline across long durations and codecs.

**Independent Test**: Compare timestamp sequences and frame counts between legacy and sequential strategies on synthetic and codec-targeted inputs.

### Tests for User Story 2

- [X] T021 [P] [US2] Add unit test for exact timestamp parity against baseline selector in tests/unit/test_video_service.py
- [X] T022 [P] [US2] Add unit test for frame-count parity tolerance (+/-1) across ranges in tests/unit/test_video_service.py
- [X] T023 [P] [US2] Add integration test for H.264/VP9 timestamp and OCR parity in tests/integration/test_video_service_codec_parity.py

### Implementation for User Story 2

- [X] T024 [US2] Implement shared frame-index selection utility used by sequential and fallback paths in src/services/video_service.py
- [X] T025 [US2] Preserve native-fps fallback and step calculation semantics in src/services/video_service.py
- [X] T026 [US2] Preserve empty/single-frame/out-of-bounds range behavior in src/services/video_service.py
- [X] T027 [US2] Add deterministic timestamp regression fixtures and assertions in tests/unit/test_video_service.py

**Checkpoint**: User Story 2 is independently testable and guarantees timestamp fidelity.

---

## Phase 5: User Story 3 - Preserve Backward Compatibility (Priority: P1)

**Goal**: Keep existing callers/tests working unchanged while supporting guarded fallback and fail-fast behavior.

**Independent Test**: Run existing workflow tests and compatibility assertions with no caller API changes.

### Tests for User Story 3

- [X] T028 [P] [US3] Add regression test confirming existing workflow behavior is unchanged in tests/integration/test_us1_workflow.py
- [X] T029 [P] [US3] Add unit test confirming iterate_frames_with_timestamps signature/contract remains unchanged in tests/unit/test_video_service.py
- [X] T030 [P] [US3] Add integration test for decode-error fallback parity behavior in tests/integration/test_video_service_fallback.py
- [X] T031 [P] [US3] Add debug-log assertion test for exactly one init-seek event and no repeated random-seek events in tests/integration/test_video_service_logging_contract.py
- [X] T032 [P] [US3] Add fallback telemetry assertion test for trigger category and source identifier fields in tests/integration/test_video_service_fallback.py

### Implementation for User Story 3

- [X] T033 [US3] Preserve public iterator contract while integrating strategy switching in src/services/video_service.py
- [X] T034 [US3] Preserve stream cache behavior (`url|quality`) across sequential and fallback paths in src/services/video_service.py
- [X] T035 [US3] Implement fail-fast read-error behavior with structured fallback-reason logging in src/services/video_service.py
- [X] T036 [US3] Add analysis pipeline regression assertions for unchanged downstream behavior in tests/unit/test_analysis_service.py

**Checkpoint**: User Story 3 is independently testable and backward compatibility is preserved.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalize validation evidence, documentation, and cleanup across all stories.

- [X] T037 [P] Add final validation runbook and command sequence updates in specs/002-sequential-frame-sampling/quickstart.md
- [X] T038 [P] Document measured benchmark and memory-checkpoint evidence in specs/002-sequential-frame-sampling/research.md
- [X] T039 Normalize debug telemetry message fields and reason categories in src/services/video_service.py
- [X] T040 Run full regression suite, capture failures, and fix implementation or fixtures as needed; do not relax assertions without explicit approval

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1): No dependencies.
- Foundational (Phase 2): Depends on Setup; blocks all user stories.
- User Stories (Phases 3-5): Depend on Foundational completion.
- Polish (Phase 6): Depends on completion of targeted user stories.

### User Story Dependencies

- US1 (P1): Can start after Phase 2; defines primary MVP outcome.
- US2 (P1): Can start after Phase 2; should not require US3 completion.
- US3 (P1): Can start after Phase 2; validates compatibility once US1/US2 code paths exist.

### Within Each User Story

- Tests first (must fail before implementation).
- Core service logic before integration wiring.
- Story checkpoint validation before moving onward.

### Parallel Opportunities

- Phase 1 tasks marked [P] can run in parallel.
- Phase 2 tasks marked [P] can run in parallel.
- In each story, [P] tests can run in parallel.
- Cross-story work can run in parallel after Phase 2 when file conflicts are managed.

---

## Parallel Example: User Story 1

```bash
# Run US1 test authoring tasks in parallel:
Task: T011 tests/unit/test_video_service.py
Task: T012 tests/integration/test_performance_sc001.py
Task: T013 tests/integration/test_performance_sc001.py
Task: T014 tests/integration/test_video_service_network_stream.py
Task: T015 tests/integration/test_video_service_memory_stability.py

# Then implement core US1 service tasks sequentially:
Task: T016 src/services/video_service.py
Task: T017 src/services/video_service.py
Task: T018 src/services/video_service.py
Task: T019 src/services/video_service.py
```

## Parallel Example: User Story 2

```bash
# Run US2 tests in parallel:
Task: T021 tests/unit/test_video_service.py
Task: T022 tests/unit/test_video_service.py
Task: T023 tests/integration/test_video_service_codec_parity.py
```

## Parallel Example: User Story 3

```bash
# Run US3 compatibility tests in parallel:
Task: T028 tests/integration/test_us1_workflow.py
Task: T029 tests/unit/test_video_service.py
Task: T030 tests/integration/test_video_service_fallback.py
Task: T031 tests/integration/test_video_service_logging_contract.py
Task: T032 tests/integration/test_video_service_fallback.py
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 (Phase 3).
3. Validate performance targets and no-seek-loop behavior.
4. Demo/deploy MVP increment.

### Incremental Delivery

1. Deliver US1 performance gains.
2. Deliver US2 timestamp parity hardening.
3. Deliver US3 compatibility/fallback guarantees.
4. Complete Phase 6 polish and evidence capture.

### Team Parallelization

1. Team aligns on shared Phase 1/2 foundation.
2. Assign US1, US2, US3 in parallel after Phase 2.
3. Reconcile shared `video_service.py` edits via short-lived branches and frequent rebases.
