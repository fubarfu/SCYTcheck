# Data Model: Video-Primary Review Flow

**Feature**: 013-video-primary-review  
**Date**: 2026-04-28  
**Scope**: Entities, storage structure, and relationships for video-centric review workflow

---

## Core Entities

### 1. Video Project

Represents one video as the primary unit, containing all analysis runs and merged review state.

**Fields**:
- `project_id` (UUID): Unique project identifier
- `video_url` (string): Original video URL or fallback filename
- `project_location` (path): Filesystem directory containing all artifacts for this video
- `created_date` (ISO8601): When project was first created
- `runs` (array[AnalysisRun]): Ordered list of analysis runs
- `merged_review_state` (ReviewContext): Cached merged state for current review session

**Storage**:
```
{project_location}/
├── metadata.json              # project_id, video_url, created_date
├── result_0.csv               # Run 0 analysis output
├── result_0.review.json       # Run 0 review metadata
├── result_1.csv               # Run 1 analysis output
├── result_1.review.json       # Run 1 review metadata
├── frames_0/                  # Run 0 frame exports
├── frames_1/                  # Run 1 frame exports
└── .scyt_review_workspaces/
    └── {video_id}/            # Per-video review workspace
        ├── review_state.json  # Persisted review decisions (merged)
        └── history.json       # Review session history
```

**Validation**:
- `project_id` must be unique within project location
- `video_url` may be empty; fallback label used in UI
- At least one run must exist for project to be valid

---

### 2. Analysis Run Record

Represents one completed analysis execution for a video.

**Fields**:
- `run_id` (string): Sequential identifier (e.g., "0", "1", "2") based on run order
- `run_timestamp` (ISO8601): When analysis started
- `analysis_duration_ms` (integer): Total analysis time
- `candidate_count` (integer): Number of candidates found in this run
- `output_filepath` (path): Relative path to result CSV (e.g., "result_1.csv")
- `run_order` (integer): Position in sequence (0 = oldest, highest = latest)

**Storage**: Part of `project_id/metadata.json` array

**Validation**:
- `run_id` must be sequential and non-negative
- `run_timestamp` must be valid ISO8601
- `output_filepath` must exist at project location
- Latest run must be accessible for candidate freshness comparison

---

### 3. Candidate Freshness State

Represents whether a candidate is newly discovered in the latest run.

**Fields**:
- `candidate_id` (UUID): Unique candidate identifier
- `spelling` (string): Text of candidate (case-sensitive)
- `discovered_in_run` (string): `run_id` where candidate first found for this video
- `marked_new` (boolean): True if discovered_in_run == latest_run AND spelling not in prior runs
- `is_persisted` (boolean): True if candidate saved to review_state.json

**Storage**: Part of `ReviewContext.candidates` (see below)

**Validation**:
- `spelling` must be non-empty
- `discovered_in_run` must reference valid run in project
- `marked_new` must be computed during review context merge; not user-settable
- Once `marked_new` is set to false (user action), must remain false for session

---

### 4. Review Context

Represents merged candidate/group state produced from all runs for one video.

**Fields**:
- `video_id` (UUID): Project ID (for reference)
- `merged_timestamp` (ISO8601): When context was merged
- `candidates` (array[Candidate]): Combined candidates from all runs with freshness flags
- `groups` (array[CandidateGroup]): Candidate groups (clustered or user-defined)
- `candidate_decisions` (map): `{candidate_id → decision}` where decision ∈ {reviewed, confirmed, rejected, edited}
- `group_decisions` (map): `{group_id → decision}` where decision ∈ {reviewed, confirmed, rejected}

**Merge Algorithm**:

```python
def merge_review_context(runs: List[AnalysisRun], prior_decisions: Dict) -> ReviewContext:
    # 1. Collect all candidates from all runs
    all_candidates = {}  # spelling → list of (run_id, candidate_data)
    latest_run_id = runs[-1].run_id
    
    for run in runs:
        for candidate in run.candidates:
            spelling = candidate.spelling
            if spelling not in all_candidates:
                all_candidates[spelling] = []
            all_candidates[spelling].append((run.run_id, candidate))
    
    # 2. Deduplicate by spelling, compute freshness
    merged_candidates = []
    for spelling, instances in all_candidates.items():
        # Use earliest run where this spelling appeared (most historically relevant)
        first_run_id = min(instances, key=lambda x: x[0])[0]
        
        # Freshness: new if spelling only in latest run
        is_new = len(instances) == 1 and instances[0][0] == latest_run_id
        
        # Prior decision overrides analysis
        decision = prior_decisions.get(spelling, "unreviewed")
        
        merged_candidates.append(Candidate(
            spelling=spelling,
            discovered_in_run=first_run_id,
            marked_new=is_new,
            decision=decision
        ))
    
    return ReviewContext(
        video_id=video_id,
        merged_timestamp=now(),
        candidates=merged_candidates,
        candidate_decisions=prior_decisions
    )
```

**Storage**: Cached in `.scyt_review_workspaces/{video_id}/review_state.json`

**Validation**:
- All candidates must have valid spelling
- Decisions must map to known candidate_ids
- `merged_timestamp` must be recent (within analysis session)

---

### 5. Project Location Setting

Represents the configured filesystem location where video projects are discovered and managed.

**Fields**:
- `project_location_path` (string): Filesystem directory path (absolute or relative)
- `is_default` (boolean): True if using default app-level setting
- `last_validated` (ISO8601): When path was last checked for writability
- `validation_status` (string): "valid", "missing", "unwritable", "unknown"

**Storage**: `%APPDATA%/SCYTcheck/scytcheck_settings.json` (with fallback to local `scytcheck_settings.json`)

```json
{
  "version": "1.0",
  "project_location": "/Users/me/Videos/SCYTcheck",
  "is_default": false,
  "last_validated": "2026-04-28T17:15:00Z",
  "validation_status": "valid"
}
```

**Validation**:
- Path must exist or be creatable
- Path must have write permissions
- Must contain valid project structure (metadata.json + result CSVs)

---

### 6. Default Project Location

Represents the initial app-level project location value applied automatically on first run.

**Value** (per platform):
- **Windows**: `%APPDATA%/SCYTcheck/projects` (e.g., `C:\Users\{user}\AppData\Roaming\SCYTcheck\projects`)
- **macOS**: `~/Library/Application Support/SCYTcheck/projects`
- **Linux**: `~/.local/share/scytcheck/projects`

**Creation**: If default location does not exist on first run:
1. Create directory tree
2. Write initial `scytcheck_settings.json` with default path and `is_default=true`
3. If creation fails, show blocking error in UI with recovery path

**Validation**:
- Must be writable at app startup
- Must be accessible during normal operation

---

### 7. Project Discovery Source

Represents the configured project location as the single authoritative source for which video projects appear in the Videos view.

**Algorithm**:

```python
def discover_projects(project_location: str) -> List[VideoProject]:
    projects = []
    
    for item in os.listdir(project_location):
        item_path = os.path.join(project_location, item)
        
        # Skip non-directories
        if not os.path.isdir(item_path):
            continue
        
        # Check for metadata.json (required marker for valid project)
        metadata_path = os.path.join(item_path, "metadata.json")
        if not os.path.exists(metadata_path):
            continue
        
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            
            project = VideoProject(
                project_id=metadata["project_id"],
                video_url=metadata.get("video_url", item),
                project_location=item_path,
                created_date=metadata["created_date"]
            )
            projects.append(project)
        except (json.JSONDecodeError, KeyError):
            # Invalid metadata; skip project
            continue
    
    return sorted(projects, key=lambda p: p.created_date, reverse=True)  # Newest first
```

**Behavior**:
- No app-level history list maintained
- Projects appear in Videos view based solely on filesystem scan
- Changes to filesystem are reflected on next Videos view load
- If configured location is missing/unwritable, Videos view shows error + recovery path

**Validation**:
- Project location must exist and be readable
- All projects must have valid metadata.json
- No assumptions about stale projects; all discovered are shown

---

## Storage Conventions

### Per-Video Output Structure

```
{project_location}/{video_id_or_hash}/
├── metadata.json
├── result_0.csv
├── result_0.review.json
├── result_1.csv
├── result_1.review.json
├── frames_0/
│   ├── frame_000.png
│   ├── frame_001.png
│   └── ...
└── frames_1/
    ├── frame_000.png
    └── ...
```

### Review State Persistence

```
.scyt_review_workspaces/{video_id}/
├── review_state.json      # Merged candidates + decisions (persisted)
└── history.json           # Optional: review session activity log
```

**review_state.json structure**:
```json
{
  "video_id": "...",
  "merged_timestamp": "2026-04-28T17:15:00Z",
  "candidate_decisions": {
    "candidate_spelling_1": {
      "status": "confirmed",
      "user_note": "..."
    },
    "candidate_spelling_2": {
      "status": "rejected",
      "user_note": "..."
    }
  },
  "group_decisions": {
    "group_id_1": {
      "status": "confirmed"
    }
  }
}
```

### App Settings Persistence

```
%APPDATA%/SCYTcheck/scytcheck_settings.json
OR
./scytcheck_settings.json (fallback)
```

**Schema**:
```json
{
  "version": "1.0",
  "theme": "light",
  "project_location": "C:\\Users\\user\\Videos\\SCYTcheck",
  "is_default": false,
  "last_validated": "2026-04-28T17:15:00Z",
  "validation_status": "valid"
}
```

---

## Relationships

```
VideoProject (1) ──← (many) AnalysisRun
  │
  └──→ ReviewContext (1..1)
       │
       └──→ (many) Candidate
       │
       └──→ (many) CandidateGroup

ReviewContext
  └──→ prior decisions (from review_state.json)
```

---

## API Contracts (Summary)

See `contracts/` directory for detailed endpoint schemas.

**Key Endpoints**:
- `GET /api/projects`: List VideoProject objects from configured location
- `POST /api/analysis/start`: Create/update VideoProject, return project status (create vs. merge)
- `GET /api/analysis/progress`: Return progress message (project create/merge) + analysis %
- `GET /api/review/context`: Return ReviewContext (merged candidates + freshness flags)
- `PUT /api/review/action`: Update candidate decision (confirmed/rejected/edited)
- `GET /api/settings`: Return ProjectLocationSetting
- `PUT /api/settings`: Update ProjectLocationSetting (validate path before save)

---

## Validation & Error Handling

### Critical Validations

1. **Project ID Uniqueness**: On creation, verify no existing project with same ID
2. **Run Ordering**: Ensure run_ids are sequential and in order
3. **Metadata Consistency**: Validate metadata.json matches actual files on disk
4. **Prior Decision Wins**: When merging, ensure `prior_decision > latest_analysis` always
5. **Freshness Accuracy**: Only candidates with unique spelling marked as new

### Error Recovery Paths

| Error | User-Facing Message | Recovery |
|-------|---------------------|----------|
| Project location missing | "Project location not found. Check Settings or choose a new location." | Button to Settings |
| Project location unwritable | "Project location is not writable. Check permissions or choose a new location." | Button to Settings |
| Invalid metadata.json | "Project data is corrupted. Contact support." | Show error code + recovery link |
| Analysis interrupted | "Analysis stopped. Previous run will be retained. Run analysis again to retry." | Auto-retry or manual retry |
| Review merge conflict (edge case) | "(Not user-visible) Prior decision preserved; new analysis added as evidence." | N/A |

---

## Design Rationale

### Why Filesystem-Based Discovery?

- **Simplicity**: No database required; uses existing per-video directory structure
- **Transparency**: Users can manage projects via file explorer
- **Portability**: Projects are portable across machines (just copy directory)
- **No History Maintenance**: Avoids stale/orphaned history records

### Why Spelling-Based Freshness?

- **Accuracy**: Avoids false positives from same misspelling detected multiple times
- **Clarity**: Users understand "new" means "different spelling we haven't seen before"
- **Simplicity**: No fuzzy matching complexity; exact spelling comparison

### Why Prior-Decision-Wins Conflict Resolution?

- **User Trust**: Human judgment is authoritative once exercised
- **Evidence Preservation**: New analysis is still visible (contributes to decision, doesn't override)
- **Stability**: No accidental reset of prior human decisions

---

## Summary

This data model enables video-centric review without introducing new database complexity. Projects are filesystem-based and self-contained. Review state is stored per-video in JSON sidecars. Project discovery is direct filesystem scan with no app-level history maintenance. Candidate freshness is computed via spelling comparison. All decisions preserve prior human judgment.
