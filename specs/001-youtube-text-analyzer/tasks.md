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