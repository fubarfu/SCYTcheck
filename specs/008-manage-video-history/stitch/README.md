# Stitch Artifact Index (Feature 008)

## Authority
- Stitch project: `projects/1293475510601425942` (SCYTcheck Web UI)
- Stitch remains authoritative for UI layout and hierarchy decisions.

## Downloaded Artifacts
- `analysis-view.html`
- `analysis-view.png`
- `analysis-running-state.html`
- `analysis-running-state.png`
- `review-view.html`
- `review-view.png`
- `scan-region-selector-overlay.html`
- `scan-region-selector-overlay.png`
- `frame-thumbnail-modal-overlay.html`
- `frame-thumbnail-modal-overlay.png`

## Stitch Screen Mapping
- Analysis View: `projects/1293475510601425942/screens/f7402167a28248a180a5efdf3a46c1cc`
- Analysis Running State: `projects/1293475510601425942/screens/4352dbb3d1494ac085550568aed93e84`
- Review View: `projects/1293475510601425942/screens/2c0fa9c23fdd48d7a913dfd6744c3f21`
- Scan Region Selector Overlay: `projects/1293475510601425942/screens/b28f75f678a54812994bedd7291de13c`
- Frame Thumbnail Modal Overlay: `projects/1293475510601425942/screens/c9dcec9785d34d23b03e296fc5b3c2c1`

## Planned Frontend Integration Points
- Navigation and view switching: `src/web/frontend/src/App.tsx`
- New history page container: `src/web/frontend/src/pages/HistoryPage.tsx`
- History actions row/card components: `src/web/frontend/src/components/HistoryEntryRow.tsx`
- History state and API binding: `src/web/frontend/src/state/historyStore.ts`
- Shared visual alignment: `src/web/frontend/src/styles/app.css` and `src/web/frontend/src/styles/theme.css`

## Usage Rule
- Implementations should follow these artifacts for structure and visual hierarchy.
- Any required technical deviation from Stitch should be documented in implementation notes and tests.

## Feature 008 Implementation Notes
- Analysis and Review shell spacing, panel elevation, and nav rhythm were preserved by extending existing `panel-card` and nav tokens used by `analysis-view` and `review-view` artifacts.
- The new History view uses the same card hierarchy (heading + metadata + action cluster) to stay consistent with Stitch section blocks while introducing history-specific actions.
- Reopen from History routes directly to Review and keeps non-blocking artifact warnings inline, matching the unobtrusive status-banner language from the running/review screens.
- Overlay and modal visual language remains unchanged by reusing existing review modal flow (`FrameThumbnailModal`) rather than introducing a new overlay pattern.
