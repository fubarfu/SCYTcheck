# Quickstart: Web Player UI (007)

## Prerequisites
- Python 3.11 environment configured for repository.
- Existing project dependencies installed from `requirements.txt`.
- Browser available locally (Edge/Chrome/Firefox).

## 1. Start Local App
- From repository root, launch the app entrypoint used by packaging/dev run.
- Expected behavior:
  - Local server starts.
  - Browser opens automatically to `localhost` Analysis view.

## 2. Verify Analysis View Parity
- Confirm presence of legacy parity controls in Analysis view:
  - YouTube URL input
  - Output folder picker
  - Output filename preview
  - Region selector launch
  - Start/Stop controls
  - Progress indicators
  - Context pattern controls
  - Filter non-matching toggle
  - Video quality selector
  - Detailed sidecar log toggle
  - Matching tolerance control
  - Frame gating toggle + threshold
  - Event merge gap control
  - OCR sensitivity control

## 3. Run Analysis
- Provide either:
  - YouTube URL, or
  - Local video file path
- Select output folder and scan region.
- Start analysis and validate live progress updates.
- Stop analysis mid-run once to verify partial-results path.

## 4. Verify Review View Workflow
- Open Review view using persistent top navigation.
- Load resulting CSV session and verify:
  - Candidate groups rendered with temporal/context cues.
  - Search/filter works in real-time.
  - Confirm/reject/edit/remove actions persist immediately.
  - Group bulk actions and manual regrouping function.
  - Unlimited undo reverses mutations in-order.

## 5. Verify Thumbnail + Deep Link UX
- For candidate rows:
  - Thumbnail renders and opens modal on click.
  - YouTube deep link shown only for YouTube-origin sessions.

## 6. Verify Export
- Export from Review and confirm files are generated:
  - Deduplicated names CSV
  - Full confirmed occurrences CSV

## 7. Verify Persistence
- Close browser tab and reopen UI.
- Reload same session and confirm review state is restored from sidecar JSON.

## 8. Validate Test Suites
- Run:
  - `cd src; pytest`
  - `cd src; ruff check .`
- Execute feature-specific integration tests for web workflow and schema gating.

## Stitch Artifacts Used
- Project: `projects/1293475510601425942`
- Design system asset: `assets/6844205393644582333`
- Exported screens (HTML + screenshots):
  - `specs/007-web-player-ui/stitch/screens/analysis-view.html`
  - `specs/007-web-player-ui/stitch/screens/analysis-running.html`
  - `specs/007-web-player-ui/stitch/screens/review-view.html`
  - `specs/007-web-player-ui/stitch/screens/thumbnail-modal.html`
  - `specs/007-web-player-ui/stitch/screens/region-selector-modal.html`

## Stitch Deviation Notes (T069)
- Current implementation preserves required flow and contracts from Stitch screens, with simplified visual treatment in some controls.
- Region selector modal currently uses numeric coordinate inputs rather than drag-canvas selection; this keeps schema-correct region capture while reducing implementation risk.
- Group review cards include separate temporal proximity and recommendation badges (FR-026/FR-031), but typography/spacing is an approximation of final Stitch polish.
