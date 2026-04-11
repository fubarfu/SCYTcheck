# Implementation Tasks: YouTube Text Analyzer

**Feature**: `001-youtube-text-analyzer`  
**Date Generated**: April 11, 2026  
**Total Tasks**: 35  
**Spec**: [specs/001-youtube-text-analyzer/spec.md](spec.md)  
**Plan**: [specs/001-youtube-text-analyzer/plan.md](plan.md)  

---

## Story Roadmap & Dependencies

### Execution Strategy
1. **Phase 1 (Setup)**: T001–T003 — Initialize environment and verify baselines
2. **Phase 2 (Foundational)**: T004–T007 — Establish core models, config, export pipelines
3. **Phase 3 (US1 - P1)**: T008–T014 — Implement scrollbar navigation, auto-filename, folder validation
4. **Phase 4 (US2 - P2)**: T015–T019 — Polish UI for folder selection and user feedback
5. **Final Phase**: T020–T028 — Packaging, code signing, distribution, testing

### User Story Parallelization
- US1 and US2 are **independent** after Phase 2 foundational tasks complete
- US1 focus: region_selector.py, export_service.py (new scrollbar + filename generation)
- US2 focus: file_selector.py, main_window.py (folder validation + error messages)
- Packaging tasks (T020–T028) can begin after US1 + US2 implementation complete

### Suggested MVP Scope
**Minimum Viable Product (v1.0)**: T001–T019 (Phases 1–4)
- Setup, foundational fixes, US1 core, US2 basic UI
- Deploy unpackaged (dev mode only)

**Production Release (v1.1)**: T020–T028 (Final Phase)
- PyInstaller bundling, code signing, distribution validation

---

## Phase 1: Setup & Environment

- [ ] T001 Configure Python 3.11 virtual environment in workspace
- [ ] T002 Install core dependencies: opencv-python, pytesseract, yt-dlp, pytest
- [ ] T003 Verify existing app runs without errors and unit tests pass

---

## Phase 2: Foundational Infrastructure

- [ ] T004 Extend Region model to support time-based seeking and frame_time metadata in src/data/models.py
- [ ] T005 [P] Update export_service.py to accept output_folder parameter instead of full_file_path
- [ ] T006 [P] Add output folder validation utility in src/services/export_service.py with error handling
- [ ] T007 Create mock video frame utilities and fixtures in tests/unit/ for offline testing

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1)

**Story Goal**: User inputs YouTube URL, defines regions on a video frame navigable via time scrollbar, and receives a CSV with detected text strings.

**Independent Test Criteria**:
1. Scrollbar appears in region selection window spanning full video duration in seconds
2. User can drag scrollbar to arbitrary time; frame updates within 500ms
3. Auto-generated CSV filename follows pattern scytcheck_<videoId>_<YYYYMMDD-HHMMSS>.csv
4. Analysis completes for 10-minute video in under 5 minutes
5. Output folder validation aborts with clear error message if folder invalid

### Implementation Tasks

- [ ] T008 [P] [US1] Add time-based horizontal scrollbar to region_selector.py for frame navigation
- [ ] T009 [P] [US1] Extend video_service.py to support seek-to-time and frame extraction at arbitrary timestamps
- [ ] T010 [US1] Implement auto-filename generation logic in export_service.py (scytcheck_<videoId>_<DateTime>.csv)
- [ ] T011 [US1] Add output folder existence and write-permission checks with user-friendly error dialog in export_service.py
- [ ] T012 [P] [US1] Unit tests for scrollbar time-value mapping and frame sync in tests/unit/test_region_selector.py
- [ ] T013 [P] [US1] Unit tests for filename generation with various video IDs and timestamps in tests/unit/test_export_service.py
- [ ] T014 [US1] Integration test: full workflow (URL input → region selection with scrollbar → analysis → CSV export) in tests/integration/

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Story Goal**: User selects an output folder (not filename) with app providing clear feedback and auto-naming the CSV.

**Independent Test Criteria**:
1. File selector dialog appears in folder-only mode on app startup
2. Selected folder path is validated and displayed/stored
3. User receives error message if folder is invalid
4. Auto-generated filename is displayed to user before/after analysis

### Implementation Tasks

- [ ] T015 [P] [US2] Verify file_selector.py uses folder-only picker mode (no manual filename entry)
- [ ] T016 [P] [US2] Add user-friendly error messages for folder validation failures in src/components/file_selector.py
- [ ] T017 [US2] Update main_window.py to display auto-generated filename to user before analysis starts
- [ ] T018 [P] [US2] Unit tests for folder selector behavior and error conditions in tests/unit/test_file_selector.py
- [ ] T019 [US2] Integration test: input URL → select folder → see displayed filename → analyze → verify output in tests/integration/

---

## Phase 5: Packaging & Distribution

**Prerequisites**: US1 + US2 implementation complete; all unit and integration tests passing.

### PyInstaller Setup & Configuration

- [ ] T020 Create PyInstaller spec file (build-config.spec) with python 3.11, opencv, pytesseract, tkinter, yt-dlp imports and onedir mode
- [ ] T021 [P] Add build automation script to bundle FFmpeg binaries into dist/ffmpeg/ folder post-build
- [ ] T022 [P] Add build automation script to copy Tesseract exe and tessdata/ into dist/tesseract/ folder post-build
- [ ] T023 [P] Configure pytesseract path detection at app startup in src/main.py to use bundled dist/tesseract/tesseract.exe

### Code Signing & Executable Preparation

- [ ] T024 Create self-signed code-signing certificate for dev/testing environment
- [ ] T025 Implement signtool automation script to sign dist/main.exe with SHA-256 timestamp
- [ ] T026 Verify signed executables pass Windows SmartScreen on clean test machine

### Cross-Architecture Builds

- [ ] T027 [P] Build x64 executable using 64-bit Python 3.11
- [ ] T028 [P] Build x86 executable using 32-bit Python 3.11
- [ ] T029 [P] Generate x64 distribution ZIP: scytcheck-x64-v1.1.zip
- [ ] T030 [P] Generate x86 distribution ZIP: scytcheck-x86-v1.1.zip

### Distribution Testing & Validation

- [ ] T031 Test x64 package on clean Windows 10/11 64-bit VM (fresh OS, no preinstalled deps)
- [ ] T032 Test x86 package on clean Windows 32-bit environment if available; document limitations
- [ ] T033 Validate CSV output identical across bundled and dev versions
- [ ] T034 Validate scrollbar frame navigation responsive on bundled version

### Documentation & Release

- [ ] T035 Update README.md with bundled distribution installation instructions, system requirements, and supported Windows versions

---

## Task Count by User Story

| Story | Task Range | Count | Parallel Safe |
|-------|-----------|-------|---|
| Setup | T001–T003 | 3 | 2/3 |
| Foundational | T004–T007 | 4 | 2/4 |
| **US1 (P1)** | **T008–T014** | **7** | **5/7** |
| **US2 (P2)** | **T015–T019** | **5** | **4/5** |
| Packaging | T020–T035 | 16 | 8/16 |
| **Total** | **T001–T035** | **35** | **~20 parallelizable** |

---

## Parallel Execution Examples

### Parallel Set 1 (Early Phase 3)
```
- T008: Add scrollbar UI
- T009: Extend video_service for seek
- T010: Auto-filename generation
- T011: Folder validation
  (All can start after T004–T007 complete)
```

### Parallel Set 2 (Phase 4, independent of US1)
```
- T015: Verify folder-only mode
- T016: Error messages
- T017: Display filename
- T018–T019: Tests
  (Can overlap with US1 implementation)
```

### Parallel Set 3 (Build & Distribution)
```
- T021: FFmpeg bundling
- T022: Tesseract bundling
- T024: Create signing cert
- T027: x64 build
- T028: x86 build
  (Builds can proceed independently after config ready)
```

---

## Quality Gates

| Gate | Task | Requirement |
|------|------|---|
| Pre-Phase 3 | T003 | All existing tests pass |
| Pre-Phase 4 | T014 | US1 integration test passes |
| Pre-Packaging | T019 | US2 integration test passes |
| Pre-Release | T034 | Bundled package testing complete |

---

## Estimated Timeline

- **Phase 1–2** (Setup + Foundational): 2–3 days
- **Phase 3** (US1 implementation): 5–7 days
- **Phase 4** (US2 implementation): 3–4 days
- **Phase 5** (Packaging + Distribution): 7–10 days
- **Total**: 17–24 days for full implementation + release

---

## Notes

- All tasks follow strict checklist format: `- [ ] [ID] [P?] [Story?] Description with file path`
- **[P]** indicates task can run in parallel with others at same phase level
- **[US1]** / **[US2]** indicates which user story the task belongs to
- Phases 3 and 4 can overlap after Phase 2 foundational tasks complete
- Packaging tasks (Phase 5) are gated by Phase 3–4 completion
- MVP scope: complete Phases 1–4 only; Phase 5 for production release only
# Tasks: YouTube Text Analyzer

**Input**: Design documents from `/specs/001-youtube-text-analyzer/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL - not requested in specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with opencv-python, pytesseract, yt-dlp, tkinter dependencies
- [X] T003 [P] Configure linting and formatting tools (ruff, black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create base data models (VideoAnalysis, TextString) in src/data/models.py
- [X] T005 [P] Setup error handling and logging infrastructure in src/services/logging.py
- [X] T006 [P] Configure environment configuration management in src/config.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Analyze YouTube Video for Text Strings (Priority: P1) 🎯 MVP

**Goal**: Enable users to input a YouTube URL, define regions, and extract text strings to CSV

**Independent Test**: Provide YouTube URL, select region on frame, run analysis, verify CSV contains detected text with positions

### Implementation for User Story 1

- [X] T007 [P] [US1] Implement video streaming service in src/services/video_service.py
- [X] T008 [P] [US1] Implement OCR service in src/services/ocr_service.py
- [X] T009 [US1] Create region selection component in src/components/region_selector.py
- [X] T010 [US1] Implement analysis logic in src/services/analysis_service.py (depends on T007, T008)
- [X] T011 [US1] Add CSV export functionality in src/services/export_service.py
- [X] T012 [US1] Add progress feedback UI component in src/components/progress_display.py
- [X] T013 [US1] Integrate components in main analysis workflow in src/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Easy Input and Output Handling (Priority: P2)

**Goal**: Provide simple UI for URL input and output file selection

**Independent Test**: Launch app, enter URL, select output path, verify inputs are stored correctly

### Implementation for User Story 2

- [X] T014 [P] [US2] Create URL input component in src/components/url_input.py
- [X] T015 [P] [US2] Create file output selector component in src/components/file_selector.py
- [X] T016 [US2] Implement main UI layout in src/components/main_window.py
- [X] T017 [US2] Integrate UI components with analysis workflow in src/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T018 [P] Documentation updates in README.md
- [X] T019 Code cleanup and refactoring
- [X] T020 Performance optimization across all stories
- [X] T021 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all services for User Story 1 together:
Task: "Implement video streaming service in src/services/video_service.py"
Task: "Implement OCR service in src/services/ocr_service.py"

# Launch analysis and export together:
Task: "Implement analysis logic in src/services/analysis_service.py"
Task: "Add CSV export functionality in src/services/export_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence