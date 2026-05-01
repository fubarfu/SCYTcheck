# Quickstart: Video-Primary Review Flow

**Feature**: 013-video-primary-review  
**Date**: 2026-04-28  
**Target**: Implementation team preparing to begin Phase 2 (tasks)

---

## Feature Overview

Transform the review workflow from **result-file centric** to **video centric**. Users:

1. Open Analysis view → enter video URL (no output filename input)
2. Click "Start Analysis" → progress window shows "Creating new project..." or "Merging with existing project (5 runs)..."
3. Analysis completes → Review view opens automatically
4. Review shows combined candidates from all runs for that video, with new candidates marked (based on unique spelling)
5. Videos view lists all projects from configured location (no app history)
6. Settings view allows project location configuration

---

## Key Changes Summary

### UI Changes

| View | Current | New |
|------|---------|-----|
| **Analysis** | Output filename input | Progress window only; no filename input |
| **Review** | Manual result load + filename shown | Auto-opens; video URL shown; combined data |
| **History** | Session history strip | Renamed to Videos; filesystem project list |
| **Settings** | N/A | New view for project location config |
| **Main Nav** | "History" tab | "Videos" tab + gear icon (Settings) |

### Data Model Changes

| Entity | Change | Impact |
|--------|--------|--------|
| **VideoProject** | Becomes primary unit | Scopes all data to one video |
| **AnalysisRun** | Ordered within project | Track which run is latest for freshness |
| **ReviewContext** | Merged from all runs | Combines all candidates + prior decisions |
| **ProjectLocation** | Global setting | Moved from per-run config to app-level |
| **CandidateFreshness** | Spelling-based | New marker only if spelling unique to latest run |

### API Endpoints (New)

- `POST /api/analysis/start` → returns project_status (creating|merging)
- `GET /api/analysis/progress` → streams project_status + progress %
- `GET /api/projects` → list all projects in configured location
- `PUT /api/settings` → update project location

---

## Implementation Sequence (High-Level)

### Phase 2A: Backend Preparation (Parallel Path 1)

1. **config.py**: Add app-level project location setting (default path)
2. **history_service.py**: Modify to scan filesystem for projects (no app history)
3. **models.py**: Add VideoProject, AnalysisRun, ReviewContext, CandidateFreshness entities
4. **analysis_service.py**: Detect create vs. merge; populate project_status in progress
5. **review_service.py**: Implement merge algorithm (candidate dedup + prior-decision-wins)
6. **api/analysis.py**: Create endpoints (POST start, GET progress)
7. **api/projects.py**: Create endpoints (GET list, PUT settings)

### Phase 2B: Frontend Design & Components (Parallel Path 2)

1. **Stitch**: Design UI screens in Google Stitch project
   - Analysis view (remove output filename input, add progress window)
   - Review view (show video URL, combined candidates, new markers)
   - Videos view (rename from History, show project list)
   - Settings view (project location config, validation feedback)
   - Gear icon in main nav

2. **React Components** (implement from Stitch designs):
   - `ProgressWindow.tsx` (new) → displays create/merge messaging
   - `CandidateList.tsx` (modify) → add visual "new" marker
   - `VideosPage.tsx` (rename from History) → project discovery + list
   - `SettingsPage.tsx` (new) → project location config
   - `MainLayout.tsx` (modify) → add gear icon, rename tab

3. **Services**:
   - `api.ts` → add new REST client methods (analysis start, projects list, settings)

### Phase 2C: Integration & Testing

1. **Contract Tests**: Validate API contracts (analysis.md, review.md, projects.md)
2. **Integration Tests**: End-to-end flows (analysis → auto-open review, project discovery, settings)
3. **Unit Tests**: Candidate freshness algorithm, conflict resolution, project discovery
4. **Manual Testing**: Full workflow on dev machine

---

## Critical Implementation Details

### 1. Candidate Freshness Algorithm

```python
def mark_new_candidates(all_runs, latest_run_id):
    """
    Mark candidates as 'new' if:
    - Spelling appears ONLY in latest run
    - No prior run has this spelling
    """
    latest_run = all_runs[-1]
    prior_spellings = set()
    
    for run in all_runs[:-1]:  # All except latest
        for candidate in run.candidates:
            prior_spellings.add(candidate.spelling)
    
    for candidate in latest_run.candidates:
        if candidate.spelling not in prior_spellings:
            candidate.marked_new = True
        else:
            candidate.marked_new = False
    
    return latest_run.candidates
```

### 2. Review Context Merge (Prior Decision Wins)

```python
def merge_review_context(all_runs, prior_decisions):
    """
    Merge all candidates by spelling.
    Prior human decision ALWAYS wins over new analysis.
    """
    merged = {}  # spelling → Candidate
    
    for run in all_runs:
        for candidate in run.candidates:
            spelling = candidate.spelling
            if spelling not in merged:
                merged[spelling] = Candidate(
                    spelling=spelling,
                    discovered_in_run=run.run_id,
                    decision=prior_decisions.get(spelling, "unreviewed")
                )
    
    # Mark new candidates
    for candidate in merged.values():
        # New if only in latest run
        candidate.marked_new = (candidate.discovered_in_run == latest_run_id)
    
    return list(merged.values())
```

### 3. Project Discovery (Filesystem Scan)

```python
def discover_projects(project_location):
    """
    Scan project location for valid projects.
    A project is valid if it contains metadata.json.
    """
    projects = []
    
    for item in os.listdir(project_location):
        path = os.path.join(project_location, item)
        if not os.path.isdir(path):
            continue
        
        metadata_path = os.path.join(path, "metadata.json")
        if not os.path.exists(metadata_path):
            continue
        
        try:
            with open(metadata_path) as f:
                metadata = json.load(f)
            projects.append(VideoProject.from_metadata(metadata, path))
        except:
            continue  # Skip invalid projects
    
    return sorted(projects, key=lambda p: p.created_date, reverse=True)
```

### 4. Progress Window Messaging

**Message Templates**:
- **New Project**: `"Creating new project for {video_url}..."`
- **Merge**: `"Merging results with existing project ({run_count} previous runs)..."`

**When to Show**:
- Immediately after `/api/analysis/start` returns
- Poll `/api/analysis/progress` every 1-2 seconds
- Display `message` field from response
- Auto-dismiss when `status: completed`

### 5. Auto-Open Review After Analysis

**Frontend Flow**:
```
1. POST /api/analysis/start → get analysis_id
2. [Progress window visible, polling progress]
3. GET /api/analysis/progress (poll every 1s)
4. When status === "completed":
   - Close progress window
   - Navigate to `/review?video_id={video_id}`
5. GET /api/review/context → load merged candidates
6. Render ReviewPage with candidates + new markers
```

**Backend Flow**:
```
1. Analysis runs in background (async)
2. Write results to project location
3. Set status → "completed"
4. Mark review_ready = true
5. Frontend detects and navigates automatically
```

---

## Testing Checklist (Phase 2C)

### Backend Tests

- [ ] `test_candidate_freshness.py`: Spelling comparison (only new if unique to latest)
- [ ] `test_review_context_merge.py`: Prior decision wins; merge deduplicates by spelling
- [ ] `test_project_discovery.py`: Filesystem scan finds valid projects; skips invalid
- [ ] `test_default_project_location.py`: Default path created on first run
- [ ] `test_analysis_progress_messaging.py`: Create vs. merge status correctly determined

### Frontend Tests

- [ ] `test_progress_window.tsx`: Shows correct message template (create vs. merge)
- [ ] `test_auto_open_review.tsx`: Review opens automatically after analysis completes
- [ ] `test_candidate_new_marker.tsx`: Only marked candidates show "new" badge
- [ ] `test_videos_discovery.tsx`: Project list populated from filesystem scan
- [ ] `test_settings_validation.tsx`: Project location validation + error recovery

### Integration Tests

- [ ] E2E: Analysis → Progress → Auto-open Review → View candidates with new markers
- [ ] E2E: Change project location → Videos list updates
- [ ] E2E: First run → Default location created + Settings accessible
- [ ] E2E: Missing project location → Error shown + Recovery path works

---

## Stitch Design Tasks

**Actions for UI Design Phase**:

1. **Analysis View (Modify)**:
   - Remove: Output filename input field
   - Keep: Video URL input
   - Add: ProgressWindow component (centered, shows message)
   - Add: Messaging "Review will open automatically after analysis completes"
   - Design: Progress bar + animated spinner

2. **Review View (Modify)**:
   - Remove: Manual "Load Result File" action
   - Modify: Source context shows "Video: {url}" (read-only)
   - Add: Candidate list with "new" badge indicator
   - Design: Visual distinction for new candidates (highlight, badge, icon)
   - Add: Group visualization if applicable

3. **Videos View (New, Rename from History)**:
   - Remove: Session history strip
   - Add: Project list (cards or table)
   - Per project: Video URL, run count, last analyzed date
   - Action: Click project → open review
   - Empty state: "No projects yet. Start Analysis to create one."

4. **Settings View (New)**:
   - Input: Project location path
   - Validation: "Path is valid and writable" / error message
   - Action: "Browse..." button to file picker
   - Action: "Reset to Default" button
   - Display: Current default path for reference

5. **Main Navigation (Modify)**:
   - Add: Gear icon in top-right corner
   - Action: Gear → navigate to Settings view
   - Rename: "History" tab to "Videos"
   - Preserve: Analysis, Review, Videos tabs

**Output**: Finalized Stitch screens exported to `specs/013-video-primary-review/stitch/` for implementation reference.

---

## Known Constraints & Gotchas

### 1. Video URL Fallback
If metadata doesn't contain video URL, use fallback label (e.g., filename). This is acceptable per spec.

### 2. Run Ordering
Assume run_id is deterministic (timestamp-based). If not, use file mtime for ordering.

### 3. Prior Decision Persistence
Once a human makes a decision, it must persist even if analysis changes. This is enforced in merge algorithm.

### 4. Freshness Flag Clearing
Once user takes ANY action on a candidate (confirm/reject/edit), marked_new is cleared permanently (not re-enabled on next analysis).

### 5. Project Location Validation
Check writability, not just existence. App must create directories as needed.

---

## Success Criteria (From Spec)

✅ **SC-001**: In 95%+ of validation attempts, users can enter review without manual file load  
✅ **SC-002**: In 99%+ of validation comparisons, review data matches combined outputs (no cross-video bleed)  
✅ **SC-003**: In 95%+ of user tests, participants correctly identify new candidates on first pass  
✅ **SC-004**: In 90%+ of usability checks, users find project location settings via gear icon  
✅ **SC-005**: In 95%+ of usability checks, users open existing project within 30 seconds  
✅ **SC-006**: In 95%+ of user tests, participants understand project status from progress message  
✅ **SC-007**: In 95%+ of validation runs, review auto-opens within 2 seconds of analysis completion  

---

## Next Steps

1. **Complete Phase 1 Design** → finalize data-model.md, contracts, quickstart (this document)
2. **Update Agent Context** → run `update-agent-context.ps1` to add Stitch + design work
3. **Generate Phase 2 Tasks** → run `/speckit.tasks` to create ordered task list
4. **Assign & Begin Implementation** → start with Phase 2A (backend) + Phase 2B (frontend UI design) in parallel
5. **Integration & Testing** → Phase 2C after both paths have functioning components

---

**Ready to proceed with Phase 2 task generation.**
