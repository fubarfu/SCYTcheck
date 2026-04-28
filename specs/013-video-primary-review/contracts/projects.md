# API Contract: Projects & Settings Endpoints

**Feature**: 013-video-primary-review  
**Endpoints**: Project discovery, project management, settings

---

## GET /api/projects

List all video projects in configured project location.

**Query Parameters**: None

**Response (200 OK)**:
```json
{
  "project_location": "/path/to/projects",
  "location_status": "valid",  // "valid" | "missing" | "unwritable"
  "projects": [
    {
      "project_id": "uuid-1",
      "video_url": "https://www.youtube.com/watch?v=abc123",
      "project_location": "/path/to/projects/uuid-1",
      "created_date": "2026-04-27T10:00:00Z",
      "run_count": 3,
      "last_analyzed": "2026-04-28T15:30:00Z",
      "candidate_count_total": 45,
      "candidate_count_reviewed": 38
    },
    {
      "project_id": "uuid-2",
      "video_url": "https://www.youtube.com/watch?v=def456",
      "project_location": "/path/to/projects/uuid-2",
      "created_date": "2026-04-26T14:15:00Z",
      "run_count": 1,
      "last_analyzed": "2026-04-26T14:45:00Z",
      "candidate_count_total": 12,
      "candidate_count_reviewed": 8
    }
  ]
}
```

**Response (422 Unprocessable Entity - Location Missing)**:
```json
{
  "error": "project_location_missing",
  "message": "Configured project location /path/to/projects does not exist.",
  "location_status": "missing",
  "recovery_action": "navigate_to_settings",
  "recovery_message": "Go to Settings to choose a valid project location."
}
```

**Response (422 Unprocessable Entity - Location Unwritable)**:
```json
{
  "error": "project_location_unwritable",
  "message": "Configured project location /path/to/projects is not writable.",
  "location_status": "unwritable",
  "recovery_action": "navigate_to_settings",
  "recovery_message": "Check permissions or choose a new location in Settings."
}
```

**Behavior**:
1. Validate configured project location
2. If location is invalid, return error with recovery action
3. Scan directory for valid projects (containing metadata.json)
4. Sort by creation date (newest first)
5. For each project, compute metadata (run_count, candidate_count, etc.)
6. Return project list

**Notes**:
- If configured location doesn't exist, frontend shows error + "Fix" button
- If location is unwritable, frontend shows warning + "Check Settings" button
- Empty location returns empty projects array (not an error)

---

## GET /api/projects/:project_id

Get details for a specific project.

**URL Parameters**:
- `project_id` (string, required): UUID of project

**Response (200 OK)**:
```json
{
  "project_id": "uuid-1",
  "video_url": "https://www.youtube.com/watch?v=abc123",
  "project_location": "/path/to/projects/uuid-1",
  "created_date": "2026-04-27T10:00:00Z",
  "run_count": 3,
  "runs": [
    {
      "run_id": "0",
      "run_timestamp": "2026-04-27T10:00:00Z",
      "candidate_count": 20,
      "frame_count": 1200
    },
    {
      "run_id": "1",
      "run_timestamp": "2026-04-27T14:30:00Z",
      "candidate_count": 25,
      "frame_count": 1500
    },
    {
      "run_id": "2",
      "run_timestamp": "2026-04-28T15:30:00Z",
      "candidate_count": 30,
      "frame_count": 2100
    }
  ],
  "metadata": {
    "total_candidates_merged": 45,
    "candidates_reviewed": 38,
    "candidates_new": 7,
    "total_frame_count": 4800
  }
}
```

**Response (404 Not Found)**:
```json
{
  "error": "project_not_found",
  "message": "Project with ID ... not found."
}
```

**Behavior**:
1. Load project metadata and all runs
2. Compute merged candidate statistics
3. Return detailed project information

---

## DELETE /api/projects/:project_id

Delete a project (remove all files).

**URL Parameters**:
- `project_id` (string, required): UUID of project

**Query Parameters**:
- `confirm` (boolean, optional): Must be true to actually delete

**Response (200 OK)**:
```json
{
  "deleted": true,
  "project_id": "uuid-1",
  "deleted_at": "2026-04-28T17:30:00Z"
}
```

**Response (400 Bad Request - Requires Confirmation)**:
```json
{
  "error": "deletion_requires_confirmation",
  "message": "Pass ?confirm=true to confirm deletion."
}
```

**Response (404 Not Found)**:
```json
{
  "error": "project_not_found",
  "message": "Project not found."
}
```

**Behavior**:
1. Require explicit confirmation (safety check)
2. Remove project directory and all contents
3. Return deletion confirmation
4. Frontend should refresh projects list after deletion

**Notes**:
- This is destructive; no undo
- Should be guarded by UI confirmation dialog
- Consider adding soft-delete or archive option in future

---

## GET /api/settings

Get current app settings.

**Response (200 OK)**:
```json
{
  "project_location": "/path/to/projects",
  "is_default": false,
  "location_status": "valid",  // "valid" | "missing" | "unwritable" | "unknown"
  "last_validated": "2026-04-28T17:15:00Z",
  "theme": "light",
  "ui_language": "en"
}
```

**Behavior**:
1. Load scytcheck_settings.json (or fallback to local)
2. Validate project location path
3. Return current settings

---

## PUT /api/settings

Update app settings (primarily project location).

**Request**:
```json
{
  "project_location": "/new/path/to/projects"
}
```

**Response (200 OK)**:
```json
{
  "project_location": "/new/path/to/projects",
  "is_default": false,
  "location_status": "valid",
  "last_validated": "2026-04-28T17:25:00Z"
}
```

**Response (422 Unprocessable Entity - Invalid Path)**:
```json
{
  "error": "invalid_project_location",
  "message": "Path /new/path does not exist or is not writable.",
  "suggested_path": "/path/to/valid/location"
}
```

**Response (422 Unprocessable Entity - Empty Path)**:
```json
{
  "error": "project_location_required",
  "message": "Project location cannot be empty."
}
```

**Behavior**:
1. Validate new project_location:
   - Must not be empty
   - Must exist or be creatable
   - Must have write permissions
2. If validation passes:
   - Update scytcheck_settings.json (create if needed)
   - Set is_default = false (user customized)
   - Return updated settings
3. If validation fails:
   - Return error with suggestion
   - Do NOT update settings

**Notes**:
- Path can be absolute or relative
- On Windows, support both forward slashes (/) and backslashes (\)
- Auto-create directory if it doesn't exist (if parent is writable)

---

## POST /api/settings/validate

Validate a project location path without saving.

**Request**:
```json
{
  "project_location": "/path/to/test"
}
```

**Response (200 OK - Valid)**:
```json
{
  "valid": true,
  "message": "Path is valid and writable.",
  "location_status": "valid",
  "project_count_at_location": 3
}
```

**Response (200 OK - Invalid)**:
```json
{
  "valid": false,
  "message": "Path does not exist.",
  "location_status": "missing",
  "can_create": true,  // true if parent directory is writable
  "recovery_suggestion": "Create the directory manually or choose another location."
}
```

**Behavior**:
1. Check path existence
2. Check write permissions
3. If valid, count existing projects at location
4. Return validation result

**Notes**:
- Does not save anything
- Useful for UI real-time validation
- Can help user choose a good location before saving

---

## GET /api/settings/default

Get default project location for this platform.

**Response (200 OK)**:
```json
{
  "default_project_location": "/home/user/.local/share/scytcheck/projects",
  "platform": "linux",
  "created_at_first_run": true  // true if app auto-created on first run
}
```

**Behavior**:
1. Return platform-specific default path
2. Indicate if it was created on first run

**Notes**:
- Windows: `%APPDATA%/SCYTcheck/projects`
- macOS: `~/Library/Application Support/SCYTcheck/projects`
- Linux: `~/.local/share/scytcheck/projects`

---

## Data Types

### VideoProject (Summary)
```typescript
type VideoProject = {
  project_id: string;
  video_url: string;
  project_location: string;
  created_date: string;  // ISO8601
  run_count: number;
  last_analyzed: string;  // ISO8601
  candidate_count_total: number;
  candidate_count_reviewed: number;
};
```

### VideoProject (Detail)
```typescript
type VideoProjectDetail = VideoProject & {
  runs: AnalysisRun[];
  metadata: {
    total_candidates_merged: number;
    candidates_reviewed: number;
    candidates_new: number;
    total_frame_count: number;
  };
};
```

### AppSettings
```typescript
type AppSettings = {
  project_location: string;
  is_default: boolean;
  location_status: "valid" | "missing" | "unwritable" | "unknown";
  last_validated: string;  // ISO8601
  theme: "light" | "dark";
  ui_language: string;
};
```

---

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `project_location_missing` | 422 | Project location does not exist |
| `project_location_unwritable` | 422 | Project location is not writable |
| `invalid_project_location` | 422 | Project location path is invalid |
| `project_location_required` | 422 | Project location is required |
| `project_not_found` | 404 | Project ID does not exist |
| `deletion_requires_confirmation` | 400 | Deletion requires ?confirm=true |

---

## Workflow Examples

### First Run
```
1. User opens app
2. Backend checks if scytcheck_settings.json exists
3. If not, creates default location + settings file
4. Frontend loads GET /api/projects → returns empty list + message "No projects yet"
5. User clicks "Start Analysis" → analysis proceeds with default location
```

### Change Project Location
```
1. User opens Settings view
2. User enters new path + clicks "Save"
3. Frontend calls PUT /api/settings with new path
4. Backend validates path (checks existence, permissions)
5. If valid, saves to scytcheck_settings.json, returns success
6. Frontend auto-refreshes Videos list (calls GET /api/projects)
7. Videos list now shows projects from new location
```

### Recover from Missing Location
```
1. GET /api/projects returns error: project_location_missing
2. Frontend displays error message + "Fix in Settings" button
3. User clicks button → navigates to Settings
4. Backend shows recovery suggestions (validate alternative paths)
5. User selects valid path + saves
6. GET /api/projects now succeeds with projects from new location
```
