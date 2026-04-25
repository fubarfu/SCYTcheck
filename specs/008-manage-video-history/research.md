# Research: Managed Video Analysis History

## Decision 1: Persistent history index format
- Decision: Store video history in a dedicated JSON index under `%APPDATA%/SCYTcheck/video_history.json` (fallback beside existing local settings file when app data is unavailable).
- Rationale: JSON supports nested context and run metadata naturally, aligns with existing local settings persistence, and requires no new dependency.
- Alternatives considered:
  - CSV-only history index: rejected because nested context and run arrays become fragile and hard to validate.
  - SQLite: rejected because it adds operational complexity and migration overhead for a local desktop workflow.

## Decision 2: Deterministic merge identity and duplicate handling
- Decision: Merge completed analyses into an existing `VideoHistoryEntry` when `canonical_source` and `duration_seconds` both match exactly; if duration is missing or malformed, create a new entry flagged `potential_duplicate=true`.
- Rationale: Matches clarified requirement for deterministic identity while preserving ambiguous cases for explicit user review.
- Alternatives considered:
  - Source-only identity: rejected because same source can point to edited content with different duration.
  - Fuzzy duration tolerance: rejected because it introduces non-determinism and hidden merge behavior.

## Decision 3: Reopen workflow and derived review artifacts
- Decision: Reopen loads `PersistedAnalysisContext`, then routes directly to Review and resolves result files from the persisted output folder (including sidecar review JSON when present).
- Rationale: Satisfies FR-006 to FR-008 with minimal user interaction and keeps review loading deterministic.
- Alternatives considered:
  - Manual CSV selection on reopen: rejected because it violates auto-discovery requirements.
  - Re-run analysis before review: rejected because it undermines "resume prior work" outcome.

## Decision 4: History-management API surface
- Decision: Add dedicated local API endpoints for list, reopen, delete, and merge-write operations, reusing existing analysis/review service functions where possible.
- Rationale: Keeps frontend state simple, supports contract testing, and isolates business logic in backend service layer.
- Alternatives considered:
  - Frontend-only file operations: rejected because filesystem access should remain backend-owned.
  - Overloading existing review endpoints: rejected because history semantics become implicit and harder to test.

## Decision 5: Stitch-driven UI planning strategy
- Decision: Keep Google Stitch project `projects/1293475510601425942` as UI authority; use downloaded artifacts in `specs/008-manage-video-history/stitch/` as planning references for History view integration and consistency checks.
- Rationale: Constitution requires Stitch-authoritative web UI decisions; existing screens establish hierarchy and component language to extend with a third tab/view.
- Alternatives considered:
  - Designing History view from scratch in code: rejected because it risks drift from approved UI language.
  - Ignoring downloaded HTML in planning docs: rejected because traceability from design artifact to implementation point is required.

## Decision 6: Frontend integration boundaries
- Decision: Integrate history navigation and view within existing React app structure: route/tab in `App.tsx`, page in `pages`, row components in `components`, store in `state`, and style alignment in shared CSS.
- Rationale: Preserves modular architecture and minimizes risk to existing analysis/review flows.
- Alternatives considered:
  - New standalone frontend entrypoint: rejected because it increases complexity and duplicates shell/state logic.
  - Embedding full history logic into existing pages: rejected because it reduces maintainability and testability.
