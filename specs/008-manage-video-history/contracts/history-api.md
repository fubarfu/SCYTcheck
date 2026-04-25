# Contract: Video History API (Web UI 008)

## Scope
Contracts between History view and local Python server for video history listing, merge updates, reopen restore, and deletion.

## Base
- Base URL: `http://127.0.0.1:<port>` (local only)
- Content type: `application/json`

## Endpoint: `GET /api/history/videos`
- Purpose: List persistent video history entries for History view.
- Query params:
  - `include_deleted` (optional, default `false`)
  - `limit` (optional, default `200`, max `1000`)
- Response 200:
```json
{
  "items": [
    {
      "history_id": "vh_001",
      "display_name": "match01.mp4",
      "canonical_source": "c:/videos/match01.mp4",
      "duration_seconds": 743,
      "potential_duplicate": false,
      "run_count": 3,
      "output_folder": "C:/output/match01",
      "updated_at": "2026-04-25T13:20:00Z"
    }
  ],
  "total": 1
}
```

## Endpoint: `POST /api/history/merge-run`
- Purpose: Persist a completed analysis run and merge into canonical history entry when merge key matches.
- Request body:
```json
{
  "source_type": "local_file",
  "source_value": "C:/videos/match01.mp4",
  "canonical_source": "c:/videos/match01.mp4",
  "duration_seconds": 743,
  "result_csv_path": "C:/output/match01/match01.csv",
  "output_folder": "C:/output/match01",
  "context": {
    "scan_region": {"x": 120, "y": 40, "width": 480, "height": 60},
    "context_patterns": [],
    "analysis_settings": {"ocr_sensitivity": 70, "matching_tolerance": 80}
  }
}
```
- Response 200:
```json
{
  "history_id": "vh_001",
  "merged": true,
  "potential_duplicate": false,
  "run_id": "run_20260425_002",
  "run_count": 4
}
```
- Behavior rules:
  - If `duration_seconds` is missing/malformed, server MUST create a new entry with `potential_duplicate=true` and `merged=false`.
- Errors:
  - 400 invalid payload/paths
  - 500 persistence failure

## Endpoint: `POST /api/history/reopen`
- Purpose: Restore persisted context and resolve review artifacts from output folder.
- Request body:
```json
{
  "history_id": "vh_001"
}
```
- Response 200:
```json
{
  "history_id": "vh_001",
  "analysis_context": {
    "scan_region": {"x": 120, "y": 40, "width": 480, "height": 60},
    "output_folder": "C:/output/match01",
    "context_patterns": [],
    "analysis_settings": {"ocr_sensitivity": 70, "matching_tolerance": 80}
  },
  "derived_results": {
    "resolution_status": "ready",
    "primary_csv_path": "C:/output/match01/match01.csv",
    "resolved_csv_paths": ["C:/output/match01/match01.csv"],
    "resolved_sidecar_paths": ["C:/output/match01/match01.review.json"],
    "resolution_messages": []
  },
  "review_route": "/review?history_id=vh_001"
}
```
- Response 200 (missing artifacts, non-blocking):
```json
{
  "history_id": "vh_001",
  "derived_results": {
    "resolution_status": "missing_results",
    "resolved_csv_paths": [],
    "resolution_messages": ["No CSV files found in output folder"]
  },
  "review_route": "/review?history_id=vh_001"
}
```
- Errors:
  - 404 unknown/deleted history entry
  - 500 restore failure

## Endpoint: `DELETE /api/history/videos/{history_id}`
- Purpose: Delete history entry from managed list.
- Response 200:
```json
{
  "history_id": "vh_001",
  "deleted": true
}
```
- Notes:
  - Deletion only removes managed history metadata.
  - Output folder files are not removed by this endpoint.

## Endpoint: `GET /api/history/videos/{history_id}`
- Purpose: Fetch one history entry with run metadata and duplicate flag.
- Response 200 includes:
  - identity fields
  - latest context summary
  - run list summary
  - delete status

## Invariants
- Duplicate prevention: visible history list must contain a single non-deleted entry per deterministic merge key.
- Reopen behavior: successful reopen always returns `review_route` and context payload.
- Missing result artifacts must not block metadata access.
