# API Contract: Analysis Endpoints

**Feature**: 013-video-primary-review  
**Endpoints**: Analysis management (start, progress, status)

---

## POST /api/analysis/start

Start a new analysis for a video.

**Request**:
```json
{
  "video_url": "https://www.youtube.com/watch?v=...",
  "project_location": "/path/to/projects"  // optional; uses configured default if omitted
}
```

**Response (200 OK)**:
```json
{
  "analysis_id": "uuid-string",
  "video_id": "uuid-string",
  "project_status": "creating",  // "creating" | "merging"
  "run_id": "1",
  "run_timestamp": "2026-04-28T17:15:00Z",
  "project_location": "/path/to/projects/video_id",
  "message": "Creating new project for https://www.youtube.com/watch?v=..."
}
```

**Response (400 Bad Request)**:
```json
{
  "error": "invalid_video_url",
  "message": "Video URL is required and must be valid."
}
```

**Response (422 Unprocessable Entity)**:
```json
{
  "error": "project_location_unavailable",
  "message": "Project location /path/to/projects is not writable. Please check Settings.",
  "recovery_action": "navigate_to_settings"
}
```

**Behavior**:
1. Validate video URL
2. Validate project location (use configured default if not provided)
3. Determine if this is a new project or merge:
   - Check if `{project_location}/{video_id_hash}` exists
   - `project_status = "creating"` if new
   - `project_status = "merging"` if exists
4. Return status and message for progress window
5. Start analysis in background (async)

**Notes**:
- Analysis runs asynchronously; caller must poll `/api/analysis/progress` for updates
- `video_id` is derived from URL hash; same URL always maps to same video_id

---

## GET /api/analysis/progress

Retrieve current analysis progress and project status.

**Query Parameters**:
- `analysis_id` (string, required): UUID from `/api/analysis/start` response

**Response (200 OK)**:
```json
{
  "status": "in_progress",  // "in_progress" | "completed" | "failed"
  "progress_percent": 45,
  "project_status": "merging",  // "creating" | "merging"
  "message": "Merging results with existing project (5 previous runs)...",
  "frame_count": 1200,
  "frames_processed": 540,
  "candidates_found": 28,
  "elapsed_ms": 12345,
  "estimated_remaining_ms": 8000
}
```

**Response (200 OK - Completed)**:
```json
{
  "status": "completed",
  "progress_percent": 100,
  "project_status": "merging",
  "message": "Analysis complete. Opening review...",
  "frame_count": 2100,
  "frames_processed": 2100,
  "candidates_found": 45,
  "elapsed_ms": 32500,
  "review_ready": true,
  "video_id": "uuid-string"
}
```

**Response (200 OK - Failed)**:
```json
{
  "status": "failed",
  "error": "ocr_service_error",
  "message": "OCR service encountered an error. Please try analysis again.",
  "frame_count": 1200,
  "frames_processed": 540,
  "elapsed_ms": 12345
}
```

**Response (404 Not Found)**:
```json
{
  "error": "analysis_not_found",
  "message": "Analysis with ID ... not found. Analysis may have expired."
}
```

**Behavior**:
1. Lookup analysis session by `analysis_id`
2. Return current progress state
3. On completion, set `review_ready: true`
4. On failure, include error details

**Notes**:
- Frontend polls this endpoint every 1-2 seconds during analysis
- `progress_percent` is used for progress bar
- `message` is displayed in progress window (user-visible)
- Project status is stable (does not change during analysis)
- Frontend auto-navigates to review when `review_ready: true`

---

## GET /api/analysis/status

Get overall analysis system status.

**Response (200 OK)**:
```json
{
  "system_ready": true,
  "active_analysis_count": 2,
  "last_analysis_completion": "2026-04-28T16:45:00Z"
}
```

**Response (503 Service Unavailable)**:
```json
{
  "system_ready": false,
  "message": "OCR service is starting up. Please wait...",
  "retry_after_seconds": 10
}
```

**Behavior**:
1. Check if analysis services are ready
2. Return system health status
3. Allow frontend to show maintenance messages if needed

---

## Data Types

### AnalysisProgress
```typescript
type AnalysisProgress = {
  status: "in_progress" | "completed" | "failed";
  progress_percent: number;  // 0-100
  project_status: "creating" | "merging";
  message: string;
  frame_count: number;
  frames_processed: number;
  candidates_found: number;
  elapsed_ms: number;
  estimated_remaining_ms?: number;
  review_ready?: boolean;
  video_id?: string;
  error?: string;
};
```

---

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `invalid_video_url` | 400 | Video URL is missing or malformed |
| `project_location_unavailable` | 422 | Project location does not exist or is not writable |
| `analysis_not_found` | 404 | Analysis ID does not exist or has expired |
| `ocr_service_error` | 500 | OCR service encountered an error |
| `video_download_error` | 500 | Video could not be downloaded |
| `analysis_interrupted` | 500 | Analysis was interrupted (user action or system failure) |

---

## Validation Rules

### Video URL
- Must be HTTPS or HTTP
- Must resolve to valid video
- Must not be empty

### Project Location
- Must exist and be readable
- Must have write permissions
- Must contain valid project structure or be empty (for new projects)

---

## State Machine

```
START
  ↓
POST /api/analysis/start (validate → returns project_status)
  ↓
[Background: analysis running]
  ↓
GET /api/analysis/progress (polling) → status in {in_progress}
  ↓
GET /api/analysis/progress → status in {completed, failed}
  ↓
Frontend: if completed, navigate to /api/review/context
           if failed, show error message + retry button
```
