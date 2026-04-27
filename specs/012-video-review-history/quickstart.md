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

Run all 012 tests at once:

```powershell
python -m pytest tests/unit/test_review_history_snapshots_012.py tests/unit/test_review_history_restore_012.py tests/integration/test_review_history_panel_flow_012.py tests/integration/test_review_history_readonly_lock_012.py tests/contract/test_video_review_history_api_012.py -v
cd src/web/frontend ; npx vitest run ; cd ..\..\..
```

## 5. Implementation Notes

### Deviations from Stitch Screens

- **Workspace video_id stability**: Video identity is derived from a SHA-1 hash of the CSV file's resolved absolute path (not the YouTube video ID). This keeps the implementation self-contained and avoids depending on the analysis pipeline to provide a stable ID.

- **Sidecar passthrough**: `analysis_settings`, `grouping_settings`, and `scan_region` are preserved as-is in the sidecar JSON. The review system does not interpret or transform these; they round-trip opaquely.

- **History compaction**: Entries older than `max_uncompressed` (default 50) are flagged `compressed: true` in the history JSON. The snapshot data is retained — compression only flags older entries for UI display purposes, consistent with FR-015.

- **Lock enforcement**: The single-writer lock is in-memory per server process (not persisted on disk). Restarting the server releases all locks. This is acceptable for the current local-server usage model.

- **Restore provenance snapshot**: The `create_restore_snapshot` flag on the restore endpoint defaults to `true` in the UI. The backend always writes a provenance snapshot when this flag is set, before applying the restore.

### Test Coverage Summary

| File | Tests |
|------|-------|
| `tests/unit/test_review_history_snapshots_012.py` | 7 (including US2 stable identity) |
| `tests/unit/test_review_history_restore_012.py` | 5 (including US3 reviewed names and candidate-state restore regression) |
| `tests/unit/test_review_lock_behavior_012.py` | 2 |
| `tests/integration/test_review_history_panel_flow_012.py` | 11 (including perf, isolation, bootstrap) |
| `tests/integration/test_review_history_readonly_lock_012.py` | 1 |
| `tests/contract/test_video_review_history_api_012.py` | 7 (including session refresh workspace metadata) |
| `src/web/frontend/tests/review/editHistoryPanel.test.tsx` | 9 |
| `src/web/frontend/tests/review/reviewLockBanner.test.tsx` | 5 |
| **Total** | **47** |

## 6. Manual Validation Flow

1. Analyze/load a video and open Review view.
2. Confirm the Edit History panel is visible in the bottom review area.
3. Execute state-changing actions (confirm/reject/unreject/restore) and verify new history rows appear.
4. Select an older history row and run restore; verify counts and candidate group states match selected row.
5. Open same video workspace from second session; verify read-only lock warning and disabled mutation controls.
6. Verify history remains visible and inspectable in read-only mode.

### Final Manual Validation Notes

- Executed on 2026-04-27 against the local app started via `python -m src.main`.
- Verified writer-session flow in Review UI using a local result CSV: state-changing actions created append-only history entries in the Edit History panel.
- Verified restore flow: restoring an older `confirm` snapshot changed the visible review state from `1 / 2 resolved` with Bob rejected to `2 / 2 resolved` with Bob confirmed, and added a provenance `restore` history entry.
- Verified second-session read-only behavior: reopening the same workspace produced the read-only lock banner and prevented mutation controls from being used.
- Verified the history panel remains visible in read-only mode and older entries remain selectable/restorable by the writer session.

## 7. Definition of Done

- Snapshot creation obeys trigger rules from FR-016.
- Restore is deterministic and creates restore provenance snapshot.
- Single-writer lock with read-only fallback is enforced.
- Per-video workspace identity uses stable `video_id`.
- UI behavior aligns with Stitch artifacts for feature 012 states.