# Tasks: PaddleOCR Migration

**Input**: Design documents from `/specs/003-paddleocr-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: No new test-first tasks are generated; tests are not explicitly requested by the feature specification. Existing integration tests are updated as part of the relevant implementation tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Dependency declarations and directory scaffolding needed by all subsequent phases.

- [X] T001 Update requirements.txt to add `paddleocr` and `paddlepaddle` (CPU) entries alongside existing dependencies
- [X] T002 [P] Create third_party/paddleocr/x64/ directory with README.md documenting how to populate model assets for local builds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Configuration discovery and settings migration logic that both OCR engine replacement (US1) and workflow regression safety (US2) depend on.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Add `paddleocr_model_root` field and `_discover_paddleocr_model_root()` helper to `AppConfig` in src/config.py (mirrors existing `_discover_tesseract_command()` pattern; resolves frozen-app-relative path first, then fallback)
- [X] T004 [P] Update safe settings deserialization in src/config.py to ignore obsolete `tesseract_cmd` and `tessdata_prefix` fields on load without raising errors and to serialize `paddleocr_model_root` to `scytcheck_settings.json`

**Checkpoint**: Config foundation is ready; user story implementation can now begin.

---

## Phase 3: User Story 1 - Better Name Extraction Accuracy (Priority: P1) 🎯 MVP

**Goal**: Replace `pytesseract.image_to_data` with the PaddleOCR Python API and normalize its output into the existing line-oriented token format so downstream matching and export behavior improves without interface changes.

**Independent Test**: Run the existing OCR quality integration tests and the maintainer baseline comparison script against the maintained reference recording set. Confirm reduction in missed player names and false positives per SC-001 and SC-002.

### Implementation for User Story 1

- [X] T005 [US1] Replace `pytesseract.image_to_data` with `PaddleOCR` initialization and inference in src/services/ocr_service.py; initialize with explicit local model dirs from `AppConfig.paddleocr_model_root` and disable unused orientation/unwarping pipeline stages
- [X] T006 [US1] Normalize PaddleOCR prediction output into line-oriented text entries in src/services/ocr_service.py using the existing `_build_line_entries` contract; preserve region crop input and return type compatibility
- [X] T007 [US1] Map PaddleOCR float confidence scores (0.0–1.0) to 0–100 integer range and apply existing `confidence_threshold` filtering in src/services/ocr_service.py
- [X] T008 [P] [US1] Create scripts/validate_ocr_baseline.py as the repeatable maintainer quality comparison tool for FR-011; accepts baseline and candidate CSV result paths and outputs missed-detection and false-positive delta per SC-001

**Checkpoint**: User Story 1 is independently testable. PaddleOCR produces results; comparison script enables quality gate validation.

---

## Phase 4: User Story 2 - No Workflow Regression For Existing Users (Priority: P2)

**Goal**: Ensure existing end-to-end workflow, settings compatibility, and output schemas are preserved after the engine swap.

**Independent Test**: Run the full workflow integration test suite (`test_us1_workflow.py`, `test_output_schema_sc004_sc005.py`, `test_log_schema_fr049.py`) and confirm all pass with the PaddleOCR path active and no schema regressions.

### Implementation for User Story 2

- [X] T009 [US2] Implement OCR initialization failure detection and user-facing error dialog in src/services/ocr_service.py (FR-007); missing bundled assets or paddle init errors must surface a clear message and must not fail silently
- [X] T010 [P] [US2] Verify tests/integration/test_us1_workflow.py, tests/integration/test_output_schema_sc004_sc005.py, and tests/integration/test_log_schema_fr049.py pass with PaddleOCR active; update only engine-specific mocks/fixtures where required

**Checkpoint**: User Story 2 is independently testable. Existing workflow and output schemas remain intact.

---

## Phase 5: User Story 3 - Portable Package Remains Self-Contained (Priority: P2)

**Goal**: Update the portable build pipeline so the Windows ZIP bundles all PaddleOCR runtime dependencies and local model files needed for fully offline analysis.

**Independent Test**: Run the release bundle integration test and perform the clean-machine portable verification from quickstart.md section 6. Confirm OCR works from the extracted ZIP with no network activity.

### Implementation for User Story 3

- [X] T011 [US3] Create scripts/download_paddleocr_models.ps1 to fetch and stage PaddleOCR detection and recognition model files (en + de) into third_party/paddleocr/x64/
- [X] T012 [US3] Update build-config.spec to replace `collect_submodules("pytesseract")` with `paddleocr` and `paddlepaddle` hidden imports and add `datas` entries pointing bundled model dirs from third_party/paddleocr/x64/ into the packaged resource root
- [X] T013 [US3] Add `Copy-OptionalTree` block for PaddleOCR asset staging in scripts/release/build.ps1 mirroring the existing ffmpeg/tesseract pattern (`$paddleocrSource`, `$paddleocrDestination`, `'PaddleOCR'` label)
- [X] T014 [P] [US3] Update tests/integration/test_release_bundle_fr010_fr013.py to assert the PaddleOCR `Copy-OptionalTree` pattern is present in build.ps1; adapt or retain existing tesseract assertions as appropriate

**Checkpoint**: All three user stories are independently functional and testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Lint, final regression validation, and acceptance confirmation.

- [X] T015 [P] Run `ruff check src tests --select=E,F,W` and resolve any lint issues introduced on changed files (src/services/ocr_service.py, src/config.py, scripts/)
- [X] T016 Run full test suite and quickstart.md acceptance checklist (`pytest tests/ -q`); confirm all SC-001 through SC-005 criteria are met before release
- [X] T017 Add local-only OCR dependency validation for FR-010: confirm runtime OCR path has no account/API-key/paid-service requirement and no cloud OCR fallback references in configuration or initialization

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — blocks all user stories
- **User Stories (Phases 3–5)**: All depend on Phase 2 completion
  - US1 (Phase 3), US2 (Phase 4), and US3 (Phase 5) can proceed in parallel after Phase 2
  - US2 depends on US1 being functionally complete (needs PaddleOCR active to verify no regression)
  - US3 depends on US1 being complete (needs working OCR to validate offline bundling)
- **Polish (Phase 6)**: Depends on all user story phases complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependency on US2 or US3
- **US2 (P2)**: Requires US1 to have an active PaddleOCR path before workflow regression can be confirmed
- **US3 (P2)**: Requires US1 to have working initialization logic before packaging can be fully validated

### Within Each User Story

- T005 → T006 → T007 (sequential; each builds on the prior OCR output shape)
- T008 is independent of T005–T007, can run in parallel
- T009 and T010 are independent within US2
- T011 → T012 → T013 → T014 (sequential; model files must exist before build spec and script reference them, test runs last)

### Parallel Opportunities

- T003 and T004 can run in parallel (both in src/config.py but in distinct functions)
- T008 (validation script) can be written in parallel with T005–T007
- T010 (workflow and output regression verification) can run in parallel with T009
- T015 (lint) can run in parallel with any final manual verification

---

## Parallel Example: User Story 1

```text
# Sequential core (must be ordered):
T005 → Replace pytesseract with PaddleOCR in src/services/ocr_service.py
T006 → Normalize output into _build_line_entries format in src/services/ocr_service.py
T007 → Map confidence scores and apply threshold in src/services/ocr_service.py

# In parallel with T005–T007:
T008 → Create scripts/validate_ocr_baseline.py (FR-011 validation tool)
```

## Parallel Example: User Story 3

```text
# Must be ordered:
T011 → Create download_paddleocr_models.ps1 and stage models to third_party/paddleocr/x64/
T012 → Update build-config.spec with hidden imports and datas
T013 → Update build.ps1 with Copy-OptionalTree block

# After T013, independently:
T014 → Update test_release_bundle_fr010_fr013.py assertions
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T004)
3. Complete Phase 3: User Story 1 (T005–T008)
4. **STOP AND VALIDATE**: Run reference recordings through both engine paths; confirm SC-001 improvement threshold
5. Proceed to US2 and US3 only after quality gate is passed

### Incremental Delivery

1. Setup + Foundational → Config and discovery ready
2. User Story 1 → PaddleOCR produces results + baseline comparison available (MVP)
3. User Story 2 → End-to-end workflow and output schemas confirmed
4. User Story 3 → Portable ZIP fully self-contained and offline-capable
5. Polish → Clean lint, full regression pass, release-ready

### Single-Developer Sequence

```text
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008
  → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017
```
