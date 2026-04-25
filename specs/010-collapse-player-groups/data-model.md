# Data Model: Collapsable Review Groups with Player Name Management

**Feature**: 010-collapse-player-groups | **Phase**: Phase 1 Design | **Date**: 2026-04-25

## Entity Definitions

### 1. CandidateGroup

Represents a set of OCR-extracted candidate spellings for a single player name field that require resolution.

```python
class CandidateGroup:
    group_id: str                          # Unique identifier within video result
    field_name: str                        # e.g., "player_name"
    frame_indices: List[int]               # OCR frames where this extraction appeared
    consensus_spelling: Optional[str]      # User-confirmed canonical spelling (null = unresolved)
    is_collapsed: bool                     # UI state: collapsed when consensus reached
    candidates: List[Candidate]            # All spelling variants
    rejected_candidate_ids: List[str]      # IDs of candidates marked as rejected (non-destructive)
    last_modified_at: datetime             # Timestamp of last change
    
    # Validation
    @property
    def is_consensus_reached(self) -> bool:
        """True if all non-rejected candidates have identical spelling"""
        active_candidates = [c for c in self.candidates if c.id not in self.rejected_candidate_ids]
        if len(active_candidates) == 0:
            return False
        return all(c.spelling == active_candidates[0].spelling for c in active_candidates)
    
    @property
    def active_spellings(self) -> Set[str]:
        """Unique spellings from non-rejected candidates"""
        active_candidates = [c for c in self.candidates if c.id not in self.rejected_candidate_ids]
        return set(c.spelling for c in active_candidates)
```

**Validation Rules**:
- `group_id` must be unique within a video result
- `frame_indices` must contain at least one frame index
- `candidates` must contain at least one candidate
- `consensus_spelling` must match one of the active candidate spellings OR be null
- `rejected_candidate_ids` must contain only IDs from `candidates`
- `is_collapsed` automatically set to `True` when `is_consensus_reached` is `True` (immutable during consensus)

**State Transitions**:
- Created: `consensus_spelling=None, is_collapsed=False`
- After candidate selection: `consensus_spelling=selected_value`
- Consensus detected: `is_collapsed=True` (automatic)
- User expands collapsed group: `is_collapsed=False` (manual toggle)

**Persistence**: Stored in sidecar JSON file as part of `ReviewSession.groups`

---

### 2. Candidate

Represents a single spelling variant extracted from video frames.

```python
class Candidate:
    id: str                               # UUID; unique within CandidateGroup
    spelling: str                         # The OCR-extracted text (e.g., "Jon Smith")
    confidence: float                     # OCR confidence score [0.0, 1.0]
    source_frame_indices: List[int]       # Frames where this spelling appeared
    
    # Validation
    @property
    def is_valid(self) -> bool:
        """True if spelling is non-empty and confidence > 0"""
        return len(self.spelling.strip()) > 0 and self.confidence >= 0.0
```

**Validation Rules**:
- `id` must be unique within parent `CandidateGroup`
- `spelling` must be non-empty string (after strip)
- `confidence` must be in range [0.0, 1.0]
- `source_frame_indices` must be non-empty

**Relationships**:
- Parent: `CandidateGroup`
- Immutable after creation (OCR source data)

---

### 3. ReviewSession

Container for all candidate groups and their consensus state for a single video analysis.

```python
class ReviewSession:
    session_id: str                       # UUID; unique per video analysis
    video_path: str                       # Absolute path to analyzed video
    analysis_completed_at: datetime       # When OCR analysis finished
    review_started_at: datetime           # When user opened Review view
    groups: Dict[str, CandidateGroup]     # group_id -> CandidateGroup
    
    # Validation
    @property
    def all_groups_consensus(self) -> bool:
        """True if all groups have reached consensus"""
        return all(g.is_consensus_reached for g in self.groups.values())
    
    @property
    def consensus_count(self) -> int:
        """Number of groups with consensus reached"""
        return sum(1 for g in self.groups.values() if g.is_consensus_reached)
    
    @property
    def conflict_count(self) -> int:
        """Number of groups without consensus"""
        return len(self.groups) - self.consensus_count
```

**Validation Rules**:
- `session_id` must be globally unique
- `video_path` must exist on file system
- `groups` dict keys must match `CandidateGroup.group_id` values
- `analysis_completed_at <= review_started_at`

**Persistence**: Serialized as `<result>.review.json` file (sidecar to CSV export)

**State Transitions**:
- Created when Review view loads (hydrate from existing session or create new)
- Modified as user selects candidates and groups reach consensus
- Finalized when user exports analysis results

---

### 4. ValidationResult

Data class returned by uniqueness validation service.

```python
@dataclass
class ValidationResult:
    is_valid: bool                        # False if validation failed
    candidate_name: str                   # The name being validated
    error_message: Optional[str]          # Null if valid; user-facing message if invalid
    conflict_group_id: Optional[str]      # Which group has conflicting candidate
    conflict_spelling: Optional[str]      # What the conflict spelling is
    hint: Optional[str]                   # Optional actionable hint for user
```

**Example Valid Result**:
```python
ValidationResult(
    is_valid=True,
    candidate_name="John Smith",
    error_message=None,
    conflict_group_id=None,
    conflict_spelling=None,
    hint=None
)
```

**Example Invalid Result**:
```python
ValidationResult(
    is_valid=False,
    candidate_name="Michael Jordan",
    error_message="Name already used in Group 3 - Michael Jordan",
    conflict_group_id="group_3",
    conflict_spelling="Michael Jordan",
    hint="Choose a different spelling from the group"
)
```

**Persistence**: Not persisted; ephemeral validation response

---

## Entity Relationships

```
ReviewSession (1)
    ├── * CandidateGroup
    │   ├── * Candidate (immutable)
    │   └── List[str] rejected_candidate_ids (references Candidate.id)
    └── session_id: str (file path key)

CandidateGroup
    ├── consensus_spelling: references Candidate.spelling
    └── rejected_candidate_ids[]: references Candidate.id
```

---

## Data Flow: Consensus Detection

```
1. User selects candidate in UI
   └─> CandidateRadioButton.onChange fires

2. Frontend validates selection
   └─> ValidationFeedback component calls review_groups_service

3. Backend validates uniqueness
   └─> review_groups_service.validate_candidate_uniqueness()
   └─> Returns ValidationResult with error details (if any)

4. Frontend handles validation response
   ├─> If valid:
   │   ├─> Update group consensus state in UI
   │   └─> Persist to sidecar JSON via API
   └─> If invalid:
       └─> Display inline error message below candidate

5. Backend checks consensus detection
   └─> After successful update, check is_consensus_reached
   └─> If true, auto-collapse group in sidecar JSON

6. Frontend reflects UI state change
   └─> Receive updated group state from API
   └─> Render collapsed/expanded state
```

---

## Storage Format: Sidecar JSON

**File Location**: `<result>.review.json` (sidecar to main CSV export)

**Example Structure**:
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
      "consensus_spelling": "John Smith",
      "is_collapsed": true,
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
      "last_modified_at": "2026-04-25T10:36:15Z"
    }
  }
}
```

---

## Validation Constraints

| Constraint | Entity | Rule | Enforced At |
| --- | --- | --- | --- |
| Unique group ID | CandidateGroup | `group_id` unique within ReviewSession | Backend + Frontend |
| Unique candidate ID | Candidate | `id` unique within CandidateGroup | Backend + Frontend |
| Unique player name | CandidateGroup | No duplicate `consensus_spelling` across groups | Backend validation service |
| Non-empty spelling | Candidate | `len(spelling.strip()) > 0` | Backend + Validation |
| Valid confidence | Candidate | `0.0 <= confidence <= 1.0` | OCR service + Validation |
| Consensus match | CandidateGroup | `consensus_spelling in active_spellings` | Backend validation |
| Immutable consensus on consensus | CandidateGroup | `is_collapsed` locked to `True` when consensus | Backend + UI |

---

## Migration & Backward Compatibility

**Existing CSV Export**: Unmodified. Sidecar JSON is additive; no breaking changes to export format.

**Existing ReviewSession**: When loading a legacy review session (without sidecar JSON), create new ReviewSession with empty `groups` (no existing consensus state). User can then interact with groups normally.

**Version Strategy**: Sidecar JSON includes optional `format_version: "1.0"` field for future migrations.

---

## Design Conclusion

Entity model is simple, testable, and aligns with existing review workflow. All validation constraints are enforced at backend service layer. Frontend receives clean validation results for immediate UX feedback.

**Next Phase**: Phase 1 Contracts & API Design (contracts/review-groups-api.md)
