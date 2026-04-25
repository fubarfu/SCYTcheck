# Tasks: Managed Video Analysis History

**Input**: Design documents from /specs/008-manage-video-history/
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/history-api.md, quickstart.md, stitch/README.md

**Tests**: Include explicit unit, contract, and integration tests aligned to quickstart validation flows and history API contract.

**Organization**: Tasks are grouped by phase and by user story so each story can be implemented and validated independently.

## Format: [ID] [P?] [Story] Description

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare test and module scaffolding for feature 008 within the existing repository structure.

- [ ] T001 Create feature-specific history fixtures and sample payload builders in tests/fixtures/history_008/__init__.py
- [ ] T002 [P] Create History API contract test module scaffold in tests/contract/test_history_api_008.py
- [ ] T003 [P] Create History feature integration test module scaffolds in tests/integration/test_history_reopen_flow_008.py and tests/integration/test_history_merge_flow_008.py
- [ ] T004 [P] Create History feature unit test module scaffolds in tests/unit/test_history_merge_logic_008.py and tests/unit/test_history_reopen_resolution_008.py
- [ ] T005 Add history feature settings keys and defaults for index path resolution in src/config.py
- [ ] T006 [P] Add web runtime config entries for history persistence and limits in src/web/app/config.py
- [ ] T007 [P] Create backend history module stubs in src/web/app/history_store.py and src/services/history_service.py
- [ ] T008 [P] Create frontend history module stubs in src/web/frontend/src/pages/HistoryPage.tsx and src/web/frontend/src/state/historyStore.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement core persistence, identity, schema, and routing foundations required by all history user stories.

**CRITICAL**: No user story work should start before this phase is complete.

- [ ] T009 Implement deterministic source canonicalization and merge-key utilities in src/web/app/history_store.py
- [ ] T010 [P] Implement history index read/write with atomic persistence and soft-delete support in src/web/app/history_store.py
- [ ] T011 [P] Extend backend data model types for VideoHistoryEntry/AnalysisRunRecord/PersistedAnalysisContext in src/data/models.py
- [ ] T012 [P] Add history request/response DTO schemas for contract parity in src/web/api/schemas.py
- [ ] T013 Implement shared history service primitives (list/get/delete/merge/reopen context load) in src/services/history_service.py
- [ ] T014 Register history API routes and error mapping in src/web/api/router.py
- [ ] T015 Add foundational unit coverage for persistence guards and schema validation in tests/unit/test_history_foundation_008.py

**Checkpoint**: History foundation ready; user stories can be implemented independently.

---

## Phase 3: User Story 1 - Reopen Prior Analysis Quickly (Priority: P1) 🎯 MVP

**Goal**: Reopen a prior analysis, restore persisted context, and auto-load review artifacts without manual selection.

**Independent Test**: Reopen one history entry and verify automatic Review routing, context restoration, and output-folder-derived result loading, including missing-folder warning behavior.

### Tests for User Story 1

- [ ] T016 [P] [US1] Add unit tests for derived review result resolution states (ready/partial/missing_results/missing_folder) in tests/unit/test_history_reopen_resolution_008.py
- [ ] T017 [P] [US1] Add contract tests for POST /api/history/reopen and GET /api/history/videos/{history_id} in tests/contract/test_history_api_008.py
- [ ] T018 [P] [US1] Add integration test for quickstart Validation Flow A (create and reopen history entry) in tests/integration/test_history_reopen_flow_008.py
- [ ] T019 [P] [US1] Add integration test for quickstart Validation Flow E (missing output folder warning path) in tests/integration/test_history_reopen_missing_folder_008.py

### Implementation for User Story 1

- [ ] T020 [US1] Implement reopen context restore and derived artifact discovery logic in src/services/history_service.py
- [ ] T021 [US1] Implement POST /api/history/reopen and GET /api/history/videos/{history_id} handlers in src/web/api/routes/history.py
- [ ] T022 [US1] Implement frontend reopen action and API client wiring in src/web/frontend/src/state/historyStore.ts
- [ ] T023 [US1] Implement review-session hydration from reopen payload in src/web/frontend/src/state/reviewStore.ts
- [ ] T024 [US1] Implement automatic Review navigation after successful reopen in src/web/frontend/src/App.tsx
- [ ] T025 [US1] Implement non-blocking missing-artifact warning presentation in src/web/frontend/src/pages/ReviewPage.tsx

**Checkpoint**: US1 is independently functional and testable as MVP.

---

## Phase 4: User Story 2 - Merge Repeat Analyses by Video (Priority: P2)

**Goal**: Merge repeat analyses into a single canonical history entry using canonical source + duration identity.

**Independent Test**: Run analysis twice for same canonical source and duration, verify one visible history entry and incremented run_count; verify malformed/missing duration creates potential-duplicate entry.

### Tests for User Story 2

- [ ] T026 [P] [US2] Add unit tests for merge identity rules and duration edge handling in tests/unit/test_history_merge_logic_008.py
- [ ] T027 [P] [US2] Add contract tests for POST /api/history/merge-run behavior and error responses in tests/contract/test_history_api_008.py
- [ ] T028 [P] [US2] Add integration test for quickstart Validation Flow B (deterministic merge and run_count increment) in tests/integration/test_history_merge_flow_008.py
- [ ] T029 [P] [US2] Add integration test for quickstart Validation Flow C (missing/malformed duration creates potential duplicate) in tests/integration/test_history_duration_edge_008.py

### Implementation for User Story 2

- [ ] T030 [US2] Implement merge-run persistence workflow and run append semantics in src/services/history_service.py
- [ ] T031 [US2] Implement POST /api/history/merge-run endpoint in src/web/api/routes/history.py
- [ ] T032 [US2] Wire analysis completion to history merge-run writes in src/web/api/routes/analysis.py and src/web/app/analysis_adapter.py
- [ ] T033 [US2] Persist latest analysis context snapshot during merge in src/services/analysis_service.py
- [ ] T034 [US2] Add potential-duplicate metadata propagation into API responses in src/web/api/schemas.py

**Checkpoint**: US2 merge behavior is independently functional and testable.

---

## Phase 5: User Story 3 - Maintain Analysis History List (Priority: P3)

**Goal**: Provide a dedicated History view with list, reopen, and delete actions while preserving output files on disk.

**Independent Test**: Open History view, verify list rendering, delete one entry, reopen another, and confirm deleted entry is removed from list only.

### Tests for User Story 3

- [ ] T035 [P] [US3] Add contract tests for GET /api/history/videos and DELETE /api/history/videos/{history_id} in tests/contract/test_history_api_008.py
- [ ] T036 [P] [US3] Add integration test for quickstart Validation Flow D (delete behavior without file deletion) in tests/integration/test_history_delete_flow_008.py
- [ ] T037 [P] [US3] Add integration test for history management view list/delete/reopen journey in tests/integration/test_history_management_view_008.py
- [ ] T038 [P] [US3] Add unit tests for history list ordering, filtering, and soft-delete exclusion in tests/unit/test_history_list_behavior_008.py

### Implementation for User Story 3

- [ ] T039 [US3] Implement GET /api/history/videos and DELETE /api/history/videos/{history_id} handlers in src/web/api/routes/history.py
- [ ] T040 [US3] Implement History page container and view-state orchestration in src/web/frontend/src/pages/HistoryPage.tsx
- [ ] T041 [US3] Implement reusable history entry row/card actions (reopen/delete/potential-duplicate badge) in src/web/frontend/src/components/HistoryEntryRow.tsx
- [ ] T042 [US3] Implement history list/load/delete/reopen store actions and API bindings in src/web/frontend/src/state/historyStore.ts
- [ ] T043 [US3] Add third-view navigation and route integration for History in src/web/frontend/src/App.tsx
- [ ] T044 [US3] Apply Stitch-aligned layout/token updates for History integration in src/web/frontend/src/styles/app.css and src/web/frontend/src/styles/theme.css
- [ ] T045 [US3] Consume and trace Stitch artifacts during frontend implementation by mapping structure from specs/008-manage-video-history/stitch/analysis-view.html, specs/008-manage-video-history/stitch/review-view.html, and specs/008-manage-video-history/stitch/frame-thumbnail-modal-overlay.html into UI notes in specs/008-manage-video-history/stitch/README.md

**Checkpoint**: US3 history management view is independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, performance checks, and documentation for feature 008.

- [ ] T046 [P] Run and fix full history contract suite for feature endpoints in tests/contract/test_history_api_008.py
- [ ] T047 [P] Run and fix full history integration suite aligned to quickstart flows A-E in tests/integration/test_history_reopen_flow_008.py, tests/integration/test_history_merge_flow_008.py, tests/integration/test_history_duration_edge_008.py, tests/integration/test_history_delete_flow_008.py, and tests/integration/test_history_reopen_missing_folder_008.py
- [ ] T048 [P] Add and validate history list/reopen performance checks (<=200ms list interactions, <=5s reopen-ready) in tests/integration/test_history_performance_008.py
- [ ] T049 Reconcile implementation against Stitch authority and document any justified deviations in specs/008-manage-video-history/quickstart.md
- [ ] T050 Execute end-to-end feature verification and capture final notes in specs/008-manage-video-history/quickstart.md and tests/integration/test_all_features_combined.py

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 (Setup): Starts immediately.
- Phase 2 (Foundational): Depends on Phase 1 and blocks all user stories.
- Phase 3 (US1): Depends on Phase 2 and delivers MVP.
- Phase 4 (US2): Depends on Phase 2 and can proceed after US1 baseline routes are available.
- Phase 5 (US3): Depends on Phase 2 and can proceed after core history endpoints exist.
- Phase 6 (Polish): Depends on completion of desired user stories.

### User Story Dependencies

- US1 (P1): No dependency on other stories after foundational completion.
- US2 (P2): Depends on foundational history persistence and analysis completion wiring.
- US3 (P3): Depends on foundational history list/delete/reopen endpoint availability.

### Within Each User Story

- Tests first, confirm failing expectations before implementation.
- Backend service logic before API handlers.
- API handlers before frontend store and UI wiring.
- Story checkpoint validation before advancing to next story.

---

## Parallel Opportunities

- Setup: T002, T003, and T004 can run in parallel.
- Foundational: T010, T011, T012 can run in parallel after T009 starts; T015 can run in parallel after T012.
- US1: T016, T017, T018, and T019 can run in parallel.
- US2: T026, T027, T028, and T029 can run in parallel.
- US3: T035, T036, T037, and T038 can run in parallel.
- Polish: T046, T047, and T048 can run in parallel.

---

## Parallel Example: User Story 1

```bash
# Parallel test authoring for US1
Task: "T016 Add unit tests in tests/unit/test_history_reopen_resolution_008.py"
Task: "T017 Add contract tests in tests/contract/test_history_api_008.py"
Task: "T018 Add integration test in tests/integration/test_history_reopen_flow_008.py"
Task: "T019 Add integration test in tests/integration/test_history_reopen_missing_folder_008.py"
```

## Parallel Example: User Story 3

```bash
# Parallel frontend implementation after history routes are stable
Task: "T040 Implement page container in src/web/frontend/src/pages/HistoryPage.tsx"
Task: "T041 Implement row/card component in src/web/frontend/src/components/HistoryEntryRow.tsx"
Task: "T044 Apply style updates in src/web/frontend/src/styles/app.css and src/web/frontend/src/styles/theme.css"
```

---

## Implementation Strategy

### MVP First (US1)

1. Complete Setup and Foundational phases.
2. Implement US1 reopen + review auto-load behavior.
3. Validate quickstart Flow A and Flow E before expanding scope.

### Incremental Delivery

1. Add US2 deterministic merge behavior and verify no duplicate entries.
2. Add US3 history management UI for list/delete/reopen.
3. Execute polish/performance validation and Stitch reconciliation notes.

### Scope Guardrails

- Limit changes to feature 008 contracts, docs, backend modules, frontend modules, and tests listed above.
- Do not introduce unrelated refactors outside history persistence, API, and view integration paths.
