# Quickstart: Managed Video Analysis History

## Goal
Validate that video history persistence, deterministic merge, reopen restore, and history management UI behavior work end-to-end in the local web application.

## Preconditions
- Python environment and frontend dependencies installed.
- Existing web UI feature flow for Analysis and Review is runnable.
- Stitch artifacts available in `specs/008-manage-video-history/stitch/`.

## Run
1. Start backend and web frontend using existing local run workflow.
2. Open the web UI and verify three primary views are available: Analysis, Review, and History.

## Validation Flow A: Create and Reopen History Entry
1. Run analysis for one video source and wait for completion.
2. Confirm history list shows a new entry.
3. From History view, choose Reopen.
4. Verify:
   - Review view opens automatically.
   - Analysis context is restored (region, output folder, patterns, settings).
   - Results are auto-discovered from the output folder without manual file browsing.

## Validation Flow B: Deterministic Merge
1. Re-run analysis on same canonical source and same duration.
2. Confirm no duplicate visible history item is added.
3. Confirm `run_count` increments for existing history entry.

## Validation Flow C: Missing/Malformed Duration
1. Simulate or inject an analysis completion with missing or invalid duration metadata.
2. Confirm new history entry is created with potential-duplicate indicator.
3. Confirm no auto-merge occurs.

## Validation Flow D: Delete Behavior
1. Delete one history entry from History view.
2. Confirm it is removed from the managed list.
3. Confirm underlying output files remain on disk.

## Validation Flow E: Missing Output Folder
1. Reopen a history entry whose output folder is unavailable.
2. Confirm user receives warning about missing artifacts.
3. Confirm history metadata remains accessible and navigation is not hard-failed.

## Stitch Reference Checks
- Compare implemented Analysis/Review shell and modal language with:
  - `specs/008-manage-video-history/stitch/analysis-view.html`
  - `specs/008-manage-video-history/stitch/analysis-running-state.html`
  - `specs/008-manage-video-history/stitch/review-view.html`
  - `specs/008-manage-video-history/stitch/scan-region-selector-overlay.html`
  - `specs/008-manage-video-history/stitch/frame-thumbnail-modal-overlay.html`
- Ensure History view integration follows the same design language and hierarchy rules from Stitch artifacts.

## Suggested Test Coverage
- Unit:
  - merge key generation and canonical source normalization
  - duration edge handling and potential-duplicate flagging
  - history persistence read/write guards
- Contract:
  - `GET /api/history/videos`
  - `POST /api/history/merge-run`
  - `POST /api/history/reopen`
  - `DELETE /api/history/videos/{history_id}`
- Integration:
  - analyze -> merge -> history list -> reopen -> review auto-load
  - missing output folder warning path
