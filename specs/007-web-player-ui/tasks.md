# Tasks: Web-Based Player Name Verification UI

**Input**: Design documents from /specs/007-web-player-ui/
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish project scaffolding for local web runtime and Stitch-aligned frontend source layout.

- [ ] T001 Create frontend source scaffold (components, pages, styles, state) in src/web/frontend/src/
- [ ] T002 Create frontend package scripts and dependencies for build/test in src/web/frontend/package.json
- [ ] T003 [P] Create shared frontend TypeScript config in src/web/frontend/tsconfig.json
- [ ] T004 [P] Create frontend build config and entry wiring in src/web/frontend/vite.config.ts
- [ ] T005 Create backend web app bootstrap module for localhost serving in src/web/app/server.py
- [ ] T006 [P] Add web app startup configuration defaults in src/web/app/config.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared contracts, persistence primitives, and core infrastructure required by all stories.

**CRITICAL**: No user story work starts before this phase is done.

- [ ] T007 Implement API DTOs and validation schemas from contracts in src/web/api/schemas.py
- [ ] T008 [P] Implement settings repository for scytcheck_settings.json read/write in src/web/app/settings_store.py
- [ ] T009 [P] Implement review sidecar JSON repository with atomic writes in src/web/app/review_sidecar_store.py
- [ ] T010 [P] Implement result CSV schema/version validator in src/web/app/result_schema_validator.py
- [ ] T011 Implement in-memory session manager and lifecycle registry in src/web/app/session_manager.py
- [ ] T012 [P] Implement thumbnail/frame asset resolver and cache path rules in src/web/app/frame_asset_store.py
- [ ] T013 Implement API route registration and shared error mapping in src/web/api/router.py
- [ ] T014 Add cross-cutting backend tests for schema validator and sidecar atomicity in tests/unit/test_review_foundation_007.py

**Checkpoint**: Core infrastructure complete; story phases can begin.

---

## Phase 3: User Story 0 - Launch App to Web UI (Priority: P0)

**Goal**: Portable executable launches local server and opens browser on Analysis view without manual steps.

**Independent Test**: Start app via launcher, verify localhost opens to Analysis within 5 seconds, rerun behavior avoids port conflict errors.

### Tests for User Story 0

- [ ] T015 [P] [US0] Add integration test for launcher opening localhost Analysis view in tests/integration/test_web_launch_007.py
- [ ] T016 [P] [US0] Add integration test for rerun behavior when server already running in tests/integration/test_web_launch_rerun_007.py

### Implementation for User Story 0

- [ ] T017 [US0] Implement single-instance startup and browser-open flow in src/web/app/launcher.py
- [ ] T018 [US0] Implement fallback port-detection and tab-open behavior in src/web/app/server.py
- [ ] T019 [US0] Implement top-level Analysis/Review navigation shell in src/web/frontend/src/App.tsx (Stitch: 860c4f4ace1a440f871b8de136d04b33)
- [ ] T020 [US0] Add route-level smoke checks for navigation without reload in tests/integration/test_web_navigation_007.py

**Checkpoint**: App launch path and view navigation independently functional.

---

## Phase 4: User Story 1 - Configure and Run Analysis (Priority: P1)

**Goal**: Full Analysis view parity with legacy controls, source selection, region selection, run/stop, and live progress.

**Independent Test**: Configure settings, start run, observe live progress, stop run, and verify partial result availability.

### Tests for User Story 1

- [ ] T021 [P] [US1] Add contract tests for settings and analysis endpoints in tests/contract/test_analysis_api_007.py
- [ ] T022 [P] [US1] Add integration test for full Analysis view parity controls in tests/integration/test_analysis_parity_controls_007.py
- [ ] T023 [P] [US1] Add integration test for start/progress/stop flow in tests/integration/test_analysis_run_stop_007.py

### Implementation for User Story 1

- [ ] T024 [US1] Implement GET/PUT settings endpoints from analysis contract in src/web/api/routes/settings.py
- [ ] T075 [US1] Implement analysis adapter bridge: async wrapper around existing src/services/analysis_service.py that runs analysis in a background thread, exposes run_id state model with progress/cancel signals, and bridges service callbacks to the FastAPI polling contract in src/web/app/analysis_adapter.py
- [ ] T025 [US1] Implement preview-frame and region selector backend endpoints in src/web/api/routes/analysis.py
- [ ] T026 [US1] Implement analysis start/progress/stop/result endpoints using T075 adapter in src/web/api/routes/analysis.py
- [ ] T027 [US1] Implement Analysis view form state and validation for source/output/settings including auto-generated output filename preview derived from video source identity (LP-003) in src/web/frontend/src/pages/AnalysisPage.tsx (Stitch: 860c4f4ace1a440f871b8de136d04b33)
- [ ] T028 [US1] Implement interactive scan-region selector modal UI in src/web/frontend/src/components/RegionSelectorModal.tsx (Stitch: b28f75f678a54812994bedd7291de13c)
- [ ] T029 [US1] Implement live progress panel and stop control wiring in src/web/frontend/src/components/AnalysisProgressPanel.tsx (Stitch: be5b3692817f4a81b652870f75c6c2ca)
- [ ] T072 [US1] Implement LP-005 export-failed retry action and error-state banner in src/web/frontend/src/components/AnalysisProgressPanel.tsx
- [ ] T030 [US1] Implement parity controls section (context patterns, gating, tolerance, OCR, logging, quality) in src/web/frontend/src/components/AnalysisSettingsPanel.tsx (Stitch: 860c4f4ace1a440f871b8de136d04b33)

**Checkpoint**: Analysis configuration/run workflow independently functional.

---

## Phase 5: User Story 2 - Review Candidates (Priority: P2)

**Goal**: Review loaded candidate occurrences with confirm/reject/edit/remove, thumbnails, deep links, undo, persistence, and exports.

**Independent Test**: Load result CSV, review candidates, mutate state, refresh/reopen, and export expected files.

### Tests for User Story 2

- [ ] T031 [P] [US2] Add contract tests for review session/action/export endpoints in tests/contract/test_review_api_007.py
- [ ] T032 [P] [US2] Add integration test for candidate review lifecycle and persistence in tests/integration/test_review_lifecycle_007.py
- [ ] T033 [P] [US2] Add integration test for thumbnail modal and YouTube deep link behavior in tests/integration/test_review_thumbnail_link_007.py
- [ ] T034 [P] [US2] Add integration test for export outputs (dedupe + occurrences) in tests/integration/test_review_export_007.py

### Implementation for User Story 2

- [ ] T035 [US2] Implement session load/list/get endpoints with schema gate in src/web/api/routes/review_sessions.py
	> Note: `review_sessions.py` is shared by T035 (load/list/get), T059 (directory scan), and T071 (PATCH thresholds). Coordinate to avoid conflicts; consider splitting T071 to `review_thresholds.py` if parallel implementation is needed.
- [ ] T036 [US2] Implement mutating action endpoint with immediate sidecar persistence in src/web/api/routes/review_actions.py; MUST handle all action_types defined in contracts/review-api.md: confirm, reject, edit, remove, move_candidate, merge_groups, reorder_group
- [ ] T037 [US2] Implement undo endpoint with full action history rollback in src/web/api/routes/review_actions.py
- [ ] T038 [US2] Implement thumbnail endpoint with local fallback extraction/cache in src/web/api/routes/review_assets.py
- [ ] T039 [US2] Implement export endpoint for deduplicated and occurrences CSV outputs in src/web/api/routes/review_export.py
- [ ] T040 [US2] Implement Review page candidate list and status actions UI in src/web/frontend/src/pages/ReviewPage.tsx (Stitch: 27b2ad687bd547429e2066b8447378cb)
- [ ] T041 [US2] Implement candidate inline edit/remove/undo interactions including conditional YouTube deep link display (shown only when source_type is youtube_url, omitted for local file sources) in src/web/frontend/src/components/CandidateRow.tsx (Stitch: 27b2ad687bd547429e2066b8447378cb)
- [ ] T042 [US2] Implement frame thumbnail modal and contextual metadata UI in src/web/frontend/src/components/FrameThumbnailModal.tsx (Stitch: 86073009f5014d538492307fd9be599e)
- [ ] T074 [US2] Modify src/services/analysis_service.py to write each detected frame image to <result_frames>/<candidate_id>.png alongside the result CSV at the moment of detection (FR-024); add unit tests for frame write path in tests/unit/test_analysis_thumbnail_capture.py

**Checkpoint**: Candidate review and persistence/export workflow independently functional.

---

## Phase 6: User Story 3 - Search and Filter (Priority: P3)

**Goal**: Real-time substring filtering and status filters on candidate list without incorrect side effects.

**Independent Test**: Apply/clear filters and verify only visible candidates are acted upon.

### Tests for User Story 3

- [ ] T043 [P] [US3] Add integration test for live search filtering behavior in tests/integration/test_review_search_filter_007.py
- [ ] T044 [P] [US3] Add integration test ensuring actions on visible candidates do not affect hidden candidates in tests/integration/test_review_filter_action_scope_007.py

### Implementation for User Story 3

- [ ] T045 [US3] Implement backend filter/query support for review snapshots in src/web/app/session_query_service.py
- [ ] T046 [US3] Implement Review search box and status filter controls in src/web/frontend/src/components/ReviewFilterBar.tsx (Stitch: 27b2ad687bd547429e2066b8447378cb)
- [ ] T047 [US3] Implement client-side filtered rendering and selection scoping in src/web/frontend/src/state/reviewSelectors.ts
- [ ] T048 [US3] Add search/filter performance assertions for 500 candidates in tests/integration/test_review_filter_performance_007.py

**Checkpoint**: Search and filtering independently functional and performant.

---

## Phase 7: User Story 4 - Bulk Similar-Name Confirmation (Priority: P4)

**Goal**: Group by similarity+temporal proximity, enable bulk confirm/reject, threshold tuning, regroup behavior, reorder, and merge/move.

**Independent Test**: Load grouped data, tune thresholds, perform bulk and manual regroup operations, verify resulting state and undo.

### Tests for User Story 4

- [ ] T049 [P] [US4] Add unit tests for grouping algorithm and threshold recomputation in tests/unit/test_review_grouping_007.py
- [ ] T050 [P] [US4] Add unit tests for recommendation scoring and threshold behavior in tests/unit/test_review_recommendations_007.py
- [ ] T051 [P] [US4] Add integration test for bulk confirm/reject and selective candidate confirmation in tests/integration/test_review_bulk_actions_007.py
- [ ] T052 [P] [US4] Add integration test for regroup on edit and user notice behavior in tests/integration/test_review_regroup_on_edit_007.py

### Implementation for User Story 4

- [ ] T053 [US4] Implement similarity+temporal grouping service in src/web/app/grouping_service.py; temporal proximity score MUST be exposed on each CandidateOccurrence as a distinct field for use as the FR-026 temporal proximity badge (separate from FR-031 recommendation badges)
- [ ] T054 [US4] Implement recommendation scoring service (group + candidate) in src/web/app/recommendation_service.py
- [ ] T055 [US4] Implement move/merge/reorder group mutation handlers in src/web/app/group_mutation_service.py
- [ ] T071 [US4] Implement PATCH /api/review/sessions/{session_id}/thresholds route with immediate grouping recompute in src/web/api/routes/review_sessions.py
- [ ] T056 [US4] Implement group card UI with: (1) bulk confirm/reject actions, (2) per-group similarity threshold slider, (3) FR-026 temporal proximity badge per occurrence (distinct chip from recommendation badge), (4) FR-031 candidate-level recommendation confidence badge, (5) drag reorder; also implement global recommendation threshold control (FR-031, range 0–100, default 70) in a Review view toolbar/panel component in src/web/frontend/src/components/CandidateGroupCard.tsx and src/web/frontend/src/components/ReviewThresholdPanel.tsx (Stitch: 27b2ad687bd547429e2066b8447378cb)

**Checkpoint**: Group-level review operations independently functional.

---

## Phase 8: User Story 5 - Multi-Session Loading and Navigation (Priority: P5)

**Goal**: Open/switch multiple result sessions with isolated review state per session.

**Independent Test**: Load two sessions, mutate one, switch sessions, and verify state isolation and restoration.

### Tests for User Story 5

- [ ] T057 [P] [US5] Add integration test for multi-session switching and state isolation in tests/integration/test_review_multi_session_007.py
- [ ] T058 [P] [US5] Add integration test for session picker directory scan and load behavior in tests/integration/test_review_session_picker_007.py

### Implementation for User Story 5

- [ ] T059 [US5] Implement CSV directory scan endpoint for session picker in src/web/api/routes/review_sessions.py
- [ ] T060 [US5] Implement session switch orchestration and cache policy in src/web/app/session_manager.py
- [ ] T061 [US5] Implement Review session picker UI with load/switch controls in src/web/frontend/src/components/SessionPicker.tsx (Stitch: 27b2ad687bd547429e2066b8447378cb)
- [ ] T062 [US5] Implement session-aware state container and hydration flow in src/web/frontend/src/state/reviewStore.ts
- [ ] T063 [US5] Add regression test for sidecar restore after browser reopen in tests/integration/test_review_sidecar_restore_007.py

**Checkpoint**: Multi-session navigation independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Complete global quality bars across stories and align implementation with approved Stitch artifacts.

- [ ] T064 [P] Implement global dark/light theme toggle, persistence, and first-run dark default behavior in src/web/frontend/src/components/ThemeToggle.tsx (Stitch: all screens — applies globally)
- [ ] T065 [P] Implement WCAG AA contrast tokens and theme variables in src/web/frontend/src/styles/theme.css
- [ ] T066 Implement backend startup timing instrumentation and SC-007 assertion coverage in tests/integration/test_web_startup_timing_007.py
- [ ] T067 Implement malformed/incompatible CSV error-state UX and API mapping in src/web/frontend/src/components/SessionLoadErrorState.tsx
- [ ] T068 [P] Add contract/integration regression for malformed CSV rejection in tests/contract/test_review_schema_gate_007.py
- [ ] T069 Reconcile frontend implementation with Stitch screens and document justified deviations in specs/007-web-player-ui/quickstart.md
- [ ] T070 Run end-to-end validation and update feature test manifest in tests/integration/test_full_workflow_007.py
- [ ] T073 Implement SC-005 lazy thumbnail loading via IntersectionObserver on candidate list images and add perf benchmark asserting <=200ms render for 500-candidate dataset in src/web/frontend/src/components/CandidateRow.tsx; benchmark fixture in src/web/frontend/tests/review/perfBenchmark.test.tsx (Depends on T041)

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) starts immediately.
- Foundational (Phase 2) depends on Setup and blocks all story phases.
- Story phases (Phase 3-8) depend on Foundational completion.
- Polish (Phase 9) depends on completion of selected story phases.

### User Story Dependencies

- US0 depends only on Foundational and unlocks reliable launch/navigation baseline.
- US1 depends on Foundational and can proceed after US0, though backend route work can overlap.
- US2 depends on Foundational and output artifacts from US1 for integrated flow testing.
- US3 depends on US2 review rendering baseline.
- US4 depends on US2 review state model and US3 filtering selectors.
- US5 depends on US2 persistence model; can run alongside later US4 UI refinements once session APIs stabilize.

### Within Each Story

- Tests should be added first and fail before implementation.
- Backend domain/service tasks should precede API route handlers.
- API route handlers should precede frontend wiring.
- Story checkpoint must pass before moving to next priority story.

---

## Parallel Execution Examples

### US0

- T015 and T016 can run in parallel.
- T017 and T019 can run in parallel after tests are in place.

### US1

- T021, T022, and T023 can run in parallel.
- T024 and T025 can run in parallel.
- T028 and T030 can run in parallel once backend endpoints are stable.

### US2

- T031 through T034 can run in parallel.
- T038 and T039 can run in parallel with T040.
- T041 and T042 can run in parallel once T040 baseline list rendering exists.

### US3

- T043 and T044 can run in parallel.
- T046 and T047 can run in parallel after T045 query contract is finalized.

### US4

- T049, T050, T051, and T052 can run in parallel.
- T053 and T054 can run in parallel.

### US5

- T057 and T058 can run in parallel.
- T061 and T062 can run in parallel after T059 and T060 are implemented.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete Phase 3 (US0) and Phase 4 (US1).
3. Validate launch, navigation, and analysis lifecycle.
4. Complete Phase 5 (US2) for usable review/export MVP.

### Incremental Delivery

1. Deliver US0 + US1 baseline.
2. Deliver US2 review and export.
3. Deliver US3 filtering/performance.
4. Deliver US4 grouping/bulk/recommendations.
5. Deliver US5 multi-session orchestration.
6. Finish polish and full regression validation.

### Parallel Team Strategy

1. Team A: Backend services and routes (Phases 2, 4, 5, 7).
2. Team B: Frontend Analysis/Review UI (Phases 3, 4, 5, 6, 7, 8).
3. Team C: Contract/integration/performance tests (all story phases + polish).

---

## Notes

- All tasks follow strict checklist format: checkbox, task ID, optional [P], optional [USx], clear file path.
- [P] markers indicate tasks that can execute concurrently in different files without incomplete dependencies.
- Google Stitch artifacts are authoritative for UI layout and component structure; implementation deviations must be documented.
