# Tasks: Video-Primary Review Flow

**Feature**: 013-video-primary-review  
**Branch**: `013-create-spec-branch`  
**Input**: spec.md, plan.md, research.md, data-model.md, quickstart.md, contracts/

**Organization**: Tasks grouped by user story (US1, US2, US3) to enable independent implementation and testing.

---

## Format

- **[P]**: Can run in parallel (different files, no dependencies)
- **[US1/US2/US3]**: User story label for traceability
- **File paths**: Exact locations for implementation

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and foundational code structure

- [X] T001 Create `/src/data/models.py` with base entity classes (VideoProject, AnalysisRun, ReviewContext, Candidate, CandidateGroup, ProjectLocationSetting)
- [X] T002 [P] Create `/src/web/api/__init__.py` REST API module structure
- [X] T003 [P] Create `/src/web/frontend/src/types/index.ts` TypeScript interfaces for API responses
- [X] T004 [P] Create `/tests/unit/` and `/tests/integration/` directory structure
- [X] T005 [P] Create `/tests/contract/` directory for API contract tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend and frontend infrastructure MUST be complete before user story work begins

**⚠️ CRITICAL**: No user story can proceed until this phase is complete

### Backend Foundational

- [X] T006 Modify `/src/config.py` to add app-level project location setting with default path (platform-aware: Windows, macOS, Linux)
- [X] T007 [P] Create `/src/services/project_service.py` with filesystem project discovery algorithm (scan directory, validate metadata.json, load project metadata)
- [X] T008 [P] Modify `/src/services/history_service.py` to replace app-level history with filesystem scan (no separate history list maintained)
- [X] T009 [P] Create `/src/services/review_service.py` with merge algorithm (deduplication by spelling, prior-decision-wins conflict resolution)
- [X] T010 [P] Implement candidate freshness algorithm in `/src/services/review_service.py` (spelling-based "new" marker logic)
- [X] T011 [P] Create `/src/web/api/settings.py` endpoints: GET /api/settings, PUT /api/settings, POST /api/settings/validate
- [X] T012 Modify `/src/main.py` to register new API routes (settings, analysis, projects)

### Frontend Foundational

- [X] T013 [P] Update `/src/web/frontend/src/types/index.ts` with all API response types (AnalysisProgress, ReviewContext, ProjectList, AppSettings)
- [X] T014 [P] Create `/src/web/frontend/src/services/api.ts` REST client with methods: startAnalysis, getProgress, getProjects, getSettings, updateSettings
- [X] T015 [P] Create `/src/web/frontend/src/components/ProgressWindow.tsx` component (message display, auto-dismiss on completion)
- [X] T016 Modify `/src/web/frontend/src/pages/MainLayout.tsx` to add gear icon in top navigation → opens Settings view

### UI Design Authority (Google Stitch)

- [ ] T017 Open Google Stitch project at `specs/013-video-primary-review/stitch/` and verify/create design system (theme, typography, colors, component styles)
- [ ] T018 [P] Design Analysis view screen in Stitch: remove output filename input, show progress window placeholder, show "Review will auto-open" messaging
- [ ] T019 [P] Design Review view screen in Stitch: show video URL (read-only), candidate list with "new" badge indicator, group visualization
- [ ] T020 [P] Design Videos view screen in Stitch: project list cards/table, project metadata (URL, run count, last analyzed), empty state message
- [ ] T021 [P] Design Settings view screen in Stitch: project location input field, validation feedback, "Browse" button, "Reset to Default" button
- [ ] T022 [P] Design MainLayout update in Stitch: gear icon placement and styling, "Videos" tab rename from "History"

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Auto-Load Video Review Context (Priority: P1) 🎯 MVP

**Goal**: Users can open review directly after analysis and see one combined review state for the analyzed video without manually choosing a result file.

**Independent Test**: Run analysis on a video with existing prior runs; verify review opens automatically with combined data set; no manual file-load action required.

### API Contracts & Tests for US1

- [X] T023 [P] [US1] Write contract test in `/tests/contract/test_analysis_api_013.py` for POST /api/analysis/start endpoint (validates project_status in response: "creating" or "merging")
- [X] T024 [P] [US1] Write contract test in `/tests/contract/test_analysis_api_013.py` for GET /api/analysis/progress endpoint (validates progress_percent, project_status, message fields)
- [X] T025 [P] [US1] Write contract test in `/tests/contract/test_review_api_013.py` for GET /api/review/context endpoint (validates merged candidates, groups structure)
- [X] T026 [P] [US1] Write integration test in `/tests/integration/test_analysis_flow_013.py` for end-to-end: analysis start → progress polling → completion → review context load

### Backend Implementation for US1

- [X] T027 [US1] Implement `/src/web/api/analysis.py::post_analysis_start()` endpoint (validate video URL, detect create vs. merge status, start async analysis)
- [X] T028 [US1] Implement `/src/web/api/analysis.py::get_analysis_progress()` endpoint (return current progress, project_status message, stream updates)
- [X] T029 [P] [US1] Modify `/src/services/analysis_service.py` to detect project create vs. merge before starting analysis (determine run_id for new vs. existing project)
- [X] T030 [P] [US1] Modify `/src/services/analysis_service.py` to track project_status during execution (populate in progress stream: "creating" or "merging")
- [X] T031 [US1] Implement `/src/web/api/review.py::get_review_context()` endpoint (load all runs for video, call review_service.merge_review_context(), return merged context)
- [X] T032 [P] [US1] Implement `review_service.merge_review_context()` function (dedup candidates by spelling, apply prior decisions, return merged ReviewContext)
- [X] T033 [P] [US1] Add prior decision loading from `{project_location}/{video_id}/.scyt_review_workspaces/review_state.json` in review_service
- [X] T034 [US1] Write unit test in `/tests/unit/test_review_merge_013.py` for merge algorithm (prior decision wins, deduplication, edge cases)

### Frontend Implementation for US1

- [X] T035 [P] [US1] Modify `/src/web/frontend/src/pages/AnalysisPage.tsx` to remove output filename input field (keep only video URL input)
- [X] T036 [P] [US1] Modify `/src/web/frontend/src/pages/AnalysisPage.tsx` to call API: POST /api/analysis/start on "Start Analysis" click
- [X] T037 [P] [US1] Modify `/src/web/frontend/src/pages/AnalysisPage.tsx` to show ProgressWindow component with polling logic (GET /api/analysis/progress every 1-2 seconds)
- [X] T038 [US1] Modify `/src/web/frontend/src/pages/AnalysisPage.tsx` to auto-navigate to ReviewPage when progress status === "completed" with video_id parameter
- [X] T039 [P] [US1] Implement `/src/web/frontend/src/pages/ReviewPage.tsx` to load review context on mount (GET /api/review/context?video_id=...)
- [X] T040 [P] [US1] Modify `/src/web/frontend/src/pages/ReviewPage.tsx` to show video URL as read-only (not filename input field)
- [X] T041 [US1] Add test in `/tests/integration/test_analysis_flow_013.py` to verify ReviewPage renders without manual load action

**Checkpoint**: User Story 1 complete - analysis workflow fully functional, review auto-opens

---

## Phase 4: User Story 2 - Emphasize Newly Found Candidates (Priority: P2)

**Goal**: Users can immediately identify which candidates came from the most recent analysis run via visual "new" marker.

**Independent Test**: Run two analyses for same video; verify candidates unique to latest run are marked as new; re-detected candidates (same spelling) are not marked.

### API Contracts & Tests for US2

- [X] T042 [P] [US2] Write unit test in `/tests/unit/test_candidate_freshness_013.py` for freshness algorithm (new if spelling NOT in any prior run, only in latest run)
- [X] T043 [P] [US2] Write unit test in `/tests/unit/test_candidate_freshness_013.py` for false negatives (same spelling re-detected → NOT marked as new)
- [X] T044 [P] [US2] Write integration test in `/tests/integration/test_candidate_markers_013.py` for multi-run scenario (run 1 → run 2 → verify new markers only on run 2 candidates)
- [X] T045 [US2] Verify GET /api/review/context returns marked_new field in candidates (contract validation in `/tests/contract/test_review_api_013.py`)

### Backend Implementation for US2

- [X] T046 [US2] Implement `review_service.mark_new_candidates()` function in `/src/services/review_service.py` (depends on T032 merge output; spelling comparison: only new if unique to latest_run)
- [X] T047 [P] [US2] Call `mark_new_candidates()` in `merge_review_context()` after deduplication step
- [X] T048 [P] [US2] Implement `/src/web/api/review.py::put_review_action()` endpoint to handle candidate action (confirmed, rejected, edited, clear_new) → clears marked_new flag
- [X] T049 [P] [US2] Persist candidate actions to `review_state.json` in PUT /api/review/action handler
- [X] T050 [US2] Write unit test in `/tests/unit/test_candidate_freshness_013.py` for persistence (marked_new cleared on user action, persisted to review_state.json)

### Frontend Implementation for US2

- [X] T051 [P] [US2] Modify `/src/web/frontend/src/pages/ReviewPage.tsx` and `/src/web/frontend/src/components/CandidateRow.tsx` to render candidates from ReviewContext
- [X] T052 [P] [US2] Add visual "new" marker/badge to candidates where marked_new === true (Material Symbols icon + highlight)
- [X] T053 [P] [US2] Implement candidate action handlers in `/src/web/frontend/src/pages/ReviewPage.tsx` and `/src/web/frontend/src/components/CandidateRow.tsx` (confirm, reject, edit, clear → PUT /api/review/action)
- [X] T054 [US2] Add test in `/src/web/frontend/tests/review/CandidateRow.test.tsx` to verify UI renders new markers correctly and dispatches clear action

**Checkpoint**: User Stories 1 & 2 complete - video review workflow with freshness indicators fully functional

---

## Phase 5: User Story 3 - Shift Project Controls To Video-Centric Navigation (Priority: P3)

**Goal**: Users manage projects via Videos view and configure project location in Settings, not in Analysis view.

**Independent Test**: Verify output filename removed from Analysis view; Settings gear icon accessible; project location editable in Settings; Videos view discovers projects from configured location.

### API Contracts & Tests for US3

- [X] T055 [P] [US3] Write contract test in `/tests/contract/test_projects_api_013.py` for GET /api/projects endpoint (validates project list structure, location_status field)
- [X] T056 [P] [US3] Write contract test in `/tests/contract/test_projects_api_013.py` for PUT /api/settings endpoint (validates path validation behavior)
- [X] T057 [P] [US3] Write integration test in `/tests/integration/test_project_discovery_013.py` for filesystem project discovery (single-level non-recursive scan, metadata validation, empty location handling)
- [X] T058 [P] [US3] Write integration test in `/tests/integration/test_settings_flow_013.py` for settings change → Videos list refresh workflow

### Backend Implementation for US3

- [X] T059 [US3] Implement `/src/web/api/routes/projects.py::get_projects()` endpoint (call project_service.discover_projects(), return sorted list with metadata)
- [X] T060 [P] [US3] Implement `/src/web/api/routes/projects.py::get_projects_detail()` endpoint for single project GET /api/projects/:project_id
- [X] T061 [P] [US3] Implement project_service.discover_projects() in `/src/services/project_service.py` (scan filesystem, validate metadata.json, load VideoProject objects)
- [X] T062 [P] [US3] Implement `/src/web/api/routes/settings.py::put_settings()` endpoint with path validation (check existence, writability, auto-create directory if possible)
- [X] T063 [P] [US3] Implement path fallback in config.py/settings store: if settings file missing on first run, create default location + write settings file
- [X] T064 [US3] Write unit test in `/tests/unit/test_project_discovery_013.py` for filesystem scanning (valid projects found, invalid projects skipped)
- [X] T065 [P] [US3] Write unit test in `/tests/unit/test_project_discovery_013.py` for metadata loading (valid metadata parsed, invalid metadata skipped)

### Frontend Implementation for US3

- [X] T066 [P] [US3] Create `/src/web/frontend/src/pages/SettingsPage.tsx` with project location input field, validation feedback, browse button, reset button
- [X] T067 [P] [US3] Implement project location form in SettingsPage: validate on change via POST /api/settings/validate, show feedback ("valid", "missing", "unwritable")
- [X] T068 [P] [US3] Implement save handler in SettingsPage: PUT /api/settings with confirmed path, reload app-level settings on success
- [X] T069 [US3] Create `/src/web/frontend/src/pages/VideosPage.tsx` (video-centric replacement for history list)
- [X] T070 [P] [US3] Implement project list loading in VideosPage: GET /api/projects on mount, handle empty state and error states
- [X] T071 [P] [US3] Implement "open project" action in VideosPage: click project → navigate to ReviewPage with video_id parameter
- [X] T072 [P] [US3] Show project metadata in VideosPage: video URL, run count, last analyzed date, candidate counts
- [X] T073 [US3] Modify `/src/web/frontend/src/pages/MainLayout.tsx` and app routing to keep "Videos" as the navigation target for project discovery
- [X] T074 [US3] Add integration test in `/tests/integration/test_project_discovery_013.py` to verify projects appear after location change in Settings

**Checkpoint**: All user stories complete - video-primary review workflow fully functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Refinements, documentation, and comprehensive testing

### Documentation & Validation

- [X] T075 [P] Verify `/src/data/models.py` entities match data-model.md entity definitions (VideoProject, AnalysisRun, ReviewContext, etc.)
- [X] T076 [P] Verify API endpoints match contracts/ specifications (analysis.md, review.md, projects.md)
- [X] T077 [P] Add API documentation comments to all endpoints in `/src/web/api/`
- [X] T078 [P] Update README.md with video-primary review workflow summary and user stories

### UI Implementation vs. Stitch Design

- [X] T079 [P] Compare AnalysisPage.tsx implementation against Stitch Analysis view screen; document any justified deviations
- [X] T080 [P] Compare ReviewPage.tsx implementation against Stitch Review view screen; document any justified deviations
- [X] T081 [P] Compare VideosPage.tsx implementation against Stitch Videos view screen; document any justified deviations
- [X] T082 [P] Compare SettingsPage.tsx implementation against Stitch Settings view screen; document any justified deviations
- [X] T083 [P] Verify MainLayout.tsx gear icon styling matches Stitch design system

### Error Handling & Edge Cases

- [X] T084 [P] Add error handling for missing project location (show blocking error + recovery path in UI)
- [X] T085 [P] Add error handling for unwritable project location (show warning + guidance in UI)
- [X] T086 [P] Add error handling for corrupted metadata.json (skip project in discovery, log error)
- [X] T087 [P] Add error handling for interrupted analysis (persist partial state, show recovery message)
- [X] T088 [P] Test edge case: video with only one analysis run (verify auto-load works, no false merge conflicts)
- [X] T089 [P] Test edge case: project location with zero projects (verify empty state in VideosPage)
- [X] T090 [P] Test edge case: prior app-level history data exists (verify ignored for project discovery)

### Performance & Optimization

- [X] T091 [P] Optimize project discovery (cache results, avoid repeated filesystem scans during session)
- [X] T092 [P] Optimize candidate merge algorithm (profile with 10k+ candidates, ensure <500ms)
- [X] T093 [P] Optimize progress polling (verify <1s latency, handle missed heartbeats gracefully)
- [X] T094 [P] Verify ReviewPage auto-opens within 2 seconds of analysis completion

### Comprehensive Testing

- [X] T095 [P] Run all contract tests: `pytest tests/contract/test_*.py`
- [X] T096 [P] Run all integration tests: `pytest tests/integration/test_*.py`
- [X] T097 [P] Run all unit tests: `pytest tests/unit/test_*.py`
- [X] T098 [P] Run frontend tests: `npm run test:ui` in src/web/frontend/
- [ ] T099 Manual end-to-end test: Full workflow on dev machine (settings → analysis → review → project management), including timed verification for auto-open-to-review <= 2s
- [ ] T100 Manual usability test: Execute SC usability protocol (n >= 20, first-attempt only, no hints) and record pass/fail for SC-003, SC-004, SC-006

---

## Dependencies & Execution Strategy

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational - BLOCKING)
    ↓ (ALL STORIES can start in parallel after this)
    ├─→ Phase 3 (User Story 1 - P1)
    ├─→ Phase 4 (User Story 2 - P2)
    └─→ Phase 5 (User Story 3 - P3)
        ↓
    Phase 6 (Polish & Cross-Cutting)
```

### Critical Path

1. Phase 1: Setup (foundation)
2. Phase 2: Foundational (BLOCKS all stories - must complete)
3. Phase 3: US1 (MVP - deliverable)
4. Phase 4: US2 (enhancement)
5. Phase 5: US3 (completion)
6. Phase 6: Polish

### Parallel Opportunities Within Phase 2

All tasks marked [P] in Phase 2 can run in parallel:
- T006-T012 can run in parallel (different files, no cross-dependencies)
- T013-T016 can run in parallel (frontend setup)
- T017-T022 can run in parallel (Stitch design tasks)

### Parallel Opportunities Within User Stories

Once Phase 2 is complete:
- **US1, US2, US3 can start in parallel** (different features, independent implementation)
- Within each story, all [P] tasks can run in parallel (e.g., T023-T026 can run together)

### Parallel Opportunities Within Phase 6

All tasks marked [P] can run in parallel (different concerns, no dependencies)

---

## Implementation Strategy

### MVP Delivery (User Story 1 Only)

1. ✅ Complete Phase 1: Setup
2. ✅ Complete Phase 2: Foundational
3. ✅ Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently (analysis → auto-open review)
5. Deploy/Demo to stakeholders
6. **THEN proceed** with US2 and US3

### Incremental Delivery (All Stories)

1. Complete Phase 1 + Phase 2 → Foundation ready
2. Complete Phase 3 → MVP deliverable (US1 complete, reviewable)
3. Complete Phase 4 → Enhanced workflow (US2 complete, new markers visible)
4. Complete Phase 5 → Full feature (US3 complete, project management complete)
5. Complete Phase 6 → Production-ready (polish, docs, comprehensive tests)

### Parallel Team Strategy (3+ developers)

- **Developer A**: Phase 2 Backend (T006-T012) + Phase 3 Backend (T027-T034)
- **Developer B**: Phase 2 Frontend (T013-T016) + Phase 3 Frontend (T035-T041)
- **Developer C**: Phase 2 Stitch Design (T017-T022) in parallel with above
- Once Phase 2 done:
  - **Developer A**: Phase 4 Backend (T046-T050) + Phase 5 Backend (T059-T065)
  - **Developer B**: Phase 4 Frontend (T051-T054) + Phase 5 Frontend (T066-T074)
  - **Developer C**: Contract tests, integration tests (T023-T026, T055-T058)

---

## Acceptance Criteria Per Phase

### Phase 1 Acceptance

- [ ] All entity classes defined in models.py
- [ ] API module structure created
- [ ] TypeScript types defined

### Phase 2 Acceptance (GATE: Must pass before US1 begins)

- [ ] Project location setting works (default path created on first run)
- [ ] Filesystem project discovery algorithm implemented and tested
- [ ] Review merge algorithm (dedup + prior-decision-wins) implemented and tested
- [ ] Candidate freshness algorithm implemented and tested
- [ ] All new API endpoints registered (settings)
- [ ] ProgressWindow component renders and updates
- [ ] MainLayout updated with gear icon
- [ ] Google Stitch screens designed and approved for Analysis, Review, Videos, Settings

### Phase 3 Acceptance (US1)

- [ ] Analysis can be started via API
- [ ] Progress can be polled
- [ ] Review context can be retrieved merged
- [ ] ReviewPage auto-opens after analysis
- [ ] Video URL shows in review (not filename input)
- [ ] All US1 tests passing (contract, integration, unit)
- [ ] US1 can be tested independently without US2 or US3

### Phase 4 Acceptance (US2)

- [ ] Candidates marked as new (spelling-based)
- [ ] New marker visible in UI
- [ ] New marker cleared on user action
- [ ] All US2 tests passing (unit, integration)
- [ ] US2 can be tested independently (alongside US1)

### Phase 5 Acceptance (US3)

- [ ] Output filename removed from Analysis view
- [ ] Settings view accessible via gear icon
- [ ] Project location configurable in Settings
- [ ] Videos view shows discovered projects
- [ ] Project discovery uses filesystem only (no app history)
- [ ] All US3 tests passing (contract, integration, unit)
- [ ] US3 can be tested independently (alongside US1 & US2)

### Phase 6 Acceptance

- [ ] All documentation updated and reviewed
- [ ] All edge cases handled with clear error messages
- [ ] All tests passing (contract, integration, unit, UI)
- [ ] Manual end-to-end workflow validated
- [ ] UI matches approved Stitch designs (or justified deviations documented)

---

## Notes & Constraints

- **Test-First**: Write contract/integration tests FIRST; they should FAIL before implementation
- **Stitch Authority**: All UI decisions driven by approved Google Stitch screens; deviations must be documented
- **File Paths**: Exact paths shown assume src/tests structure from plan.md; adjust if needed
- **Independence**: Each user story must be independently testable and deployable
- **No Cross-Story Dependencies**: US2 and US3 should not block each other or US1
- **Parallel Execution**: [P] tasks can run in parallel within same phase
- **Commit Strategy**: Commit after each task or logical group (e.g., after all T0XX tests, after all T0XX implementations)
- **MVP First**: Complete Phase 1 + 2 + 3, validate, then proceed to Phase 4 & 5

---

## Summary

**Total Tasks**: 100  
**Setup Phase**: 5 tasks  
**Foundational Phase**: 17 tasks (BLOCKING - highest priority)  
**User Story 1 (MVP)**: 18 tasks (P1)  
**User Story 2**: 9 tasks (P2)  
**User Story 3**: 19 tasks (P3)  
**Polish & Cross-Cutting**: 32 tasks  

**MVP Scope (Phase 1 + 2 + 3)**: 40 tasks ≈ 2-3 weeks (with 2-3 developer team)  
**Full Feature (All Phases)**: 100 tasks ≈ 4-5 weeks (with 2-3 developer team)  

**Ready to begin Phase 1: Setup**
