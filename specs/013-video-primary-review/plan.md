# Implementation Plan: Video-Primary Review Flow

**Branch**: `013-create-spec-branch` | **Date**: 2026-04-28 | **Spec**: [specs/013-video-primary-review/spec.md](spec.md)
**Input**: Feature specification from `/specs/013-video-primary-review/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Redesign the review workflow to treat video as the primary unit instead of result files. Users will open analysis, see a progress window indicating whether a new project is created or results are merged, and automatically transition to review after analysis completes. In review, all outputs for the analyzed video are combined into one context with visual markers for newly detected candidates (differing spelling only). Project location shifts from per-run setting to a global configuration accessible via settings. The former History view becomes a Videos view for managing projects from the configured location with filesystem-based discovery (no app-level history retained).

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript/React (Vite, frontend)  
**Primary Dependencies**: Backend: `opencv-python`, `paddleocr`, `yt-dlp`, `thefuzz`, `numpy`; Frontend: React, Vite, Material Symbols, TypeScript  
**Storage**: CSV outputs + JSON sidecar per video; local JSON settings (`%APPDATA%/SCYTcheck/scytcheck_settings.json`, fallback to local)  
**Testing**: pytest (backend), vitest (frontend)  
**Target Platform**: Web application (React SPA served from Python backend at localhost:8765)  
**Project Type**: Web application (desktop-class SPA)  
**Performance Goals**: Instant view switching, <1s analysis completion messaging  
**Constraints**: <2s auto-open to review after analysis; no database (files only)  
**Scale/Scope**: 10+ UI screens, multi-run per video, sub-second candidate lookup  

**Google Stitch Integration**: Use existing stitch/ project for design decisions. UI screens, design system, and visual hierarchy SHALL be authored in Stitch. Implementation adapts only where technical constraints require, documented in PRs.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Simple, Modular Design**: The plan removes per-run project settings (reducing state coupling) and centralizes project location config. Video becomes the scoping unit, simplifying data flow. Unmarked complexity: none identified.

✅ **Testing Requirements**: Non-trivial business logic requiring tests:
  - Candidate freshness detection (spelling-based comparison across runs)
  - Review context merging (conflict resolution: prior human decision wins)
  - Project discovery from filesystem (directory scanning + metadata extraction)
  - Auto-redirect after analysis (timing synchronization)
  - Progress window messaging (project create vs. merge state)

✅ **Google Stitch as UI Design Authority**: 
  - Existing Stitch project at `specs/013-video-primary-review/stitch/` SHALL be the source of truth for all web UI decisions.
  - Analysis view, Review view, Videos view, and Settings view SHALL be designed in Stitch first.
  - Visual hierarchy, component structure, interaction flow, and design system usage SHALL follow approved Stitch screens.
  - Implementation deviations SHALL be documented in PR commit messages with technical justification (e.g., accessibility, performance, browser compatibility).

✅ **Dependencies**: No new third-party dependencies proposed. Uses existing tech stack (React, Python, CSV/JSON).

**Deviations Planned**: None at this stage. All design decisions will be Stitch-driven.

## Project Structure

### Documentation (this feature)

```text
specs/013-video-primary-review/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── stitch/              # Google Stitch UI design project (design authority)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── main.py                      # FastAPI app entry
├── config.py                    # App configuration (project location settings)
├── services/
│   ├── analysis_service.py      # Analysis orchestration
│   ├── export_service.py        # Result export to CSV
│   ├── history_service.py       # [MODIFIED] Video project discovery from filesystem
│   ├── video_service.py         # Video metadata + project structure
│   ├── ocr_service.py           # OCR orchestration
│   └── logging.py               # Logging with sidecar streaming
├── data/
│   └── models.py                # Data entities (Video, Project, Run, Candidate, etc.)
└── web/
    ├── api/                     # [NEW] REST endpoints for web UI
    │   ├── analysis.py          # POST /api/analysis/start, /api/analysis/progress
    │   ├── review.py            # GET /api/review/context, PUT /api/review/action
    │   ├── projects.py          # GET /api/projects, POST /api/project/settings
    │   └── settings.py          # GET /api/settings, PUT /api/settings
    ├── app/                     # [NEW] Backend SPA serving logic
    └── frontend/                # React/TypeScript SPA (Vite)
        ├── src/
        │   ├── pages/
        │   │   ├── AnalysisPage.tsx     # [MODIFIED] Remove output-filename input
        │   │   ├── ReviewPage.tsx       # [MODIFIED] Combined view, auto-open, new markers
        │   │   ├── VideosPage.tsx       # [RENAMED] From History
        │   │   ├── SettingsPage.tsx     # [NEW] Project location config
        │   │   └── MainLayout.tsx       # [MODIFIED] Add settings gear icon
        │   ├── components/
        │   │   ├── ProgressWindow.tsx   # [NEW] Project create/merge messaging
        │   │   ├── CandidateList.tsx    # [MODIFIED] Add "new" visual marker
        │   │   └── ...
        │   ├── services/
        │   │   └── api.ts               # REST client for backend API
        │   └── styles/
        │       └── app.css
        └── dist/                # Built SPA (served by Flask at /static/)

tests/
├── contract/                    # API contract tests (Stitch-validated)
│   └── test_api_013.py
├── integration/                 # End-to-end workflow tests
│   └── test_video_primary_flow.py
└── unit/
    ├── test_candidate_freshness.py      # Spelling-based newness detection
    ├── test_review_context_merge.py     # Conflict resolution
    └── test_project_discovery.py        # Filesystem scanning

spec/013-video-primary-review/stitch/     # Google Stitch design authority
```

**Structure Decision**: Web application (backend + frontend). Analysis, Review, and Videos flows are web-first. Stitch project `specs/013-video-primary-review/stitch/` is the UI design authority; all screen definitions originate there.

## Complexity Tracking

> **No violations identified.** All complexity is justified by feature requirements and reduces overall per-run friction.

| Aspect | Justification |
| ------ | ------------- |
| Multi-run merging | Required by user story 1 (auto-load combined context); essential for continuous analysis workflow |
| Conflict resolution (prior-reviewed-wins) | Required by user story 1 acceptance scenario 4; preserves user trust in prior decisions |
| Filesystem project discovery | Required by user story 3 acceptance scenario 5; avoids app-level history maintenance |
| Progress messaging (create vs. merge) | Required by clarification 5; gives users critical context during long-running analysis |
| Candidate freshness (spelling-based) | Required by user story 2; provides necessary differentiation without false positives |
| Settings view + gear icon | Required by user story 3; centralizes project configuration, reduces analysis UI clutter |

---

## Phase 0: Research & Clarifications

**Status**: Starting. Dependencies resolved via clarification in spec phase. Moving to design.

### Pre-Existing Clarifications Resolved (Spec Phase)

All major design questions have been clarified:

1. ✅ App-level history not retained → filesystem-based project discovery only
2. ✅ Default project location → used automatically on first run
3. ✅ Conflict resolution → prior human-reviewed status wins
4. ✅ Candidate freshness duration → marked until user action
5. ✅ Candidate freshness trigger → spelling difference only
6. ✅ Progress messaging + auto-open → progress window shows create/merge; review opens after analysis

**Transition**: All research inputs are satisfied. No blocking unknowns remain for Phase 1 design.

---

## Phase 1: Design & Contracts

### 1.1 Data Model Design

**Deliverable**: `data-model.md` (generated next)

**Design Activities**:

1. **Video Project Entity**: Define structure for per-video storage
   - Video metadata (URL, original filename, added timestamp)
   - Analysis run records (ordered list, run metadata, output references)
   - Merged review state (combined candidates, groups, freshness flags)

2. **Candidate Freshness State**: Design spelling-based comparison logic
   - Candidate entity: spelling, source (run_id), discovered_run, marked_new (boolean)
   - Freshness marker logic: compare new spelling against all prior runs for same video

3. **Review Conflict Resolution**: Design prior-decision-wins algorithm
   - Per-candidate reviewed status (human decision overrides analysis)
   - Merge conflict: latest analysis + prior decision = merged state

4. **Project Location Config**: Design settings storage
   - App-level: default project location (file path)
   - Per-user: configurable project location (stored in scytcheck_settings.json)
   - Fallback: if configured location unavailable, show error + recovery path

5. **API Contracts**: Define backend ↔ frontend interfaces
   - POST /api/analysis/start: start analysis, track project create/merge status
   - GET /api/analysis/progress: return project status message
   - GET /api/review/context: return merged candidates + freshness flags for video
   - GET /api/projects: list projects from configured location
   - PUT /api/settings: update project location config

### 1.2 UI Design Authority: Google Stitch

**Action**: Use Google Stitch MCO tools to design required screens in the existing Stitch project at `specs/013-video-primary-review/stitch/`.

**Stitch Design Tasks**:

1. **Analysis View** (modify existing)
   - Remove: output filename input field
   - Add: progress window with project create/merge messaging
   - Add: visual indicator of analysis in progress
   - Add: messaging that review will auto-open

2. **Review View** (modify existing)
   - Remove: manual result-file load action
   - Modify: video URL shown as read-only context (not filename input)
   - Add: candidate list with freshness markers for new candidates
   - Add: group merge conflict visualization (if prior reviewed decision differs from latest)

3. **Videos View** (rename from History)
   - Remove: session history strip
   - Add: list of projects from configured location
   - Add: "open project" action for each
   - Add: project metadata (video URL, run count, last analyzed date)

4. **Settings View** (new)
   - Add: project location config field
   - Add: validation feedback (path exists, writable)
   - Add: recovery guidance if configured location is unavailable

5. **Main Layout** (modify)
   - Add: small gear icon in top navigation bar → opens Settings
   - Rename: "History" tab to "Videos"
   - Preserve: Analysis, Review, Videos navigation

6. **ProgressWindow Component** (new)
   - Message template 1 (new project): "Creating new project for [video URL]..."
   - Message template 2 (merge): "Merging results with existing project [run_count runs]..."
   - Auto-dismiss on analysis completion

### 1.3 Quickstart & API Contracts

**Deliverables**: `quickstart.md`, `contracts/` directory

Outputs after Phase 1 completion.

### 1.4 Agent Context Update

**Action**: Run update-agent-context script to add Stitch + UI design work to agent knowledge.

```powershell
.\.specify\scripts\powershell\update-agent-context.ps1 -AgentType copilot
```

---

## Phase 2: Task Generation

**Status**: Pending Phase 1 completion.

After Phase 1 design is complete, run `/speckit.tasks` to generate ordered, dependency-tracked task list for implementation.
