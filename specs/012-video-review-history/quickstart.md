# Quickstart: Video-Centric Review History (Feature 012)

**Feature**: 012-video-review-history | **Date**: 2026-04-27

## 1. Setup

From repository root:

```powershell
cd c:\Users\SteSt\source\SCYTcheck
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Frontend dependencies:

```powershell
cd src/web/frontend
npm install
cd ..\..\..
```

## 2. Run App

```powershell
cd c:\Users\SteSt\source\SCYTcheck
python -m src.main
```

Verify health endpoint:

```powershell
curl http://127.0.0.1:8765/api/health
```

Expected:
- `{"status":"ok"}`

## 3. Stitch Artifacts

Feature 012 UI prototypes are in:
- `specs/012-video-review-history/stitch/review-edit-history-update.html`
- `specs/012-video-review-history/stitch/review-edit-history-update.png`
- `specs/012-video-review-history/stitch/review-restored-snapshot-state.html`
- `specs/012-video-review-history/stitch/review-restored-snapshot-state.png`
- `specs/012-video-review-history/stitch/review-read-only-lock-state.html`
- `specs/012-video-review-history/stitch/review-read-only-lock-state.png`

Open HTML files in a browser to inspect implementation targets.

## 4. Targeted Tests

Run planned feature tests (as they are implemented):

```powershell
pytest tests/unit/test_review_history_snapshots_012.py -v
pytest tests/unit/test_review_history_restore_012.py -v
pytest tests/unit/test_review_lock_behavior_012.py -v
pytest tests/contract/test_video_review_history_api_012.py -v
pytest tests/integration/test_review_history_panel_flow_012.py -v
pytest tests/integration/test_review_history_readonly_lock_012.py -v
```

Frontend tests:

```powershell
cd src/web/frontend
npx vitest run tests/review/editHistoryPanel.test.tsx tests/review/reviewLockBanner.test.tsx
```

## 5. Manual Validation Flow

1. Analyze/load a video and open Review view.
2. Confirm the Edit History panel is visible in the bottom review area.
3. Execute state-changing actions (confirm/reject/unreject/restore) and verify new history rows appear.
4. Select an older history row and run restore; verify counts and candidate group states match selected row.
5. Open same video workspace from second session; verify read-only lock warning and disabled mutation controls.
6. Verify history remains visible and inspectable in read-only mode.

## 6. Definition of Done

- Snapshot creation obeys trigger rules from FR-016.
- Restore is deterministic and creates restore provenance snapshot.
- Single-writer lock with read-only fallback is enforced.
- Per-video workspace identity uses stable `video_id`.
- UI behavior aligns with Stitch artifacts for feature 012 states.