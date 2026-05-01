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
- [ ] T019 [US0] Implement top-level Analysis/Review navigation shell in src/web/frontend/src/App.tsx
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
- [ ] T025 [US1] Implement preview-frame and region selector backend endpoints in src/web/api/routes/analysis.py
- [ ] T026 [US1] Implement analysis start/progress/stop/result endpoints in src/web/api/routes/analysis.py
- [ ] T027 [US1] Implement Analysis view form state and validation for source/output/settings in src/web/frontend/src/pages/AnalysisPage.tsx
- [ ] T028 [US1] Implement interactive scan-region selector modal UI in src/web/frontend/src/components/RegionSelectorModal.tsx
- [ ] T029 [US1] Implement live progress panel and stop control wiring in src/web/frontend/src/components/AnalysisProgressPanel.tsx
- [ ] T030 [US1] Implement parity controls section (context patterns, gating, tolerance, OCR, logging, quality) in src/web/frontend/src/components/AnalysisSettingsPanel.tsx

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
- [ ] T036 [US2] Implement mutating action endpoint with immediate sidecar persistence in src/web/api/routes/review_actions.py
- [ ] T037 [US2] Implement undo endpoint with full action history rollback in src/web/api/routes/review_actions.py
- [ ] T038 [US2] Implement thumbnail endpoint with local fallback extraction/cache in src/web/api/routes/review_assets.py
- [ ] T039 [US2] Implement export endpoint for deduplicated and occurrences CSV outputs in src/web/api/routes/review_export.py
- [ ] T040 [US2] Implement Review page candidate list and status actions UI in src/web/frontend/src/pages/ReviewPage.tsx
- [ ] T041 [US2] Implement candidate inline edit/remove/undo interactions in src/web/frontend/src/components/CandidateRow.tsx
- [ ] T042 [US2] Implement frame thumbnail modal and contextual metadata UI in src/web/frontend/src/components/FrameThumbnailModal.tsx

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
- [ ] T046 [US3] Implement Review search box and status filter controls in src/web/frontend/src/components/ReviewFilterBar.tsx
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

- [ ] T053 [US4] Implement similarity+temporal grouping service in src/web/app/grouping_service.py
- [ ] T054 [US4] Implement recommendation scoring service (group + candidate) in src/web/app/recommendation_service.py
- [ ] T055 [US4] Implement move/merge/reorder group mutation handlers in src/web/app/group_mutation_service.py
- [ ] T056 [US4] Implement group card UI with bulk actions, threshold sliders, badges, and drag reorder in src/web/frontend/src/components/CandidateGroupCard.tsx

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
- [ ] T061 [US5] Implement Review session picker UI with load/switch controls in src/web/frontend/src/components/SessionPicker.tsx
- [ ] T062 [US5] Implement session-aware state container and hydration flow in src/web/frontend/src/state/reviewStore.ts
- [ ] T063 [US5] Add regression test for sidecar restore after browser reopen in tests/integration/test_review_sidecar_restore_007.py

**Checkpoint**: Multi-session navigation independently functional.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Complete global quality bars across stories and align implementation with approved Stitch artifacts.

- [ ] T064 [P] Implement global dark/light theme toggle, persistence, and first-run dark default behavior in src/web/frontend/src/components/ThemeToggle.tsx
- [ ] T065 [P] Implement WCAG AA contrast tokens and theme variables in src/web/frontend/src/styles/theme.css
- [ ] T066 Implement backend startup timing instrumentation and SC-007 assertion coverage in tests/integration/test_web_startup_timing_007.py
- [ ] T067 Implement malformed/incompatible CSV error-state UX and API mapping in src/web/frontend/src/components/SessionLoadErrorState.tsx
- [ ] T068 [P] Add contract/integration regression for malformed CSV rejection in tests/contract/test_review_schema_gate_007.py
- [ ] T069 Reconcile frontend implementation with Stitch screens and document justified deviations in specs/007-web-player-ui/quickstart.md
- [ ] T070 Run end-to-end validation and update feature test manifest in tests/integration/test_full_workflow_007.py

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
# Tasks: Web-Based Player Name Verification UI

**Input**: Design documents from `specs/007-web-player-ui/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required), `research.md`, `data-model.md`, `contracts/web-api-contract.md`, `quickstart.md`

**Tests**: Included because `spec.md` explicitly defines mandatory user scenarios and independent tests.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no unmet dependencies)
- **[Story]**: User story label (`[US0]` ... `[US5]`) for story-phase tasks only
- Every task includes an explicit file path

> Visual fidelity remediation reopened on 2026-04-20. Behavioral implementation remains in place, but Stitch shell/layout/token work below is still active.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize backend/frontend scaffolding and core tooling.

- [X] T001 Create web package scaffolding in `src/web/__init__.py`, `src/web/app/__init__.py`, and `src/web/api/__init__.py`
- [X] T002 Initialize frontend workspace configuration in `src/web/frontend/package.json`, `src/web/frontend/tsconfig.json`, and `src/web/frontend/vite.config.ts`
- [X] T003 [P] Add frontend test/lint configuration in `src/web/frontend/vitest.config.ts`, `src/web/frontend/eslint.config.js`, and `src/web/frontend/tests/setup.ts`
- [X] T004 [P] Add backend web dependencies and optional extras in `pyproject.toml` and `requirements.txt`
- [X] T005 Create FastAPI server bootstrap with static mounting placeholder in `src/web/app/server.py`
- [X] T006 Create frontend app bootstrap in `src/web/frontend/src/main.tsx` and `src/web/frontend/src/App.tsx`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement shared infrastructure that blocks all user stories.

**⚠️ CRITICAL**: No user story implementation should begin before this phase is complete.

- [X] T007 Implement API schema contracts in `src/web/api/schemas.py`
- [X] T008 Implement API router and error envelope handlers in `src/web/api/router.py` and `src/web/api/error_handlers.py`
- [X] T009 [P] Implement settings persistence adapter (`scytcheck_settings.json`) in `src/web/app/settings_store.py`
- [X] T010 [P] Implement review sidecar persistence (`*.review.json`) in `src/web/app/review_store.py`
- [X] T011 Implement session registry and lifecycle state model in `src/web/app/session_manager.py` and `src/web/app/state.py`
- [X] T012 [P] Implement analysis bridge to existing pipeline in `src/web/app/analysis_adapter.py`
- [X] T013 [P] Implement thumbnail persistence/extraction service in `src/web/app/thumbnail_service.py`
- [X] T014 [P] Implement grouping and recommendation base services in `src/web/app/grouping_service.py` and `src/web/app/recommendation_service.py`
- [X] T015 Add foundational API contract smoke tests in `tests/contract/test_web_api_core.py`

**Checkpoint**: Foundation complete. User story phases can now proceed.

---

## Phase 3: User Story 0 - Launch to Web UI (Priority: P0)

**Goal**: Portable app launches local web server and opens browser to Analysis view.

**Independent Test**: Running the portable app opens browser to Analysis view within 5 seconds, and Review is reachable via top nav without reload.

### Tests for User Story 0

- [X] T016 [P] [US0] Add integration launch test (including single-instance/port-reuse scenario: if server already running, no port conflict; browser focuses existing tab or opens new tab) and assert end-to-end launch-to-functional-UI time <=5s in `tests/integration/test_web_launch_entrypoint.py`
- [X] T017 [P] [US0] Add navigation shell integration test in `tests/integration/test_web_navigation_shell.py`

### Implementation for User Story 0

- [X] T018 [US0] Implement launch orchestration (start server + open browser) with single-instance guard (port check: if already bound, open browser to running instance instead of restarting) in `src/main.py`
- [X] T019 [US0] Update portable launch scripts for web startup in `run_app.ps1` and `run_app.bat`
- [X] T020 [US0] Implement top-level navigation shell in `src/web/frontend/src/components/TopNav.tsx` (Stitch: `bc3dd84c4b11426db5983a60eb2dcbf3`)
- [X] T021 [US0] Implement route pages for Analysis and Review in `src/web/frontend/src/pages/AnalysisPage.tsx` (Stitch: `bc3dd84c4b11426db5983a60eb2dcbf3`) and `src/web/frontend/src/pages/ReviewPage.tsx` (Stitch: `6d16e85501654ed58fb2dc38e4c00f69`)
- [X] T022 [US0] Add server health/version endpoint for startup verification in `src/web/api/routes/settings.py`

**Checkpoint**: Web app launches correctly and basic navigation works end-to-end.

---

## Phase 4: User Story 1 - Configure and Run Video Analysis (Priority: P1)

**Goal**: Configure analysis source/settings, run and stop analysis, and display live progress.

**Independent Test**: User can start analysis from YouTube/local source, observe progress, stop run, and obtain reviewable partial or complete results.

### Tests for User Story 1

- [X] T023 [P] [US1] Add contract tests for analysis start/stop/progress in `tests/contract/test_web_api_analysis.py`
- [X] T024 [P] [US1] Add integration analysis flow test in `tests/integration/test_web_analysis_flow.py`

### Implementation for User Story 1

- [X] T025 [US1] Implement analysis start/stop/progress API routes in `src/web/api/routes/analysis.py`
- [X] T026 [US1] Implement Analysis source input UI in `src/web/frontend/src/features/analysis/SourceInput.tsx` (Stitch: `bc3dd84c4b11426db5983a60eb2dcbf3`)
- [X] T027 [US1] Enumerate all `src/config.py` / `scytcheck_settings.json` keys into `specs/007-web-player-ui/fr018-settings-parity.md` as the FR-018 parity checklist artifact, then implement full settings parity panel covering every enumerated key in `src/web/frontend/src/features/analysis/SettingsPanel.tsx` (Stitch: `bc3dd84c4b11426db5983a60eb2dcbf3`)
- [X] T028 [US1] Implement interactive scan region selector in `src/web/frontend/src/features/analysis/ScanRegionSelector.tsx` (Stitch: `bc3dd84c4b11426db5983a60eb2dcbf3`)
- [X] T029 [US1] Implement analysis controls and progress widgets in `src/web/frontend/src/features/analysis/AnalysisControls.tsx` and `src/web/frontend/src/features/analysis/ProgressWidgets.tsx` (Stitch: `bc3dd84c4b11426db5983a60eb2dcbf3`)
- [X] T030 [US1] Implement settings read/write routes using existing settings file in `src/web/api/routes/settings.py`
- [X] T031 [US1] Wire Analysis page state/actions via store and API client in `src/web/frontend/src/state/appStore.ts` and `src/web/frontend/src/services/apiClient.ts`

**Checkpoint**: Analysis can be fully configured and run from the web UI.

---

## Phase 5: User Story 2 - Review Detected Player Name Candidates (Priority: P2)

**Goal**: Review candidates with confirm/reject/edit actions, thumbnail preview, timestamp links, and dual CSV export.

**Independent Test**: Load a result session, review candidates, edit text, confirm/reject/remove entries, and export both required CSV outputs.

### Tests for User Story 2

- [X] T032 [P] [US2] Add contract tests for review candidate operations in `tests/contract/test_web_api_review_candidates.py`
- [X] T033 [P] [US2] Add integration review/export flow test in `tests/integration/test_web_review_candidates.py`

### Implementation for User Story 2

- [X] T034 [US2] Implement review session retrieval and candidate patch routes in `src/web/api/routes/review.py`
- [X] T035 [US2] Implement thumbnail endpoint and fallback extraction behavior in `src/web/api/routes/thumbnails.py`
- [X] T036 [US2] Implement dual export endpoint (names + occurrences CSV) in `src/web/api/routes/export.py`
- [X] T037 [US2] Implement frame capture write-path during analysis in `src/services/analysis_service.py`
- [X] T038 [US2] Add unit tests for frame capture thumbnail writes in `tests/unit/test_analysis_thumbnail_capture.py`
- [X] T039 [US2] Implement candidate/group rendering UI including temporal proximity chip/badge sourced from `temporalCohesionScore` on each `CandidateCard` in `src/web/frontend/src/features/review/CandidateGroupList.tsx` and `src/web/frontend/src/features/review/CandidateCard.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`)
- [X] T040 [US2] Implement candidate action controls (confirm/reject/edit/remove) in `src/web/frontend/src/features/review/CandidateActions.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`)
- [X] T041 [US2] Implement thumbnail modal and YouTube deep-link viewer in `src/web/frontend/src/features/review/ThumbnailViewer.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`)
- [X] T042 [US2] Implement review progress display in `src/web/frontend/src/features/review/ReviewProgressBar.tsx` (Stitch: `6d16e85501654ed58fb2dc38e4c00f69`)
- [X] T043 [US2] Implement dual export action bar in `src/web/frontend/src/features/review/ExportBar.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`)

**Checkpoint**: Core review loop and exports are functional.

---

## Phase 6: User Story 3 - Search and Filter Candidates (Priority: P3)

**Goal**: Real-time candidate filtering with action correctness under active filters.

**Independent Test**: Typing a query filters visible candidates immediately; clearing query restores all results; actions affect only targeted candidates.

### Tests for User Story 3

- [X] T044 [P] [US3] Add frontend filter unit tests in `src/web/frontend/tests/review/searchFilter.test.tsx`
- [X] T045 [P] [US3] Add integration filtering action test in `tests/integration/test_web_review_filtering.py`

### Implementation for User Story 3

- [X] T046 [US3] Implement filtering hook/state selectors in `src/web/frontend/src/features/review/useReviewFilter.ts`
- [X] T047 [US3] Implement filter/search bar UI in `src/web/frontend/src/features/review/ReviewSearchBar.tsx` (Stitch: `0d725633a5c04755a3edf78f2c0726c4`)
- [X] T048 [US3] Integrate filtered rendering pipeline in `src/web/frontend/src/features/review/CandidateGroupList.tsx` (Stitch: `0d725633a5c04755a3edf78f2c0726c4`)

**Checkpoint**: Search/filter behavior is fast and deterministic.

---

## Phase 7: User Story 4 - Bulk Confirmation of Similar Names (Priority: P4)

**Goal**: Group-level review operations, regrouping, reorder, unlimited undo, and recommendation guidance.

**Independent Test**: User performs group confirm/reject, move/merge, reorder, hard delete + undo, and threshold updates with immediate visual feedback.

### Tests for User Story 4

- [X] T049 [P] [US4] Add advanced review contract tests in `tests/contract/test_web_api_review_advanced.py`
- [X] T050 [P] [US4] Add advanced review integration test in `tests/integration/test_web_review_advanced_actions.py`

### Implementation for User Story 4

- [X] T051 [US4] Implement bulk group action routes in `src/web/api/routes/review_groups.py`
- [X] T052 [US4] Implement regroup move/merge and group reorder routes in `src/web/api/routes/review_reorder.py`
- [X] T053 [US4] Implement unlimited undo action log and undo endpoint in `src/web/app/action_log.py` and `src/web/api/routes/review_undo.py`
- [X] T054 [US4] Implement recommendation scoring and threshold recalculation routes in `src/web/app/recommendation_service.py` and `src/web/api/routes/recommendations.py`
- [X] T055 [US4] Implement grouping-threshold route and recompute flow in `src/web/app/grouping_service.py` and `src/web/api/routes/review_groups.py`
- [X] T056 [US4] Implement group action toolbar (bulk, merge, move, reorder) in `src/web/frontend/src/features/review/GroupActionToolbar.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`)
- [X] T057 [US4] Implement undo history panel in `src/web/frontend/src/features/review/UndoHistoryPanel.tsx` (Stitch: `6d16e85501654ed58fb2dc38e4c00f69`)
- [X] T058 [US4] Implement recommendation and threshold UI panels in `src/web/frontend/src/features/review/RecommendationPanel.tsx` and `src/web/frontend/src/features/review/GroupingThresholdControl.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`)

**Checkpoint**: Advanced group operations and recommendation guidance are complete.

---

## Phase 8: User Story 5 - Load and Navigate Multiple Analysis Sessions (Priority: P5)

**Goal**: Load sessions from selected folders and preserve independent review state per session.

**Independent Test**: User loads two CSV sessions, switches back and forth, and sees each session state restored accurately.

### Tests for User Story 5

- [X] T059 [P] [US5] Add session route contract tests in `tests/contract/test_web_api_sessions.py`
- [X] T060 [P] [US5] Add multi-session integration test in `tests/integration/test_web_multi_session_state.py`

### Implementation for User Story 5

- [X] T061 [US5] Implement directory scan/session list routes in `src/web/api/routes/sessions.py`
- [X] T062 [US5] Implement session switch/load restore behavior in `src/web/app/session_manager.py`
- [X] T063 [US5] Implement folder/session picker UI in `src/web/frontend/src/features/sessions/SessionPicker.tsx` (Stitch: `0d725633a5c04755a3edf78f2c0726c4`)

**Checkpoint**: Multi-session workflow is stable and independently persisted.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Accessibility, performance, packaging, documentation, and final validation.

- [X] T064 [P] Implement global theme toggle + dark-default persistence in `src/web/frontend/src/components/ThemeToggle.tsx` (Stitch: `ddea17d197634e119c84858e46c61bf7`) and `src/web/api/routes/settings.py`
- [X] T065 [P] Add theme accessibility and WCAG contrast tests in `src/web/frontend/tests/theme/accessibility.test.ts`
- [X] T066 Implement SC-005 performance for candidate list: (a) apply `IntersectionObserver` / `loading="lazy"` to all thumbnail images in `src/web/frontend/src/features/review/CandidateGroupList.tsx` (Stitch: `ca5cd390184a4002953178d25c920a67`); (b) add perf benchmark fixture with a 500-candidate dataset in `src/web/frontend/tests/review/perfBenchmark.test.tsx`; (c) assert <=200ms render response - task is not complete until the benchmark assertion passes
- [X] T067 Update packaging to bundle frontend assets and web launch path in `scripts/release/build.ps1` and `build-config.spec`
- [X] T068 Update user documentation for web workflow in `README.md`
- [X] T069 Validate quickstart workflows and update run instructions in `specs/007-web-player-ui/quickstart.md`
- [X] T070 Run complete pytest and vitest suites; for any failures fix production code (never edit test assertions to force green); rerun until all suites pass green; store final clean run logs in `artifacts/test-runs/web-final-pytest.log` and `artifacts/test-runs/web-final-vitest.log`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1; blocks all user stories.
- **Phases 3-8 (User Stories)**: Depend on Phase 2 completion.
- **Phase 9 (Polish)**: Depends on selected user stories being complete.

### User Story Dependencies

- **US0 (P0)**: Starts after foundational phase; no dependency on other stories.
- **US1 (P1)**: Starts after foundational phase; independent from US2-US5.
- **US2 (P2)**: Starts after foundational phase and benefits from US0 shell completion.
- **US3 (P3)**: Depends on US2 candidate rendering baseline.
- **US4 (P4)**: Depends on US2 core review data/actions.
- **US5 (P5)**: Depends on foundational session/review persistence and can run parallel to US3/US4 after US2 endpoints exist.

### Story Completion Order

US0 → US1 → US2 → US3 → US4 → US5

---

## Parallel Execution Examples

### US0 Parallel Example

- T016 and T017 can run in parallel (separate integration test files).

### US1 Parallel Example

- T023 and T024 can run in parallel (contract vs integration tests).
- T026 and T027 can run in parallel after T025 (independent UI files).

### US2 Parallel Example

- T032 and T033 can run in parallel.
- T041 and T043 can run in parallel after T039/T040 (independent review UI components).

### US3 Parallel Example

- T044 and T045 can run in parallel.

### US4 Parallel Example

- T049 and T050 can run in parallel.
- T057 and T058 can run in parallel after T053/T054 (independent frontend panels).

### US5 Parallel Example

- T059 and T060 can run in parallel.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US0 and US1.
3. Validate launch + analysis flow as first deliverable.

### Incremental Delivery

1. Add US2 review flow.
2. Add US3 filtering.
3. Add US4 advanced review operations.
4. Add US5 multi-session management.
5. Finish Phase 9 polish and validation.

### Parallel Team Strategy

1. Team A: Backend routes/services (`src/web/api/`, `src/web/app/`).
2. Team B: Frontend views/components (`src/web/frontend/src/`).
3. Team C: Contract/integration/frontend tests (`tests/`, `src/web/frontend/tests/`).

---

## Notes

- `[P]` tasks target independent files and can be parallelized safely.
- Each user story phase is independently testable.
- Any frontend implementation task must follow the Stitch coverage/fidelity rules defined in `plan.md`.

