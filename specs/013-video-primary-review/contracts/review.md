# API Contract: Review Endpoints

**Feature**: 013-video-primary-review  
**Endpoints**: Review context, candidate actions, group decisions

---

## GET /api/review/context

Retrieve merged review context for a video (all candidates + groups + freshness flags).

**Query Parameters**:
- `video_id` (string, required): Video project ID

**Response (200 OK)**:
```json
{
  "video_id": "uuid-video-id",
  "video_url": "https://www.youtube.com/watch?v=...",
  "project_location": "/path/to/projects/uuid-video-id",
  "run_count": 3,
  "latest_run_id": "2",
  "merged_timestamp": "2026-04-28T17:15:00Z",
  "candidates": [
    {
      "id": "cand-001",
      "spelling": "misspelling1",
      "discovered_in_run": "1",
      "marked_new": true,
      "decision": "unreviewed",
      "frame_count": 12,
      "frame_samples": ["frame_0001.png", "frame_0045.png"]
    },
    {
      "id": "cand-002",
      "spelling": "misspelling2",
      "discovered_in_run": "0",
      "marked_new": false,
      "decision": "confirmed",
      "frame_count": 8,
      "frame_samples": ["frame_0002.png"]
    }
  ],
  "groups": [
    {
      "id": "group-001",
      "name": "Technical Terms",
      "candidate_ids": ["cand-001", "cand-003"],
      "decision": "confirmed"
    }
  ]
}
```

**Response (404 Not Found)**:
```json
{
  "error": "video_not_found",
  "message": "Video with ID ... not found in project location."
}
```

**Behavior**:
1. Load all analysis runs for video_id
2. Merge candidates with freshness flags
3. Load prior decisions from review_state.json
4. Return complete review context
5. Include frame samples for UI display

**Notes**:
- All candidates are merged by spelling (deduplicated)
- `marked_new` is true only if spelling is unique to latest run
- `decision` reflects prior human decisions (or "unreviewed" if none)
- `frame_samples` are up to 3 sample frame paths for UI preview

---

## PUT /api/review/action

Update a candidate decision (confirm, reject, edit, clear new marker).

**Request**:
```json
{
  "video_id": "uuid-video-id",
  "candidate_id": "cand-001",
  "action": "confirmed",  // "confirmed" | "rejected" | "edited" | "clear_new"
  "user_note": "This is the correct spelling"  // optional
}
```

**Response (200 OK)**:
```json
{
  "candidate_id": "cand-001",
  "decision": "confirmed",
  "marked_new": false,  // cleared when action taken
  "timestamp": "2026-04-28T17:20:00Z"
}
```

**Response (400 Bad Request)**:
```json
{
  "error": "invalid_action",
  "message": "Action must be one of: confirmed, rejected, edited, clear_new"
}
```

**Response (404 Not Found)**:
```json
{
  "error": "candidate_not_found",
  "message": "Candidate not found in review context."
}
```

**Behavior**:
1. Validate video_id and candidate_id
2. Validate action type
3. Update candidate decision in review_state.json
4. **Immediately clear `marked_new` flag** (any action clears it)
5. Persist to disk
6. Return updated candidate state

**Notes**:
- Taking any action clears the "new" marker for that candidate
- Decisions persist across sessions
- "edit" action may include user_note for future reference

---

## PUT /api/review/group

Update a candidate group decision.

**Request**:
```json
{
  "video_id": "uuid-video-id",
  "group_id": "group-001",
  "action": "confirmed",  // "confirmed" | "rejected"
  "user_note": "All confirmed as correct"  // optional
}
```

**Response (200 OK)**:
```json
{
  "group_id": "group-001",
  "decision": "confirmed",
  "affected_candidate_ids": ["cand-001", "cand-003"],
  "timestamp": "2026-04-28T17:20:00Z"
}
```

**Behavior**:
1. Update group decision in review_state.json
2. Do NOT auto-update individual candidate decisions (group decision is separate)
3. Persist to disk
4. Return updated group state

---

## DELETE /api/review/decision

Clear a decision (revert to unreviewed).

**Query Parameters**:
- `video_id` (string, required): Video project ID
- `candidate_id` (string, required): Candidate ID

**Response (200 OK)**:
```json
{
  "candidate_id": "cand-001",
  "decision": "unreviewed",
  "marked_new": false  // remains false even after clearing decision
}
```

**Behavior**:
1. Remove candidate decision from review_state.json
2. Reset to "unreviewed" state
3. Do NOT re-enable "marked_new" (once cleared, stays cleared)
4. Persist to disk

---

## GET /api/review/export

Export current review context to CSV or JSON.

**Query Parameters**:
- `video_id` (string, required): Video project ID
- `format` (string, optional): "csv" or "json" (default: "csv")

**Response (200 OK - CSV)**:
```
Content-Type: text/csv
Content-Disposition: attachment; filename="review_uuid-video-id.csv"

spelling,discovered_in_run,marked_new,decision,frame_count
misspelling1,1,false,confirmed,12
misspelling2,0,false,unreviewed,8
...
```

**Response (200 OK - JSON)**:
```json
{
  "video_id": "uuid-video-id",
  "export_timestamp": "2026-04-28T17:25:00Z",
  "candidates": [...]  // same as GET /api/review/context
}
```

**Behavior**:
1. Load review context for video_id
2. Format for export (CSV or JSON)
3. Return with appropriate content type
4. Do NOT modify state

---

## Data Types

### Candidate
```typescript
type Candidate = {
  id: string;
  spelling: string;
  discovered_in_run: string;
  marked_new: boolean;
  decision: "unreviewed" | "confirmed" | "rejected" | "edited";
  frame_count: number;
  frame_samples: string[];  // paths to sample frames
};
```

### CandidateGroup
```typescript
type CandidateGroup = {
  id: string;
  name: string;
  candidate_ids: string[];
  decision: "unreviewed" | "confirmed" | "rejected";
};
```

### ReviewContext
```typescript
type ReviewContext = {
  video_id: string;
  video_url: string;
  project_location: string;
  run_count: number;
  latest_run_id: string;
  merged_timestamp: string;
  candidates: Candidate[];
  groups: CandidateGroup[];
};
```

---

## Error Codes

| Code | HTTP | Meaning |
|------|------|---------|
| `video_not_found` | 404 | Video project does not exist |
| `candidate_not_found` | 404 | Candidate not found in review context |
| `invalid_action` | 400 | Action is not valid |
| `project_location_unavailable` | 422 | Project location is not accessible |

---

## State Transitions

```
Candidate Lifecycle:
  1. Analysis → Candidate created (unreviewed, marked_new=true if unique spelling in latest run)
  2. User Action → Candidate decision set + marked_new cleared
  3. User exports → Candidate state written to CSV/JSON
  4. User clears decision → Marked_new remains false, decision reverts to unreviewed
  5. Next analysis → Marked_new recomputed (true if spelling still unique to latest run)
```
