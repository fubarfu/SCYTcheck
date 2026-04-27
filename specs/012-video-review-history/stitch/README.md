# Stitch Artifact Index (Feature 012)

## Authority

- Stitch project: `projects/1293475510601425942`
- Design system: `assets/6844205393644582333` (`SCYTcheck Dark`)
- Stitch remains authoritative for UI structure, hierarchy, and visual states for this feature.

## Generated Screens

- `projects/1293475510601425942/screens/58b4fe5ef0c14e6ead4a05b7128c76e1`
  - Title: Review - Edit History Update
  - Local artifacts:
    - `review-edit-history-update.html`
    - `review-edit-history-update.png`

- `projects/1293475510601425942/screens/bf9df208fb654424b42f496d79def82b`
  - Title: Review - Restored Snapshot State
  - Local artifacts:
    - `review-restored-snapshot-state.html`
    - `review-restored-snapshot-state.png`

- `projects/1293475510601425942/screens/866f61b774804cccaea05150abdbb421`
  - Title: Review View (Read-Only)
  - Local artifacts:
    - `review-read-only-lock-state.html`
    - `review-read-only-lock-state.png`

## Scope Captured by Prototypes

1. Bottom-panel Edit History list with timestamp and summary counts.
2. Selected snapshot restore feedback and active-row highlight.
3. Read-only lock warning mode with disabled mutation controls.

## Implementation Mapping

- Review page orchestration: `src/web/frontend/src/pages/ReviewPage.tsx`
- New history panel UI: `src/web/frontend/src/components/EditHistoryPanel.tsx`
- Lock banner + read-only control state: `src/web/frontend/src/components/ReviewLockBanner.tsx`
- History API/state integration: `src/web/frontend/src/state/reviewStore.ts`

## Deviation Log

- No approved deviations recorded at planning time.
- If implementation requires deviation, document the rationale in this file and in `specs/012-video-review-history/quickstart.md`.
