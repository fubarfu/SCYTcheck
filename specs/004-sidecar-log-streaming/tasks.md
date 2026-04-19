# Tasks: Continuous Sidecar Log Writing

**Feature**: `004-sidecar-log-streaming`  
**Branch**: `006-sidecar-log-streaming`  
**Date**: 2026-04-14  
**Input**: [spec.md](spec.md), [plan.md](plan.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [research.md](research.md)

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no incomplete task dependencies)
- **[US#]**: User story this task belongs to (Phase 3+ only)
- Each task includes exact file path

---

## Phase 1: Setup

**Purpose**: No new project structure is required. All changes target existing files. This phase verifies the baseline is clean before modification.

- [X] T001 Confirm existing tests pass before any changes: run `pytest tests/unit/test_analysis_service.py tests/unit/test_export_service.py` and record baseline status

---

## Phase 2: Foundational — SidecarLogWriter class

**Purpose**: Implement the `SidecarLogWriter` context manager in `src/services/logging.py`. This is the foundational building block that both US1 and US2 depend on. All other story phases require this to be complete first.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 Add `SidecarLogWriter` class to `src/services/logging.py`: implement `__init__(output_folder: str, summary_filename: str)` storing `_folder` and deriving `_path` via `sidecar_log_name()`; set `_handle` and `_writer` to `None`
- [X] T003 Implement `__enter__` on `SidecarLogWriter` in `src/services/logging.py`: create output folder, open file in `"w"` mode with `newline=""` and `encoding="utf-8"`, create `csv.writer`, write `LOG_HEADERS` row, call `flush()`, return `self`
- [X] T004 Implement `__exit__` on `SidecarLogWriter` in `src/services/logging.py`: close `_handle` unconditionally (even when `exc_type` is not `None`), reset `_handle` and `_writer` to `None`; do not suppress exceptions
- [X] T005 Implement `write_record(record: LogRecord) -> None` on `SidecarLogWriter` in `src/services/logging.py`: write one CSV row matching the existing `write_sidecar_log()` field order, call `flush()`; wrap in `try/except OSError` and log a `WARNING` on failure without re-raising
- [X] T006 [P] Write unit tests for `SidecarLogWriter` in `tests/unit/test_export_service.py`: test that `__enter__` creates the file with header-only content; test that `write_record()` appends one data row and flushes; test that `__exit__` closes the file; test that an `OSError` in `write_record()` is swallowed and does not raise

**Checkpoint**: `SidecarLogWriter` is fully implemented and unit-tested. It is not yet wired into analysis.

---

## Phase 3: User Story 1 — Partial Log Preserved on Interruption (Priority: P1) 🎯 MVP

**Goal**: When analysis is interrupted at any point, the sidecar log on disk contains every entry generated up to that moment.

**Independent Test**: Run analysis with `logging_enabled=True`; interrupt mid-run; verify log file contains all pre-interruption entries with correct header.

### Implementation for User Story 1

- [X] T007 [US1] Add `on_log_record: Callable[[LogRecord], None] | None = None` parameter to `AnalysisService.analyze()` in `src/services/analysis_service.py` (append after `logging_enabled`; no other changes to signature or existing behaviour)
- [X] T008 [US1] In `AnalysisService.analyze()` in `src/services/analysis_service.py`: after every `analysis.add_log_record(record)` call (there are three such call sites in the frame loop and one post-loop site), add `if on_log_record is not None: on_log_record(record)` immediately after each
- [X] T009 [US1] In `src/main.py` `run_analysis_worker()`: import `contextlib`; replace the `write_sidecar_log(...)` call at the end of `run_analysis_worker()` with a `SidecarLogWriter` context wrapping the `analysis_service.analyze()` call; pass `on_log_record=writer.write_record` when `advanced.logging_enabled` is true, `None` otherwise; use `contextlib.nullcontext()` when logging is disabled (so the `with` block is unconditional)
- [X] T010 [US1] Extend `tests/unit/test_analysis_service.py`: add test that invokes `analyze()` with a list-append callback as `on_log_record` and asserts the callback was called once for every record in `analysis.log_records`

**Checkpoint**: User Story 1 is complete. Analysis with sidecar log enabled now streams to disk. Interrupting analysis leaves the log intact with all pre-interruption entries.

---

## Phase 4: User Story 2 — Log Visible in Real Time (Priority: P2)

**Goal**: An external observer reading the log file during a running analysis sees entries appear incrementally, not only after the run ends.

**Independent Test**: Open the log file in a text editor mid-analysis and confirm previously-processed-frame entries are already present.

**Note**: US2 is delivered by the same implementation as US1 (each `write_record()` call flushes to disk immediately). No additional code changes are required. This phase validates the requirement explicitly.

### Implementation for User Story 2

- [X] T011 [P] [US2] Add a unit test to `tests/unit/test_export_service.py` that verifies `SidecarLogWriter.write_record()` calls `flush()` after each individual write (use `unittest.mock.patch` on the file handle's `flush` method and assert it was called once per `write_record()` invocation)
- [X] T012 [P] [US2] Add an integration test to `tests/integration/test_log_schema_fr049.py` (or a new `tests/integration/test_sidecar_streaming.py`) that runs a minimal fake analysis with 3 log records via `on_log_record`, interrupts after the first record is written, then reads the file and asserts exactly 1 data row plus header is present

**Checkpoint**: User Story 2 validated. The flush-per-write behaviour is explicitly tested; real-time observability is confirmed by the interruption integration test.

---

## Phase 5: User Story 3 — No Regression When Sidecar Log Is Inactive (Priority: P3)

**Goal**: When `logging_enabled` is `False`, no sidecar log file is created or written.

**Independent Test**: Run a complete analysis with `logging_enabled=False`; assert no `_log.csv` file is created in the output folder.

### Implementation for User Story 3

- [X] T013 [P] [US3] Add a unit test to `tests/unit/test_analysis_service.py` that runs `analyze()` with `logging_enabled=False` and `on_log_record=None`; asserts that no `_log.csv` file was created and `analysis.log_records` is empty
- [X] T014 [P] [US3] Verify in `tests/unit/test_export_service.py` that constructing a `SidecarLogWriter` but never entering its context (no `with` statement) does not create any file

**Checkpoint**: All three user stories complete. Regression scenario confirmed.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T015 [P] Update `src/main.py` import line: add `import contextlib` (or verify it is already imported); add `SidecarLogWriter` to the import from `src.services.logging`
- [X] T016 Remove the now-redundant `write_sidecar_log` call from the `retry_export()` path in `src/main.py` **only if** the retry path is also updated to use `SidecarLogWriter`; otherwise leave as-is (batch write on retry is by design per research.md)
- [X] T017 Run full test suite: `pytest tests/unit/ tests/integration/test_log_schema_fr049.py` and confirm all pre-existing tests still pass
- [X] T018 [P] Validate output against `quickstart.md` acceptance criteria table: confirm all FR-001 through FR-007 items are covered by implemented code or tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks** all user story phases
- **Phase 3 (US1 P1)**: Depends on Phase 2 — MVP; implement first
- **Phase 4 (US2 P2)**: Depends on Phase 2 — validation-only; can run after Phase 3 in parallel with Phase 5
- **Phase 5 (US3 P3)**: Depends on Phase 2 — regression tests; can run after Phase 3 in parallel with Phase 4
- **Phase 6 (Polish)**: Depends on all user story phases

### User Story Dependencies

- **US1 (P1)**: Foundational phase complete → US1 is core code change
- **US2 (P2)**: No additional code beyond US1; validation tasks only; can run immediately after US1
- **US3 (P3)**: Regression tests only; independent of US1 and US2 code

### Parallel Opportunities

Within **Phase 2**: T002 → T003 → T004 → T005 must be sequential (class build-up); T006 can start in parallel once `write_record()` spec is known.

Within **Phase 3**: T007 → T008 must be sequential; T009 and T010 can run in parallel after T008.

Within **Phase 4–5**: T011, T012, T013, T014 are all marked [P] and can run simultaneously.

---

## Parallel Example: Phase 2 + Phase 3

```
T001
 └─> T002 → T003 → T004 → T005
                           ├─> T006 [P]
                           └─> T007 → T008
                                       ├─> T009
                                       └─> T010 [P]
                                            └─> T011 [P] T012 [P] T013 [P] T014 [P]
                                                              └─> T015 → T016 → T017 → T018 [P]
```

---

## Implementation Strategy

**MVP Scope**: Complete Phases 1–3 (T001–T010). This delivers US1 (P1) — the entire core value of the feature — with no UI changes and no new dependencies.

**Incremental delivery**:
1. Phase 2 alone (T002–T006) is safe to commit; `SidecarLogWriter` has no callers yet, existing behavior unchanged.
2. T007+T008 alone are safe; the new `on_log_record` param defaults to `None` so all existing callers are unaffected.
3. T009 is the switchover; the batch write is replaced by the streaming write. This is the only breaking change point.

**Total tasks**: 18  
**Parallelizable**: T006, T009 (after T008), T010, T011, T012, T013, T014, T015, T018
