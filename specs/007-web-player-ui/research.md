# Research: Web Player UI (007)

## Decision 1: Stitch Is The Authoritative UI Source
- Decision: Use Stitch project `projects/1293475510601425942` and design system asset `assets/6844205393644582333` as the UI source of truth for all web views.
- Rationale: Constitution v1.3.0 mandates Stitch authority for web UI design decisions and this feature explicitly requires a modern two-view web UI with full parity.
- Alternatives considered:
  - Hand-authored wireframes in markdown: rejected because it weakens design authority and drifts from constitution.
  - Direct implementation without pre-approved screens: rejected because it increases rework risk and review ambiguity.

## Decision 2: Core Screen Set For Feature Scope
- Decision: Define and export five canonical desktop screens from Stitch:
  1. Analysis View (idle)
  2. Analysis View (running)
  3. Review View
  4. Frame Thumbnail Modal
  5. Scan Region Selector Modal
- Rationale: These screens cover all required primary interactions in FR-017 through FR-034 and user stories P0-P5.
- Alternatives considered:
  - Only two high-level screens (Analysis/Review): rejected because modal-heavy flows (region selection and thumbnail zoom) become underspecified.
  - Generating many micro-state screens: rejected as over-scoped for planning phase.

## Decision 3: Web Architecture And Runtime Integration
- Decision: Keep a single Python project with local FastAPI-style HTTP routes under `src/web/api/` and static frontend assets under `src/web/frontend/`.
- Rationale: Reuses existing repository structure and supports portable local execution (`localhost`) with minimal operational complexity.
- Alternatives considered:
  - Split backend/frontend repositories: rejected due to packaging overhead and drift risk.
  - External hosted backend: rejected due to local-only assumption and portable executable requirement.

## Decision 4: Session Persistence And Mutations
- Decision: Persist review session state after each mutating action into sidecar JSON adjacent to CSV (`result.review.json`).
- Rationale: Satisfies FR-011 and edge-case recovery requirements; prevents data loss on refresh/close.
- Alternatives considered:
  - Browser local storage only: rejected because it is non-portable and fragile across browsers/profiles.
  - Manual save checkpoints: rejected because FR-011 requires immediate persistence.

## Decision 5: Candidate Grouping Strategy
- Decision: Group candidates via combined signal of fuzzy text similarity and temporal proximity, with immediate regroup on threshold or inline edit changes.
- Rationale: Directly satisfies FR-007 and FR-034 while enabling user comprehension of confidence quality.
- Alternatives considered:
  - Text-only grouping: rejected due to poorer clustering for near-time repeated detections.
  - Fixed threshold without user control: rejected due to FR-007 slider requirement.

## Decision 6: Thumbnail Delivery Strategy
- Decision: Prefer persisted detection-time frames for YouTube runs; allow local video on-demand extraction with cache fallback to sibling frame directory.
- Rationale: Aligns with FR-024 clarifications and keeps review fast while preserving local-source flexibility.
- Alternatives considered:
  - Always on-demand extraction: rejected for YouTube streams due to runtime instability and repeated seeks.
  - Always pre-generate all frames for local files: rejected for heavy IO cost on large videos.

## Decision 7: Export Contract
- Decision: Export two outputs from Review:
  - Deduplicated confirmed names CSV
  - Confirmed occurrences CSV retaining timestamp/frame reference
- Rationale: Matches FR-010 and supports downstream auditing plus concise player lists.
- Alternatives considered:
  - Single merged export: rejected due to mixed consumer needs.

## Decision 8: Recommendation System Surface
- Decision: Keep recommendations advisory only with adjustable threshold, shown at both group and candidate levels.
- Rationale: Meets FR-031 while preserving user authority and preventing accidental automation.
- Alternatives considered:
  - Auto-confirm high-confidence candidates: rejected because FR-031 forbids automatic state changes.

## Decision 9: Theme Behavior
- Decision: Default to dark mode on first launch, persist user theme in existing settings file, and expose one global nav toggle.
- Rationale: Satisfies FR-032 and keeps consistent, low-friction behavior.
- Alternatives considered:
  - Follow OS theme on first run: rejected because FR-032 explicitly overrides this behavior.

## Decision 10: Validation And Quality Gates
- Decision: Enforce schema/version validation for loaded result CSVs prior to session creation and fail closed on malformed input.
- Rationale: Implements FR-033 and avoids partially corrupted review sessions.
- Alternatives considered:
  - Best-effort partial import: rejected due to silent data-quality risk.
