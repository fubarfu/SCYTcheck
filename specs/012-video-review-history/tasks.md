# Tasks: Video-Centric Review History

Input: Design documents from /specs/012-video-review-history/
Prerequisites: plan.md, spec.md, research.md, data-model.md, contracts/video-review-history-api.md, quickstart.md

Tests: Include explicit backend unit, contract, integration, and frontend Vitest coverage because the feature relies on deterministic restore, append-only persistence, and lock correctness.

Organization: Tasks are grouped by phase and by user story so each story can be implemented and validated independently.

## Format: [ID] [P?] [Story] Description

---

## Phase 1: Setup (Shared Infrastructure)

Purpose: Prepare scaffolding, fixtures, and stitch references for implementation.

- [X] T001 Confirm and index authoritative Stitch artifacts in specs/012-video-review-history/stitch/README.md
- [X] T002 [P] Create feature fixture builders for workspace, history entries, and lock states in tests/fixtures/review_history_012/__init__.py
- [X] T003 [P] Create contract test scaffold in tests/contract/test_video_review_history_api_012.py
- [X] T004 [P] Create integration test scaffolds in tests/integration/test_review_history_panel_flow_012.py and tests/integration/test_review_history_readonly_lock_012.py
- [X] T005 [P] Create backend unit test scaffolds in tests/unit/test_review_history_snapshots_012.py, tests/unit/test_review_history_restore_012.py, and tests/unit/test_review_lock_behavior_012.py
- [X] T006 [P] Create frontend Vitest scaffolds in src/web/frontend/tests/review/editHistoryPanel.test.tsx and src/web/frontend/tests/review/reviewLockBanner.test.tsx

---

## Phase 2: Foundational (Blocking Prerequisites)

Purpose: Implement shared persistence, lock primitives, and API model changes required by all stories.

Critical: No story work should start before this phase is complete.

- [X] T007 Add or extend review-history and lock entities in src/data/models.py
- [X] T008 [P] Implement per-video append-only history storage service in src/web/app/review_history_store.py
- [X] T009 [P] Implement single-writer lock service with read-only detection in src/web/app/review_lock_service.py
- [X] T010 [P] Extend sidecar/workspace metadata handling for stable video_id folder identity in src/web/app/review_sidecar_store.py
- [X] T011 [P] Add history and lock DTOs in src/web/api/schemas.py
- [X] T012 Wire new history route surface in src/web/api/routes/review_history.py and src/web/api/router.py
- [X] T013 Extend existing review_sessions and review_actions route plumbing for history and lock context in src/web/api/routes/review_sessions.py and src/web/api/routes/review_actions.py
- [X] T014 Add foundational tests for append-only writes, ordering guarantees, and lock invariants in tests/unit/test_review_history_snapshots_012.py and tests/unit/test_review_lock_behavior_012.py
- [X] T014A Define and implement snapshot trigger matrix for state-changing mutations only in src/web/app/review_mutation_service.py and src/web/app/review_history_store.py
- [X] T014B Add negative tests proving no snapshot is created for non-state-changing UI interactions in tests/integration/test_review_history_panel_flow_012.py and tests/unit/test_review_history_snapshots_012.py
- [X] T014C Implement history compaction/compression policy for older entries within the per-video container in src/web/app/review_history_store.py
- [X] T014D Add unit and integration tests for deterministic restore from compressed and uncompressed entries in tests/unit/test_review_history_restore_012.py and tests/integration/test_review_history_panel_flow_012.py

Checkpoint: Shared history and lock primitives are ready for user-story delivery.

---

## Phase 3: User Story 1 - Reopen Prior Review State (Priority P1)

Goal: Show bottom-panel edit history and allow restoring a selected prior snapshot.

Independent test: Load a workspace with multiple history entries, select one entry, and verify restored group and resolution counts match that entry.

### Tests for User Story 1

- [X] T015 [P] [US1] Add contract tests for GET history list and GET history entry payload in tests/contract/test_video_review_history_api_012.py
- [X] T016 [P] [US1] Add integration tests for restore flow and restore provenance snapshot creation in tests/integration/test_review_history_panel_flow_012.py
- [X] T017 [P] [US1] Add Vitest coverage for bottom-panel edit-history rendering and row selection behavior in src/web/frontend/tests/review/editHistoryPanel.test.tsx
- [X] T017A [P] [US1] Add contract and integration coverage for first-save history bootstrap when a video has no history entries in tests/contract/test_video_review_history_api_012.py and tests/integration/test_review_history_panel_flow_012.py

### Implementation for User Story 1

- [X] T018 [US1] Implement ordered history list and entry retrieval endpoints in src/web/api/routes/review_history.py
- [X] T019 [US1] Implement restore endpoint semantics with create_restore_snapshot support in src/web/api/routes/review_history.py and src/web/app/review_history_store.py
- [X] T020 [US1] Add edit-history state actions and selectors in src/web/frontend/src/state/reviewStore.ts
- [X] T021 [US1] Implement EditHistoryPanel component with timestamp, group count, resolved, unresolved, and restore action in src/web/frontend/src/components/EditHistoryPanel.tsx
- [X] T022 [US1] Integrate bottom-panel edit history and restore banner hooks into review screen in src/web/frontend/src/pages/ReviewPage.tsx
- [X] T022A [US1] Implement and wire empty-history panel state message in src/web/frontend/src/components/EditHistoryPanel.tsx and src/web/frontend/src/pages/ReviewPage.tsx

Checkpoint: Prior snapshots are discoverable and restorable with deterministic state reconstruction.

---

## Phase 4: User Story 2 - Keep Video-Centric Data Together (Priority P2)

Goal: Enforce stable video_id workspace identity and keep per-video artifacts as single source of truth.

Independent test: Create or open multiple workspaces and verify each uses stable video_id folder naming and loads only its own artifacts.

### Tests for User Story 2

- [X] T023 [P] [US2] Add unit tests for stable folder identity and title metadata behavior in tests/unit/test_review_history_snapshots_012.py
- [X] T024 [P] [US2] Add integration tests for workspace isolation and source-of-truth loading in tests/integration/test_review_history_panel_flow_012.py

### Implementation for User Story 2

- [X] T025 [US2] Implement stable video_id path resolution and display-title metadata persistence in src/web/app/review_sidecar_store.py
- [X] T026 [US2] Ensure history container path belongs to workspace and is loaded per video_id in src/web/app/review_history_store.py
- [X] T027 [US2] Expose workspace metadata endpoint details in src/web/api/routes/review_history.py and src/web/api/schemas.py
- [X] T027A [US2] Persist and validate per-video analysis runs and candidate payload loading in src/web/app/review_sidecar_store.py and tests/integration/test_review_history_panel_flow_012.py
- [X] T027B [US2] Persist and validate per-video analysis settings, grouping settings, and selection-region configuration in src/web/app/review_sidecar_store.py, src/web/api/routes/review_history.py, and tests/contract/test_video_review_history_api_012.py

Checkpoint: Workspace data ownership is video-centric and stable across renames.

---

## Phase 5: User Story 3 - Preserve Final Reviewed Names (Priority P3)

Goal: Maintain one durable reviewed-name list and keep it consistent through restore and reopen flows.

Independent test: Finalize names, restore an older snapshot, return to latest snapshot, and verify reviewed-name list consistency rules are preserved.

### Tests for User Story 3

- [X] T028 [P] [US3] Add unit tests for reviewed-name list persistence and merge or replace semantics in tests/unit/test_review_history_restore_012.py
- [X] T029 [P] [US3] Add contract tests validating reviewed-name payload shape in history and workspace responses in tests/contract/test_video_review_history_api_012.py

### Implementation for User Story 3

- [X] T030 [US3] Persist reviewed-name list alongside snapshots and workspace metadata in src/web/app/review_history_store.py
- [X] T031 [US3] Ensure restore semantics update active reviewed-name state consistently in src/web/app/review_mutation_service.py and src/web/api/routes/review_history.py
- [X] T032 [US3] Render reviewed-name summary consistency indicators in review page state layer in src/web/frontend/src/state/reviewStore.ts and src/web/frontend/src/pages/ReviewPage.tsx

Checkpoint: Reviewed names remain durable and consistent across history navigation.

---

## Phase 6: Read-Only Lock Behavior (Cross-Story Critical)

Purpose: Deliver lock warning UX and enforce mutation blocking for non-owner sessions.

- [X] T033 [P] Add contract coverage for 409 workspace_locked behavior on mutation endpoints in tests/contract/test_video_review_history_api_012.py
- [X] T034 [P] Add integration coverage for second-session read-only mode and non-blocking inspection in tests/integration/test_review_history_readonly_lock_012.py
- [X] T035 Implement lock checks in mutation paths in src/web/api/routes/review_actions.py and src/web/api/routes/review_history.py
- [X] T036 Implement ReviewLockBanner and disabled control wiring in src/web/frontend/src/components/ReviewLockBanner.tsx and src/web/frontend/src/pages/ReviewPage.tsx

Checkpoint: Single-writer lock and read-only fallback are fully enforced and visible.

---

## Phase 7: Polish and Validation

Purpose: Reconcile with stitch artifacts, run full suite, and finalize implementation notes.

- [X] T037 [P] Run and fix backend unit suite for history, restore, and lock tests in tests/unit/test_review_history_snapshots_012.py, tests/unit/test_review_history_restore_012.py, and tests/unit/test_review_lock_behavior_012.py
- [X] T038 [P] Run and fix contract and integration suites in tests/contract/test_video_review_history_api_012.py, tests/integration/test_review_history_panel_flow_012.py, and tests/integration/test_review_history_readonly_lock_012.py
- [X] T039 [P] Run and fix frontend Vitest suite in src/web/frontend/tests/review/editHistoryPanel.test.tsx and src/web/frontend/tests/review/reviewLockBanner.test.tsx
- [X] T040 Reconcile implementation against 012 Stitch screens and record justified deviations in specs/012-video-review-history/stitch/README.md and specs/012-video-review-history/quickstart.md
- [X] T041 Validate performance targets for restore UI feedback and hydration time at 100, 500, and 1,000 history-entry datasets in tests/integration/test_review_history_panel_flow_012.py
- [X] T042 Execute quickstart manual validation and capture final notes in specs/012-video-review-history/quickstart.md

---

## Dependencies and Execution Order

### Phase dependencies

- Phase 1 starts immediately.
- Phase 2 depends on Phase 1 and blocks all story delivery.
- Phase 3 depends on Phase 2 and delivers MVP behavior.
- Phase 4 depends on Phase 2 and can run in parallel with Phase 3 once shared endpoints exist.
- Phase 5 depends on Phase 2 and should follow once restore semantics are stable.
- Phase 6 depends on Phase 2 and should be completed before final validation.
- Phase 7 depends on all desired stories and lock behavior.

### Story dependencies

- US1 has no dependency on other stories after foundational completion.
- US2 has no dependency on US1 but shares route and persistence infrastructure.
- US3 depends on restore and persistence semantics being implemented.
- Lock behavior is cross-story critical and must be complete before release.

---

## Parallel opportunities

- Setup: T002 to T006 can run in parallel after T001 starts.
- Foundational: T008 to T011 can run in parallel after T007 starts.
- US1 tests T015 to T017 can run in parallel.
- US2 tests T023 and T024 can run in parallel.
- US3 tests T028 and T029 can run in parallel.
- Polish: T037 to T039 can run in parallel.

---

## Implementation strategy

### MVP first

1. Complete Setup and Foundational phases.
2. Deliver US1 bottom-panel history list and restore behavior.
3. Complete read-only lock behavior to protect data integrity.
4. Validate end to end before adding lower-priority refinements.

### Incremental delivery

1. Add US2 workspace identity and source-of-truth hardening.
2. Add US3 reviewed-name durability and consistency behavior.
3. Execute polish, stitch reconciliation, and quickstart validation.