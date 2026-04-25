# Research Phase: Collapsable Review Groups with Player Name Management

**Feature**: 010-collapse-player-groups | **Phase**: Phase 0 Research | **Date**: 2026-04-25

## Purpose

Consolidate technical findings and architectural decisions made during research phase. All NEEDS CLARIFICATION markers from the feature spec have been resolved through iterative clarification sessions.

## Key Technical Decisions

### 1. Consensus Detection Logic

**Decision**: Use **exact string matching** for consensus detection.

**Rationale**:
- Simplest, most transparent approach for user verification workflow
- Avoids false positives from fuzzy matching (e.g., "John Smith" vs "Jon Smith")
- Data integrity: user must consciously choose between alternatives
- Aligns with existing `thefuzz` usage in OCR post-processing (which is strictly for OCR validation, not consensus)

**Alternatives Considered**:
- Fuzzy matching (Levenshtein distance): Rejected due to potential false consensus detection; creates confusion about data accuracy
- Phonetic matching (Soundex/Metaphone): Rejected for same reason; too aggressive
- User-configurable threshold: Rejected as out-of-scope; adds settings complexity

**Outcome**: Consensus = all candidates in group have identical string values after trim/normalize

---

### 2. Persistence Strategy & Auto-Save

**Decision**: Store group consensus state in **sidecar review session JSON** (`<result>.review.json`) and integrate with existing `review_session_persistence.py` service.

**Rationale**:
- Aligns with existing architecture (feature 007-web-player-ui uses sidecar JSON for session state)
- Non-destructive: original CSV unmodified; consensus choices stored separately
- Auto-save on each group state change (collapse/expand, candidate selection)
- Survives application restart via session hydration on Review view load
- No database dependency; local file system only

**Alternatives Considered**:
- Direct CSV column addition: Rejected due to export format stability (CSV is immutable output format)
- In-memory only: Rejected due to loss of work on browser crash; aligns with stateless web principles but contradicts user expectations
- Settings file storage: Rejected; sidecar JSON semantically correct (per-video, not global)

**Outcome**: Enhanced `review_session_persistence.py` with methods `save_group_consensus(group_id, consensus_spelling)` and `load_group_consensus(video_id)`.

---

### 3. Uniqueness Validation Architecture

**Decision**: **Backend validation** via new `review_groups_service.py` with **frontend immediate feedback**.

**Rationale**:
- Backend enforces data integrity (prevents accidental duplicates)
- Frontend displays context-aware inline error immediately (UX responsiveness)
- Error message includes conflicting group reference (helps user resolve)
- Service layer decouples validation logic from routes (testable, reusable)

**Alternatives Considered**:
- Frontend-only validation: Rejected; can be bypassed; no data integrity guarantee
- Batch validation on export: Rejected; too late; user unaware of conflict mid-session
- Real-time WebSocket validation: Rejected as over-engineering; single-video analysis scope

**Outcome**: `review_groups_service.py` with method `validate_candidate_uniqueness(candidate_name, excluded_group_id) -> (is_valid, conflict_group_id, conflict_name)`.

---

### 4. Rejection Workflow (Non-Destructive)

**Decision**: **Visual marking + state tracking** (strikethrough, faded color, disabled interaction).

**Rationale**:
- Preserves user intent (shows what was considered but rejected)
- Supports audit trail (can track which candidates were evaluated)
- Allows undo via state reversal (user can change mind without data loss)
- Avoids destructive deletion (reduces risk of accidental irreversible actions)

**Alternatives Considered**:
- Physical deletion from list: Rejected; loses information; complicates undo
- Modal confirmation dialog: Rejected; interruptive; doesn't match modern UI patterns
- Trash bin recovery: Rejected as out-of-scope; adds complexity

**Outcome**: Rejected candidates tracked in `CandidateGroup.rejected_candidate_ids` array; UI renders strikethrough + disabled state for visual feedback.

---

### 5. Validation Feedback Pattern

**Decision**: **Inline + contextual error messages** below selected candidate with optional hint below error.

**Rationale**:
- Inline position keeps error near source (selected candidate causing error)
- Context-aware message (shows conflicting group) helps user understand issue
- Hint provides actionable next step (choose different spelling)
- Reduces need for documentation (message is self-explanatory)

**Alternatives Considered**:
- Toast notifications: Rejected; fleeting; user may miss context reference
- Modal dialogs: Rejected; interruptive; blocks interaction
- Form-level errors at top: Rejected; disconnected from candidate causing issue

**Outcome**: Error displayed with light red background (#c54d4a 20% opacity), red text (#fa746f), icon (⚠), and optional hint in smaller font below.

---

### 6. Data Integrity: Duplicate Prevention

**Decision**: **Uniqueness constraint** enforced at backend service layer; validated before state persistence.

**Rationale**:
- Prevents invalid states from being saved
- Constraint checked at transaction boundary (group state change)
- Error prevents state update; user must choose different spelling
- Aligns with database-like transaction semantics (ACID properties simulated)

**Alternatives Considered**:
- Warn but allow: Rejected; violates spec requirement for "zero duplicate names"
- Auto-rename conflicting candidates: Rejected; modifies user-selected data without consent
- Soft constraint (warning only): Rejected; doesn't guarantee integrity

**Outcome**: Service method returns validation result; state only updates if valid.

---

### 7. UI State Transitions & Collapse Logic

**Decision**: **Automatic collapse on consensus** (all candidates identical); **manual toggle** otherwise.

**Rationale**:
- Reduces UI clutter (resolved groups out of view)
- Signals completion to user (visual feedback of progress)
- Manual toggle preserves user choice to review conflict details again
- Matches user mental model (collapsed = "done", expanded = "needs attention")

**Alternatives Considered**:
- Always collapsed by default: Rejected; hides conflicts; requires explicit expand to see issues
- Always expanded: Rejected; no visual progress indicator; cluttered UI
- User preference setting: Rejected as out-of-scope; adds complexity

**Outcome**: Group collapse state stored in `CandidateGroup.is_collapsed`; set to `true` only when consensus detected.

---

### 8. Integration with Existing 007 Architecture

**Decision**: Extend existing `src/web/frontend` (React/Vite) and `src/web/api` without creating new top-level directories.

**Rationale**:
- Continuation of 007-web-player-ui; code reuse
- Consistent with project modularity principle
- Simpler deployment (single frontend bundle, single API service)
- Reduces configuration complexity

**Alternatives Considered**:
- Separate `feature-010/` microservice: Rejected; over-architecture; single feature scope
- New `/frontend-2` directory: Rejected; violates principle of simplicity

**Outcome**: New React components in `src/web/frontend/src/components/` and new Python service module in `src/web/api/`.

---

## Technology Stack Confirmation

All technology choices verified against project constitution and existing infrastructure:

| Technology | Role | Rationale | Existing? |
| --- | --- | --- | --- |
| Python 3.11 | Backend validation, group logic | Consistent with existing services | ✓ Yes (007) |
| React/TypeScript | Frontend UI components | Consistent with 007-web-player-ui | ✓ Yes (007) |
| Vite | Frontend build | Project standard | ✓ Yes (007) |
| pytest | Backend testing | Project standard | ✓ Yes |
| Local JSON sidecar | Session persistence | Existing pattern from 007 | ✓ Yes (007) |
| CSV output | Analysis results | Immutable export format | ✓ Yes (all features) |

---

## Outstanding Dependencies

| Dependency | Status | Impact |
| --- | --- | --- |
| 007-web-player-ui Review view structure | ✓ Available | Requires understanding of existing `ReviewGroupsPanel.tsx` |
| Google Stitch UI design screens | ✓ Generated (3 screens) | 5 key UI states now designed; reference for component development |
| `review_session_persistence.py` extension points | ✓ Available | Existing service can be extended without breaking changes |

---

## Research Conclusion

All architectural decisions resolved through iterative clarification and pattern analysis from existing features (007-web-player-ui, 006-optimize-analysis-hotpaths). No NEEDS CLARIFICATION markers remain.

**Next Phase**: Phase 1 Design (data-model.md, contracts/, quickstart.md)
