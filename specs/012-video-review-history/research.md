# Research Phase: Video-Centric Review History

**Feature**: 012-video-review-history | **Phase**: Phase 0 Research | **Date**: 2026-04-27

## Purpose

Resolve technical decisions required by the feature spec and eliminate all planning-time ambiguities before implementation.

## Decision 1: Snapshot Persistence Model

**Decision**: Persist a full review-state snapshot per history entry in an append-only per-video history container.

**Rationale**:
- Deterministic restore does not depend on replaying mutation diffs.
- Easier corruption recovery because each entry is self-contained.
- Aligns directly with FR-013 and reduces behavioral ambiguity.

**Alternatives considered**:
- Delta/diff-only history: Smaller storage but restore complexity and replay fragility increase.
- Periodic full checkpoints plus deltas: More complex logic than needed for current scope.

## Decision 2: Snapshot Creation Trigger Rules

**Decision**: Create snapshots only on state-changing review mutations.

**Rationale**:
- Prevents noisy history growth from passive UI interactions.
- Keeps timeline semantically meaningful for user restore intent.
- Aligns with FR-016.

**Alternatives considered**:
- Snapshot on all UI interactions: Too much noise and storage growth.
- Manual snapshot button only: Risks missing key recoverable states.

## Decision 3: Long-Term Retention and Compression

**Decision**: Retain all snapshots while allowing compression of older entries in the same container.

**Rationale**:
- Preserves full auditability and restore capability.
- Controls storage growth without deleting historical states.
- Aligns with FR-015.

**Alternatives considered**:
- Time-based deletion: Violates restore completeness expectations.
- Fixed cap (last N only): Could silently remove important states.

## Decision 4: Concurrent Access and Locking

**Decision**: Enforce single-writer lock per video workspace; additional sessions are read-only with lock warning.

**Rationale**:
- Prevents race conditions and out-of-order snapshot writes.
- Keeps behavior simple and predictable for local desktop workflow.
- Aligns with FR-014.

**Alternatives considered**:
- Last-write-wins optimistic edits: High risk of accidental overwrite.
- Multi-writer merge: Overly complex for current product model.

## Decision 5: Workspace Identity and Folder Naming

**Decision**: Use stable `video_id` for workspace folder identity and store display title in metadata.

**Rationale**:
- Path identity remains stable when display naming changes.
- Avoids filesystem issues from title edits/special characters.
- Aligns with FR-017.

**Alternatives considered**:
- Folder name from current title: Unstable and rename-prone.
- Hash-only path without metadata title: Poor usability/debuggability.

## Decision 6: Stitch-Driven UI Design Direction

**Decision**: Use Stitch project `projects/1293475510601425942` as authoritative UI design source for 012 review-history states and download generated HTML/PNG artifacts.

**Rationale**:
- Constitution principle VIII requires Stitch authority for web UI decisions.
- Captures concrete implementation-ready reference for review history panel, restored-state feedback, and read-only lock mode.

**Alternatives considered**:
- Hand-authored mockups only: Not constitution-compliant for this feature class.
- Reusing old screens without new generation: Misses new 012 UI state requirements.

## Stitch Outputs Used in Phase 1

Generated screens:
- `projects/1293475510601425942/screens/58b4fe5ef0c14e6ead4a05b7128c76e1` (Review - Edit History Update)
- `projects/1293475510601425942/screens/bf9df208fb654424b42f496d79def82b` (Review - Restored Snapshot State)
- `projects/1293475510601425942/screens/866f61b774804cccaea05150abdbb421` (Review View - Read-Only)

Downloaded local artifacts:
- `specs/012-video-review-history/stitch/review-edit-history-update.html`
- `specs/012-video-review-history/stitch/review-edit-history-update.png`
- `specs/012-video-review-history/stitch/review-restored-snapshot-state.html`
- `specs/012-video-review-history/stitch/review-restored-snapshot-state.png`
- `specs/012-video-review-history/stitch/review-read-only-lock-state.html`
- `specs/012-video-review-history/stitch/review-read-only-lock-state.png`

## Research Conclusion

All technical context items are resolved and no `NEEDS CLARIFICATION` markers remain.