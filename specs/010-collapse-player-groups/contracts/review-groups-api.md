# API Contract: Review Groups Management

**Feature**: 010-collapse-player-groups | **Contract Type**: HTTP REST API | **Version**: 1.0 | **Date**: 2026-04-25

## Overview

Backend HTTP API endpoints for managing candidate groups, validating uniqueness, and persisting consensus state. These endpoints are called by the React frontend components (`CollapsibleGroup.tsx`, `CandidateRadioButton.tsx`, `ValidationFeedback.tsx`).

**Base URL**: `http://localhost:5000/api/v1` (continuation of 007 architecture)  
**Content-Type**: `application/json`  
**Authentication**: None (local app)  
**Error Handling**: HTTP status codes + JSON error responses

---

## Endpoints

### 1. GET /review-sessions/{session_id}

Retrieve a review session with all candidate groups.

**Path Parameters**:
- `session_id` (string, UUID): Review session identifier

**Query Parameters**: None

**Response** (200 OK):
```json
{
  "session_id": "uuid-12345",
  "video_path": "C:/videos/game_footage.mp4",
  "analysis_completed_at": "2026-04-25T10:30:00Z",
  "review_started_at": "2026-04-25T10:35:00Z",
  "groups": {
    "group_1": {
      "group_id": "group_1",
      "field_name": "player_name",
      "frame_indices": [10, 45, 120],
      "consensus_spelling": null,
      "is_collapsed": false,
      "candidates": [
        {
          "id": "cand_1",
          "spelling": "John Smith",
          "confidence": 0.95,
          "source_frame_indices": [10, 120]
        },
        {
          "id": "cand_2",
          "spelling": "Jon Smith",
          "confidence": 0.72,
          "source_frame_indices": [45]
        }
      ],
      "rejected_candidate_ids": [],
      "last_modified_at": "2026-04-25T10:35:15Z"
    }
  }
}
```

**Response** (404 Not Found):
```json
{
  "error": "Session not found",
  "session_id": "uuid-12345"
}
```

**Contract Behavior**:
- If session exists in sidecar JSON, hydrate full session state
- If session doesn't exist, return 404 (frontend should handle gracefully)

---

### 2. POST /review-sessions/{session_id}/groups/{group_id}/candidates/{candidate_id}/select

Select a candidate as the consensus spelling. Validates uniqueness and persists state.

**Path Parameters**:
- `session_id` (string, UUID): Review session identifier
- `group_id` (string): Candidate group identifier
- `candidate_id` (string, UUID): Candidate to select

**Request Body**: None (candidate identified by path)

**Response** (200 OK):
```json
{
  "success": true,
  "group_id": "group_1",
  "consensus_spelling": "John Smith",
  "is_consensus_reached": true,
  "is_collapsed": true,
  "validation": {
    "is_valid": true,
    "error_message": null
  }
}
```

**Response** (422 Unprocessable Entity - Validation Failed):
```json
{
  "success": false,
  "group_id": "group_1",
  "validation": {
    "is_valid": false,
    "candidate_name": "Michael Jordan",
    "error_message": "Name already used in Group 3 - Michael Jordan",
    "conflict_group_id": "group_3",
    "conflict_spelling": "Michael Jordan",
    "hint": "Choose a different spelling from the group"
  }
}
```

**Contract Behavior**:
- Retrieve candidate from group
- Call `review_groups_service.validate_candidate_uniqueness(candidate_spelling, excluded_group_id=group_id)`
- If validation fails, return 422 with validation result (state NOT persisted)
- If validation passes:
  - Update `group.consensus_spelling` to candidate spelling
  - Check `is_consensus_reached()` property
  - If consensus reached, set `is_collapsed = True`
  - Persist session to sidecar JSON
  - Return 200 with updated group state

**Error Codes**:
- `404 Not Found`: Session or group not found
- `422 Unprocessable Entity`: Validation failed (duplicate name)

---

### 3. POST /review-sessions/{session_id}/groups/{group_id}/candidates/{candidate_id}/reject

Mark a candidate as rejected (non-destructive). Updates visual feedback but preserves candidate data.

**Path Parameters**:
- `session_id` (string, UUID): Review session identifier
- `group_id` (string): Candidate group identifier
- `candidate_id` (string, UUID): Candidate to reject

**Request Body**: None

**Response** (200 OK):
```json
{
  "success": true,
  "group_id": "group_1",
  "rejected_candidate_ids": ["cand_2"],
  "active_spellings": ["John Smith"]
}
```

**Response** (404 Not Found):
```json
{
  "error": "Session, group, or candidate not found"
}
```

**Contract Behavior**:
- Add `candidate_id` to `group.rejected_candidate_ids` list
- Do NOT delete candidate from `group.candidates` (preserved for audit)
- Persist session to sidecar JSON
- Return 200 with updated list of rejected IDs

---

### 4. POST /review-sessions/{session_id}/groups/{group_id}/toggle-collapse

Toggle group expanded/collapsed state manually.

**Path Parameters**:
- `session_id` (string, UUID): Review session identifier
- `group_id` (string): Candidate group identifier

**Query Parameters**:
- `collapsed` (boolean): Desired state (true = collapse, false = expand)

**Request Body**: None

**Response** (200 OK):
```json
{
  "success": true,
  "group_id": "group_1",
  "is_collapsed": false
}
```

**Contract Behavior**:
- If consensus is reached AND user tries to set `collapsed=true`, allow (explicit confirmation)
- If consensus is NOT reached AND user tries to set `collapsed=true`, allow but log warning (group has conflicts)
- Update `group.is_collapsed` to requested value
- Persist session to sidecar JSON
- Return 200 with new state

**Constraint**: Cannot manually collapse a group that has NOT reached consensus (spec requirement to keep conflicts visible).

---

### 5. GET /review-groups/validate

Validate a candidate spelling for uniqueness across all groups.

**Query Parameters**:
- `candidate_spelling` (string, required): Name to validate
- `excluded_group_id` (string, optional): Group ID to exclude from check (for candidate selection)
- `session_id` (string, required): Review session context

**Response** (200 OK):
```json
{
  "is_valid": true,
  "candidate_name": "John Smith",
  "error_message": null,
  "conflict_group_id": null,
  "conflict_spelling": null,
  "hint": null
}
```

**Response** (200 OK - Validation Failed):
```json
{
  "is_valid": false,
  "candidate_name": "Michael Jordan",
  "error_message": "Name already used in Group 3 - Michael Jordan",
  "conflict_group_id": "group_3",
  "conflict_spelling": "Michael Jordan",
  "hint": "Choose a different spelling from the group"
}
```

**Contract Behavior**:
- Load review session from sidecar JSON
- Iterate all groups (excluding `excluded_group_id` if provided)
- Check if `candidate_spelling` matches any `group.consensus_spelling`
- If match found, return validation failure with conflict details
- If no match found, return validation success
- Frontend uses this for real-time feedback as user types or hovers over candidates

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "error": "Human-readable error message",
  "status": 400,
  "details": {
    "field": "session_id",
    "reason": "UUID format invalid"
  }
}
```

**Standard HTTP Status Codes**:
- `200 OK`: Request succeeded
- `400 Bad Request`: Malformed request (invalid JSON, missing required fields)
- `404 Not Found`: Resource not found (session, group, candidate)
- `422 Unprocessable Entity`: Validation failed (duplicate name, business logic violation)
- `500 Internal Server Error`: Unexpected server error

---

## Backend Implementation Notes

### Service Layer

```python
# File: src/web/api/review_groups_service.py

class ReviewGroupsService:
    def get_session(self, session_id: str) -> ReviewSession:
        """Load review session from sidecar JSON"""
        
    def select_candidate(self, session_id: str, group_id: str, candidate_id: str) -> SelectCandidateResult:
        """Validate and select candidate; auto-collapse if consensus reached"""
        
    def validate_candidate_uniqueness(self, candidate_name: str, session_id: str, excluded_group_id: str = None) -> ValidationResult:
        """Check if name conflicts with existing consensus spellings"""
        
    def reject_candidate(self, session_id: str, group_id: str, candidate_id: str) -> RejectCandidateResult:
        """Mark candidate as rejected (non-destructive)"""
        
    def toggle_collapse(self, session_id: str, group_id: str, collapsed: bool) -> ToggleCollapseResult:
        """Manually toggle group collapse state"""
```

### Route Layer

```python
# File: src/web/api/routes/review_groups_routes.py

@app.get("/api/v1/review-sessions/{session_id}")
def get_session(session_id: str) -> ReviewSessionResponse:
    """Retrieve session state"""
    
@app.post("/api/v1/review-sessions/{session_id}/groups/{group_id}/candidates/{candidate_id}/select")
def select_candidate(session_id: str, group_id: str, candidate_id: str) -> SelectCandidateResponse:
    """Select candidate with validation"""
    
@app.get("/api/v1/review-groups/validate")
def validate_candidate(candidate_spelling: str, session_id: str, excluded_group_id: str = None) -> ValidationResponse:
    """Validate spelling uniqueness"""
```

### Persistence

```python
# File: src/services/review_session_persistence.py (ENHANCED)

def save_review_session(session: ReviewSession, result_path: str) -> None:
    """Save session to <result>.review.json"""
    
def load_review_session(result_path: str) -> ReviewSession:
    """Load session from <result>.review.json"""
```

---

## Frontend Integration Points

**Component**: `CollapsibleGroup.tsx`
```typescript
// Calls endpoint: POST /api/v1/review-sessions/{session_id}/groups/{group_id}/toggle-collapse
const onCollapse = (collapsed: boolean) => {
  const result = await api.toggleCollapse(sessionId, groupId, collapsed);
  // Update local state with result
};
```

**Component**: `CandidateRadioButton.tsx`
```typescript
// Calls endpoint: POST /api/v1/review-sessions/{session_id}/groups/{group_id}/candidates/{candidate_id}/select
const onSelect = async (candidateId: string) => {
  const result = await api.selectCandidate(sessionId, groupId, candidateId);
  if (!result.validation.is_valid) {
    // Display inline validation error via ValidationFeedback component
    setValidationError(result.validation);
  } else {
    // Update group state; check if collapsed
    updateGroupState(result);
  }
};
```

**Component**: `ValidationFeedback.tsx`
```typescript
// Calls endpoint: GET /api/v1/review-groups/validate
const validateOnHover = async (spelling: string) => {
  const validation = await api.validate(spelling, sessionId, groupId);
  setFeedback(validation);
};
```

---

## Testing Strategy

**Contract Tests** (`tests/contract/test_review_groups_api_010.py`):
- Verify all endpoints exist and accept correct parameters
- Test error cases (404, 422, validation failures)
- Test happy path (candidate selection, auto-collapse)
- Verify persistence (state saved to sidecar JSON)

**Integration Tests** (`tests/integration/test_review_groups_integration.py`):
- Test full workflow: load session → select candidates → verify consensus → export
- Test conflict detection across groups
- Test rejection workflow (mark rejected, verify UI state)

**Unit Tests** (`tests/unit/test_review_groups_service.py`):
- Test `validate_candidate_uniqueness()` with various inputs
- Test consensus detection logic
- Test state transitions (collapsed/expanded)

---

## Compatibility

**Existing Systems**:
- **review_session_persistence.py**: Enhanced to support new CandidateGroup entities (backward compatible)
- **CSV Export**: Unmodified; sidecar JSON is additive
- **Review View** (007): New React components integrated alongside existing review UI

**Migration Path**:
- Existing sessions without sidecar JSON load cleanly (no groups pre-loaded)
- New sessions created on first Review view load with fresh ReviewSession
- Full backward compatibility maintained

---

## Contract Conclusion

API is minimal and focused on core operations: candidate selection, validation, and state management. All endpoints persist state immediately to sidecar JSON. Frontend receives immediate validation feedback for responsive UX.

**Next Phase**: Implementation (backend service layer, React components, integration tests)
