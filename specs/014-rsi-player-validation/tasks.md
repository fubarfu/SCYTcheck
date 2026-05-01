# Tasks: RSI Player Validation Signal

**Input**: Design documents from `/specs/014-rsi-player-validation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅, quickstart.md ✅

**Branch**: `014-add-rsi-player-validation`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: New entities and config changes that all three user stories depend on. Must be complete before any story-phase work begins.

- [ ] T001 Add `ValidationState` literal and `ValidationOutcome` dataclass to new `src/services/validation_service.py` (stub file — class body filled in Phase 2)
- [ ] T002 Add `validation_enabled: bool = True` field to `AdvancedSettings` in `src/config.py`
- [ ] T003 [P] Add `ValidationState` type alias and extend `Candidate` interface with optional `validation_state` field in `src/web/frontend/src/types/index.ts`
- [ ] T004 [P] Extend `AnalysisProgress` TypeScript interface with `validation_queue_size`, `validation_outcomes`, and `review_ready` fields in `src/web/frontend/src/types/index.ts`

**Checkpoint**: Shared types and config ready — all phases can proceed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core `ValidationService` implementation and analysis pipeline wiring. Must be complete before US1 backend work begins.

**⚠️ CRITICAL**: US1 analysis integration (T009–T011) depends on this phase

- [ ] T005 Implement full `ValidationService` class body in `src/services/validation_service.py` — `start()`, `stop()`, `wait()`, `enqueue()`, `get_outcomes()`, `queue_size()`; rate-limited worker thread (1 req/sec), `urllib.request` HTTP check, `threading.Lock`-protected outcomes dict
- [ ] T006 Add `on_candidate_discovered: Callable[[str], None] | None = None` parameter to `AnalysisService.analyze()` in `src/services/analysis_service.py`; maintain `seen_normalized: set[str]` locally; fire callback on first occurrence of each unique normalized spelling
- [ ] T007 [P] Extend `AnalysisRunState` dataclass in `src/web/app/analysis_adapter.py` with `validation_outcomes: dict[str, dict] | None = None`, `validation_queue_size: int = 0`, `review_ready: bool = False`; add `set_validation_state()` method
- [ ] T008 [P] Write unit tests for `ValidationService` in `tests/unit/test_validation_service.py` — cover: queue deduplication (same spelling enqueued twice → one HTTP call), rate limiting (≥1 sec between dispatches), outcome mapping (200→found, 404→not_found, 5xx→failed, timeout→failed), `stop()`+`wait()` drain behaviour

**Checkpoint**: `ValidationService` fully tested; analysis pipeline ready for wiring

---

## Phase 3: User Story 1 — Validate Candidates During Analysis (Priority: P1) 🎯 MVP

**Goal**: Detected candidate spellings are validated concurrently with scanning; results influence recommendation scores and persist in the sidecar; the frontend shows live validation progress.

**Independent Test**: Run analysis with validation enabled on a video with multiple unique candidate spellings. Verify each spelling is validated at most once, recommendation ordering reflects found vs not-found, and reopening review shows persisted outcome icons.

### Implementation for User Story 1

- [ ] T009 [US1] Wire `ValidationService` into `work()` in `src/web/api/routes/analysis.py` — instantiate service when `validation_enabled`, pass `on_candidate_discovered=service.enqueue` to `analyze()`, call `service.stop()` after scan, periodically call `adapter.set_validation_state()` until queue drains
- [ ] T010 [US1] Extend `GET /api/analysis/progress/{run_id}` response in `src/web/api/routes/analysis.py` to include `review_ready`, `validation_queue_size`, and `validation_outcomes` fields per contracts/api.md
- [ ] T011 [US1] Extend `score_candidate()` in `src/web/app/recommendation_service.py` to accept optional `validation_state` and apply +20 (found) / −10 (not_found) signal; guard with `min(100.0, ...)` and `max(0.0, ...)`
- [ ] T012 [US1] Add `update_validation_outcomes()` to `ReviewSidecarStore` (or equivalent sidecar writer) so validation outcomes are persisted to `result_<n>.review.json` under the `validation_outcomes` key; load on reopen
- [ ] T013 [US1] Update `AnalysisPage.tsx` in `src/web/frontend/src/pages/AnalysisPage.tsx` to handle `review_ready: true` (enable "View Results" button / navigate to review page) and display validation queue progress while `validation_queue_size > 0`
- [ ] T014 [US1] Update `ReviewPage.tsx` in `src/web/frontend/src/pages/ReviewPage.tsx` to continue polling the progress endpoint while `validation_queue_size > 0` and apply live outcome updates to candidate cards
- [ ] T015 [US1] Update `CandidateRow.tsx` in `src/web/frontend/src/components/CandidateRow.tsx` to render the validation state icon (Material Symbol) per the Stitch design — `check_circle` green, `person_off` amber, `progress_activity` grey animated, `error_outline` red, no icon for `unchecked`; follow `specs/014-rsi-player-validation/stitch/review-expanded-candidate-group-validation-states.html`
- [ ] T016 [US1] Add unit tests for `score_candidate()` validation signal in `tests/unit/test_recommendation_service.py` — found/not_found/unchecked/None inputs, cap behaviour

**Checkpoint**: US1 fully functional — analysis validates candidates, scores reflect outcomes, review shows live icons, sidecar persists results

---

## Phase 4: User Story 2 — Validation Toggle in Analysis Settings (Priority: P2)

**Goal**: The analysis settings panel includes a "Validate player names (RSI)" toggle; when disabled, zero external requests are made and candidates show `unchecked` state.

**Independent Test**: Disable validation toggle, run analysis, confirm no HTTP requests to RSI, confirm all candidate cards show neutral/unchecked state, confirm other analysis outputs are unaffected.

### Implementation for User Story 2

- [ ] T017 [US2] Add `validation_enabled` toggle to `AnalysisSettingsPanel.tsx` in `src/web/frontend/src/components/AnalysisSettingsPanel.tsx` — primary label "Validate player names", subtitle "Checks detected names against robertsspaceindustries.com during analysis (1 req/sec)", toggle ON by default; follow `specs/014-rsi-player-validation/stitch/analysis-view-validation-toggle.html`
- [ ] T018 [US2] Pass `validation_enabled` value from `AnalysisSettingsPanel` through to the `POST /api/analysis/start` request body in `src/web/frontend/src/pages/AnalysisPage.tsx` (or api client layer)
- [ ] T019 [US2] Persist `validation_enabled` preference in `AdvancedSettings` (`src/config.py`) and load it into the settings panel on page load
- [ ] T020 [US2] Guard `ValidationService` instantiation in `work()` (`src/web/api/routes/analysis.py`) so the service is not created and `on_candidate_discovered` is not wired when `validation_enabled=False`; confirm `validation_queue_size=0` is returned in progress responses

**Checkpoint**: US2 functional — toggle appears in settings, disabling it produces zero RSI requests and neutral candidate icons

---

## Phase 5: User Story 3 — Recheck Individual Candidates in Review (Priority: P3)

**Goal**: Reviewers can trigger a one-off validation check on any candidate card (including manually edited names); only that card updates; failure is non-blocking.

**Independent Test**: Open review, edit a candidate spelling, click "Re-check", confirm the icon updates to found/not-found/failed only for that candidate, confirm other candidates are unaffected and review remains navigable.

### Implementation for User Story 3

- [ ] T021 [US3] Implement `POST /api/review/candidates/{candidate_id}/validate` endpoint in `src/web/api/routes/review_actions.py` — resolve current spelling from sidecar, synchronous `urllib.request` HTTP check (10-sec timeout), write updated `ValidationOutcome` to sidecar, return outcome; per contracts/api.md
- [ ] T022 [US3] Register the new recheck route in `src/web/api/router.py`
- [ ] T023 [US3] Add "Re-check" text button to `CandidateRow.tsx` in `src/web/frontend/src/components/CandidateRow.tsx` — visible for `found`/`not_found`/`failed` states, hidden during `checking`; clicking calls the validate endpoint and updates only that card's icon; follow Stitch design
- [ ] T024 [US3] Add integration test for the recheck endpoint in `tests/integration/test_validation_api.py` — happy path (found, not-found), timeout (failed), invalid candidate_id (404)

**Checkpoint**: US3 functional — individual recheck works for any candidate in any state; review unblocked on failure

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Wiring correctness, edge cases, and final integration checks across all stories

- [ ] T025 [P] Verify recommendation call sites in `src/web/api/routes/` pass `validation_state` from sidecar into `score_candidate()` when recommendations are computed at review-ready time
- [ ] T026 [P] Add `reviewed_at` / `source` fields when writing `ValidationOutcome` to sidecar (ensure `analysis_batch` vs `manual_review` source is recorded correctly per data-model.md)
- [ ] T027 Handle polling teardown in `ReviewPage.tsx` — stop polling the progress endpoint once `validation_queue_size == 0` and `status == completed` to avoid unnecessary requests
- [ ] T028 [P] Validate settings round-trip: `validation_enabled` persists to `scytcheck_settings.json` and reloads correctly on app restart
- [ ] T029 Run full quickstart validation per `specs/014-rsi-player-validation/quickstart.md` — confirm all three user stories pass their independent tests end-to-end

---

## Dependency Graph

```
T001 (ValidationState/Outcome dataclass)
T002 (AdvancedSettings.validation_enabled)
T003/T004 (TS types)
    └── Phase 2 (T005–T008)
            ├── T005 (ValidationService impl)
            │       └── T008 (unit tests — can run alongside T006/T007)
            ├── T006 (analyze() callback)
            └── T007 (AnalysisRunState fields)
                    └── Phase 3 (US1 — T009–T016)
                            ├── T009 (wire service into work())
                            ├── T010 (progress endpoint extension)
                            ├── T011 (score_candidate +20/-10)
                            ├── T012 (sidecar persistence)
                            ├── T013 (AnalysisPage review_ready)
                            ├── T014 (ReviewPage live polling)
                            ├── T015 (CandidateRow icons)
                            └── T016 (recommendation unit tests)
                    Phase 4 (US2) — independent of US1 for backend toggle guard;
                            T017/T018 independent; T019 after T002; T020 after T009
                    Phase 5 (US3) — independent of US1/US2 (separate endpoint)
                            T021 (recheck endpoint)
                            T022 (router registration)
                            T023 (Re-check button — after T015)
                            T024 (integration tests)
                    Phase 6 (Polish) — after all story phases complete
```

## Parallel Execution Examples

**Within Phase 3 (US1)**:
```
T009 ──────────────────────── sequential
T010 ────── parallel with T009 (different file)
T011 ────── parallel with T009 (different file)
T012 ────── parallel with T011 (different file)
T013 ──┐
T014 ──┤ parallel (different files, all depend on T010)
T015 ──┘
T016 ────── parallel (tests, after T011)
```

**US2 vs US1 frontend tasks**:
```
T017 (AnalysisSettingsPanel toggle) — parallel with T015 (CandidateRow)
T018 (AnalysisPage payload) — parallel with T013 (AnalysisPage review_ready handling)
```

**US3 vs US2**:
```
T021+T022 (recheck endpoint) — fully parallel with all US2 tasks
T023 (Re-check button) — after T015 (icon rendering done)
```

## Implementation Strategy

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (US1) delivers the core value — validation runs during analysis, outcomes influence recommendations, review shows live icons, results persist.

**Recommended delivery order**:
1. Phase 1 (types + config) — fast, unblocks everything
2. Phase 2 (ValidationService + analysis callback) — backend core
3. Phase 3 US1 — primary user value; can be demonstrated end-to-end
4. Phase 4 US2 — user control (toggle); small delta on top of US1
5. Phase 5 US3 — manual recheck; independent of US1/US2 backend
6. Phase 6 — polish and final verification
