# Tasks: Collapsable Review Groups with Player Name Management

**Input**: Design documents from `/specs/010-collapse-player-groups/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/review-groups-api.md, quickstart.md

**Tests**: Include explicit backend unit, contract, integration, and frontend Vitest coverage because the specification and plan require validation of consensus logic, duplicate prevention, persistence, and review UI behavior.

**Organization**: Tasks are grouped by phase and by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare test scaffolding, authoritative Stitch exports, and review-group feature anchors inside the existing web review stack.

- [ ] T001 Export and document authoritative Stitch artifacts for the review-group states in `specs/010-collapse-player-groups/stitch/README.md`, `specs/010-collapse-player-groups/stitch/review-candidate-groups.html`, `specs/010-collapse-player-groups/stitch/review-validation-error-state.html`, and `specs/010-collapse-player-groups/stitch/review-expanded-candidate-group.html`
- [ ] T002 [P] Create feature-specific review-group fixtures and payload builders in `tests/fixtures/review_groups_010/__init__.py`
- [ ] T003 [P] Create review-group contract test scaffold in `tests/contract/test_review_groups_api_010.py`
- [ ] T004 [P] Create review-group integration test scaffolds in `tests/integration/test_review_groups_consensus_flow_010.py`, `tests/integration/test_review_groups_conflict_flow_010.py`, `tests/integration/test_review_groups_validation_flow_010.py`, and `tests/integration/test_review_groups_toggle_persistence_010.py`
- [ ] T005 [P] Create backend unit test scaffolds for foundation, mutation, and uniqueness coverage in `tests/unit/test_review_group_foundation_010.py`, `tests/unit/test_review_group_mutations_010.py`, and `tests/unit/test_review_group_uniqueness_010.py`
- [ ] T006 [P] Create frontend Vitest scaffolds for group card, candidate row, and review store behavior in `src/web/frontend/tests/review/CandidateGroupCard.test.tsx`, `src/web/frontend/tests/review/CandidateRow.test.tsx`, and `src/web/frontend/tests/review/reviewStore.test.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement the shared sidecar schema, grouping primitives, mutation logic, and API surfaces required by every review-group story.

**CRITICAL**: No user story work should start before this phase is complete.

- [ ] T007 Extend persisted review-session data structures for accepted names, rejected candidates, collapse state, and resolution status in `src/data/models.py`
- [ ] T008 [P] Implement review-group sidecar read/write helpers for accepted-name, rejection, and collapse-state persistence in `src/web/app/review_sidecar_store.py`
- [ ] T009 [P] Implement exact-match consensus recompute utilities and resolved/unresolved grouping state in `src/web/app/review_grouping.py`
- [ ] T010 [P] Implement review-group mutation and uniqueness-validation primitives for confirm, reject, undo, and duplicate detection in `src/web/app/group_mutation_service.py`
- [ ] T011 [P] Add request and response DTOs for review sessions, group toggles, candidate confirmations, and validation feedback in `src/web/api/schemas.py`
- [ ] T012 Wire review-group routes and session payload mapping into `src/web/api/routes/review_sessions.py`, `src/web/api/routes/review_actions.py`, and `src/web/api/router.py`
- [ ] T013 Add foundational test coverage for sidecar persistence, grouping recompute guards, and schema parity in `tests/unit/test_review_group_foundation_010.py`

**Checkpoint**: Review-group foundations are ready; user stories can now be implemented and validated independently.

---

## Phase 3: User Story 1 - View Collapsed Groups with Consensus Names (Priority: P1) 🎯 MVP

**Goal**: Show consensus groups collapsed by default with the accepted name visible and expandable on demand.

**Independent Test**: Load a review session containing identical-name groups and verify those groups render collapsed by default, display the consensus name, and expand to reveal the full occurrence list and metadata.

### Tests for User Story 1

- [ ] T014 [P] [US1] Add Vitest coverage for default-collapsed resolved-group rendering and expand interaction in `src/web/frontend/tests/review/CandidateGroupCard.test.tsx`
- [ ] T015 [P] [US1] Add integration coverage for default-collapsed consensus groups and metadata reveal in `tests/integration/test_review_groups_consensus_flow_010.py`

### Implementation for User Story 1

- [ ] T016 [US1] Expose resolved-group summary fields and collapsed consensus state from the session loader in `src/web/api/routes/review_sessions.py` and `src/web/api/schemas.py`
- [ ] T017 [US1] Implement collapsed resolved-group header, accepted-name summary, and expand affordance in `src/web/frontend/src/components/CandidateGroupCard.tsx`
- [ ] T018 [US1] Render identical candidate occurrences and occurrence metadata for expanded resolved groups in `src/web/frontend/src/components/CandidateRow.tsx`
- [ ] T019 [US1] Wire collapsed consensus groups into review-page rendering and derived selectors in `src/web/frontend/src/pages/ReviewPage.tsx` and `src/web/frontend/src/state/reviewSelectors.ts`

**Checkpoint**: Consensus groups are independently visible, collapsed by default, and expandable with full context.

---

## Phase 4: User Story 2 - View Expanded Groups with Conflicting Names (Priority: P1)

**Goal**: Show conflicting groups expanded by default, visually emphasize unresolved status, and remember manual collapse changes during the session.

**Independent Test**: Load a review session with mixed spellings and verify conflict groups open by default, unresolved styling is visible, and a manual collapse or re-expand action persists across subsequent interactions.

### Tests for User Story 2

- [ ] T020 [P] [US2] Add Vitest coverage for unresolved-group default-open state and manual toggle behavior in `src/web/frontend/tests/review/CandidateGroupCard.test.tsx`
- [ ] T021 [P] [US2] Add integration coverage for conflicting groups default-open hydration and toggle persistence in `tests/integration/test_review_groups_conflict_flow_010.py`

### Implementation for User Story 2

- [ ] T022 [US2] Extend grouping/session payload generation with active spellings, unresolved status, and remembered toggle state in `src/web/app/review_grouping.py` and `src/web/api/routes/review_sessions.py`
- [ ] T023 [US2] Implement unresolved-group header styling, chevron toggle, and conflict summary in `src/web/frontend/src/components/CandidateGroupCard.tsx`
- [ ] T024 [US2] Persist manual collapse and expand actions through the review action handler and sidecar store in `src/web/api/routes/review_actions.py` and `src/web/app/review_sidecar_store.py`
- [ ] T025 [US2] Update review-page and store wiring for per-group toggle state and default-open conflict hydration in `src/web/frontend/src/pages/ReviewPage.tsx` and `src/web/frontend/src/state/reviewStore.ts`

**Checkpoint**: Conflict groups are independently highlighted, expanded by default, and manually toggleable with remembered state.

---

## Phase 5: User Story 3 - Confirm Candidates and Achieve Consensus (Priority: P1)

**Goal**: Let the reviewer confirm a candidate with radio-button selection, reject or undo rejected candidates, and auto-collapse a group when consensus is achieved.

**Independent Test**: Resolve a conflicting group by confirming one candidate or rejecting alternates, verify the accepted candidate is visually marked, and confirm the group auto-collapses once only identical non-rejected names remain.

### Tests for User Story 3

- [ ] T026 [P] [US3] Add backend unit coverage for confirm, reject, un-reject, and consensus-transition rules in `tests/unit/test_review_group_mutations_010.py`
- [ ] T027 [P] [US3] Add contract coverage for confirm, reject, deselect, and undo review-group actions in `tests/contract/test_review_groups_api_010.py`
- [ ] T028 [P] [US3] Add Vitest coverage for radio-button selection, explicit deselection, success feedback, and rejected-candidate rendering in `src/web/frontend/tests/review/CandidateRow.test.tsx`

### Implementation for User Story 3

- [ ] T029 [US3] Implement confirm, reject, deselect, and un-reject mutation semantics plus accepted-name updates in `src/web/app/group_mutation_service.py` and `src/web/api/routes/review_actions.py`
- [ ] T030 [US3] Persist accepted-name changes and auto-collapse-on-consensus behavior in `src/web/app/review_sidecar_store.py` and `src/web/api/routes/review_sessions.py`
- [ ] T031 [US3] Create shared inline feedback rendering for successful confirmations in `src/web/frontend/src/components/ValidationFeedback.tsx`
- [ ] T032 [US3] Implement candidate-level radio-button selection, reject or undo affordances, and success-state styling in `src/web/frontend/src/components/CandidateRow.tsx`
- [ ] T033 [US3] Reconcile accepted-name, rejected-candidate, and auto-collapse transitions into client state in `src/web/frontend/src/state/reviewStore.ts` and `src/web/frontend/src/state/reviewSelectors.ts`

**Checkpoint**: Reviewers can independently resolve groups, see confirmation feedback, and watch groups auto-collapse on consensus.

---

## Phase 6: User Story 4 - Prevent Duplicate Accepted Names Across Groups (Priority: P1)

**Goal**: Block duplicate accepted names across groups and surface clear inline error feedback with the conflicting group reference.

**Independent Test**: Confirm a name in one group, attempt to confirm the same name in a second group, verify the action is rejected, and confirm the reviewer sees a clear inline error that references the conflicting group until a different action is taken.

### Tests for User Story 4

- [ ] T034 [P] [US4] Add backend unit coverage for duplicate accepted-name detection and conflict payload generation in `tests/unit/test_review_group_uniqueness_010.py`
- [ ] T035 [P] [US4] Extend contract coverage for duplicate-name validation failures and conflicting-group references in `tests/contract/test_review_groups_api_010.py`
- [ ] T036 [P] [US4] Add integration coverage for cross-group duplicate prevention and rollback of invalid selections in `tests/integration/test_review_groups_validation_flow_010.py`

### Implementation for User Story 4

- [ ] T037 [US4] Implement backend uniqueness checks and conflicting-group lookup for review actions in `src/web/app/group_mutation_service.py` and `src/web/api/routes/review_actions.py`
- [ ] T038 [US4] Add validation result DTOs and failed-action response payloads for duplicate-name feedback in `src/web/api/schemas.py` and `src/web/api/routes/review_actions.py`
- [ ] T039 [US4] Extend `src/web/frontend/src/components/ValidationFeedback.tsx` to render inline duplicate-name errors and hints from the API payload
- [ ] T040 [US4] Surface duplicate-name errors, conflicting-group references, and selection rollback in `src/web/frontend/src/components/CandidateRow.tsx` and `src/web/frontend/src/pages/ReviewPage.tsx`

**Checkpoint**: Duplicate accepted names are independently blocked with persistent inline feedback and clear conflict context.

---

## Phase 7: User Story 5 - Manage Collapse State for Resolved Groups (Priority: P2)

**Goal**: Let users manually collapse or expand resolved groups and preserve mixed collapse states during the review session.

**Independent Test**: Toggle resolved groups individually, reload the session, and verify the review UI restores the same mixed collapse states.

### Tests for User Story 5

- [ ] T041 [P] [US5] Add Vitest coverage for resolved-group manual toggle persistence in `src/web/frontend/tests/review/CandidateGroupCard.test.tsx` and `src/web/frontend/tests/review/reviewStore.test.ts`
- [ ] T042 [P] [US5] Add integration coverage for persisted mixed collapse states across session reload in `tests/integration/test_review_groups_toggle_persistence_010.py`

### Implementation for User Story 5

- [ ] T043 [US5] Implement persisted per-group toggle state and reload hydration for resolved groups in `src/web/app/review_sidecar_store.py` and `src/web/api/routes/review_sessions.py`
- [ ] T044 [US5] Add resolved-group manual toggle controls and associated review actions in `src/web/frontend/src/pages/ReviewPage.tsx` and `src/web/frontend/src/components/CandidateGroupCard.tsx`
- [ ] T045 [US5] Preserve mixed collapse states after confirm, reject, undo, and reload flows in `src/web/frontend/src/state/reviewStore.ts` and `src/web/frontend/src/state/reviewSelectors.ts`

**Checkpoint**: Resolved-group layout control is independently functional and survives session reloads.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Reconcile the implementation against the approved Stitch artifacts, run the full validation matrix, and capture end-to-end notes.

- [ ] T046 [P] Run and fix the backend unit suite for review-group foundation, mutation, and uniqueness behavior in `tests/unit/test_review_group_foundation_010.py`, `tests/unit/test_review_group_mutations_010.py`, and `tests/unit/test_review_group_uniqueness_010.py`
- [ ] T047 [P] Run and fix the review-group contract and integration suites in `tests/contract/test_review_groups_api_010.py`, `tests/integration/test_review_groups_consensus_flow_010.py`, `tests/integration/test_review_groups_conflict_flow_010.py`, `tests/integration/test_review_groups_validation_flow_010.py`, and `tests/integration/test_review_groups_toggle_persistence_010.py`
- [ ] T048 [P] Run and fix the frontend Vitest suite for review-group UI behavior in `src/web/frontend/tests/review/CandidateGroupCard.test.tsx`, `src/web/frontend/tests/review/CandidateRow.test.tsx`, and `src/web/frontend/tests/review/reviewStore.test.ts`
- [ ] T049 Reconcile implementation against the approved Stitch screens and document any justified deviations in `specs/010-collapse-player-groups/stitch/README.md` and `specs/010-collapse-player-groups/quickstart.md`
- [ ] T050 Execute the quickstart end-to-end validation flow and capture final implementation notes in `specs/010-collapse-player-groups/quickstart.md`
- [ ] T051 [P] Add backend export-gate checks that reject export when any group is unresolved or accepted names are duplicated in `tests/contract/test_review_groups_api_010.py` and `tests/integration/test_review_groups_validation_flow_010.py`
- [ ] T052 Implement completion/export gating rules in `src/web/api/routes/review_export.py` and `src/web/app/group_mutation_service.py` to satisfy FR-021 and SC-006/SC-008
- [ ] T053 [P] Add integration timing assertions for SC-003 (resolve under 10s simulated workflow) and SC-003b (validation feedback under 500ms) in `tests/integration/test_review_groups_consensus_flow_010.py` and `tests/integration/test_review_groups_validation_flow_010.py`
- [ ] T054 [P] Add frontend perf timing checks for validation response and toggle latency in `src/web/frontend/tests/review/perfBenchmark.test.tsx`
- [ ] T055 Document completion/export gate behavior and timing measurement procedure in `specs/010-collapse-player-groups/quickstart.md`
- [ ] T056 [P] Add explicit recovery test for the all-candidates-rejected edge case (user must recover by unreject/select before export) in `tests/integration/test_review_groups_validation_flow_010.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 and delivers the MVP baseline for resolved groups.
- **Phase 4 (US2)**: Depends on Phase 2 and can proceed in parallel with US1 once foundational payloads exist.
- **Phase 5 (US3)**: Depends on Phase 2 and builds the core resolution workflow used by later validation.
- **Phase 6 (US4)**: Depends on Phase 2 and should follow once confirm-selection semantics are in place.
- **Phase 7 (US5)**: Depends on Phase 2 and can proceed after group toggle persistence exists.
- **Phase 8 (Polish)**: Depends on completion of the desired user stories.

### User Story Dependencies

- **US1 (P1)**: No dependency on other stories after foundational completion.
- **US2 (P1)**: No dependency on other stories after foundational completion.
- **US3 (P1)**: Depends on foundational mutation and session payload support but does not require US1 or US2 to be fully complete.
- **US4 (P1)**: Depends on US3 confirm-selection behavior to validate and reject duplicate accepted names.
- **US5 (P2)**: Depends on foundational toggle persistence and integrates cleanly after US1 or US2 group rendering is in place.

### Within Each User Story

- Tests first, confirm failing expectations before implementation.
- Backend mutation or grouping logic before route wiring.
- Route payloads before frontend state and UI wiring.
- Story checkpoint validation before advancing to the next priority.

---

## Parallel Opportunities

- Setup: T002, T003, T004, T005, and T006 can run in parallel after T001 starts.
- Foundational: T008, T009, T010, and T011 can run in parallel after T007 starts; T013 follows the shared primitives.
- US1: T014 and T015 can run in parallel.
- US2: T020 and T021 can run in parallel.
- US3: T026, T027, and T028 can run in parallel.
- US4: T034, T035, and T036 can run in parallel.
- US5: T041 and T042 can run in parallel.
- Polish: T046, T047, and T048 can run in parallel.

---

## Parallel Example: User Story 3

```bash
# Parallel test authoring for US3
Task: "T026 Add backend unit coverage in tests/unit/test_review_group_mutations_010.py"
Task: "T027 Add contract coverage in tests/contract/test_review_groups_api_010.py"
Task: "T028 Add Vitest coverage in src/web/frontend/tests/review/CandidateRow.test.tsx"
```

## Parallel Example: User Story 4

```bash
# Parallel duplicate-prevention validation work
Task: "T034 Add backend uniqueness tests in tests/unit/test_review_group_uniqueness_010.py"
Task: "T035 Extend contract duplicate-name coverage in tests/contract/test_review_groups_api_010.py"
Task: "T036 Add integration duplicate-prevention coverage in tests/integration/test_review_groups_validation_flow_010.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Setup and Foundational phases.
2. Implement US1 collapsed consensus rendering.
3. Implement US2 conflict-group expansion and toggle persistence.
4. Implement US3 confirm or reject workflow and auto-collapse on consensus.
5. Validate the review workflow before adding duplicate prevention and batch layout controls.

### Incremental Delivery

1. Add US4 duplicate accepted-name prevention and inline validation feedback.
2. Add US5 resolved-group manual layout controls and reload persistence.
3. Execute polish, Stitch reconciliation, and quickstart validation.

### Scope Guardrails

- Keep changes within the review-view files, sidecar persistence helpers, API schemas and routes, and the tests listed above.
- Preserve the existing CSV export format; only sidecar JSON and in-memory review payloads change.
- Treat the approved Stitch artifacts in `specs/010-collapse-player-groups/stitch/` as authoritative for UI layout and feedback states.