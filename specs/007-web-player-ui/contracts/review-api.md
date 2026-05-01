# Contract: Review API (Web UI 007)

## Scope
Contracts between Review view and local Python server for session loading, candidate/group operations, undo, and exports.

## Endpoint: `POST /api/review/sessions/load`
- Purpose: Load CSV into review session after schema/version validation.
- Request body:
```json
{
  "csv_path": "C:/output/match01.csv"
}
```
- Response 200:
```json
{
  "session_id": "sess_match01",
  "csv_path": "C:/output/match01.csv",
  "schema_version": "1.0",
  "source_type": "youtube_url",
  "source_value": "https://youtube.com/watch?v=abc123"
}
```
- Errors:
  - 422 invalid schema or unsupported version

## Endpoint: `GET /api/review/sessions`
- Purpose: List loadable/recent sessions for picker.
- Response 200:
```json
{
  "sessions": [
    {
      "session_id": "sess_match01",
      "display_name": "match01.csv",
      "csv_path": "C:/output/match01.csv",
      "updated_at": "2026-04-21T11:04:00Z"
    }
  ]
}
```

## Endpoint: `GET /api/review/sessions/{session_id}`
- Purpose: Retrieve full session snapshot.
- Response 200 includes:
  - thresholds
  - ordered groups
  - candidate rows
  - review counts
  - recommendation metadata

## Endpoint: `PATCH /api/review/sessions/{session_id}/thresholds`
- Purpose: Update grouping/recommendation thresholds.
- Request:
```json
{
  "similarity_threshold": 85,
  "recommendation_threshold": 72
}
```
- Response 200: updated session snapshot with recomputed grouping/recommendations.

## Endpoint: `POST /api/review/sessions/{session_id}/actions`
- Purpose: Apply mutating review action and persist sidecar immediately.
- Request examples:
```json
{"action_type":"confirm","target_ids":["cand_1"]}
```
```json
{"action_type":"reject","target_ids":["cand_7","cand_8"]}
```
```json
{"action_type":"edit","target_ids":["cand_3"],"payload":{"corrected_text":"PlayerAlpha"}}
```
```json
{"action_type":"remove","target_ids":["cand_10"]}
```
```json
{"action_type":"move_candidate","target_ids":["cand_12"],"payload":{"to_group_id":"grp_2"}}
```
```json
{"action_type":"merge_groups","target_ids":["grp_3","grp_4"]}
```
```json
{"action_type":"reorder_group","target_ids":["grp_2"],"payload":{"to_index":0}}
```
- Response 200:
```json
{
  "session_id": "sess_match01",
  "action_id": "act_111",
  "persisted": true,
  "updated_at": "2026-04-21T11:05:30Z"
}
```
- Errors:
  - 400 invalid action payload
  - 409 conflicting mutation

## Endpoint: `POST /api/review/sessions/{session_id}/undo`
- Purpose: Undo latest mutating action.
- Response 200:
```json
{
  "session_id": "sess_match01",
  "undone_action_id": "act_111",
  "remaining_undo_count": 12
}
```

## Endpoint: `GET /api/review/sessions/{session_id}/thumbnails/{candidate_id}`
- Purpose: Resolve thumbnail URL or trigger local fallback extraction/cache.
- Response 200:
```json
{
  "candidate_id": "cand_1",
  "thumbnail_url": "/api/assets/thumbs/cand_1.png"
}
```

## Endpoint: `POST /api/review/sessions/{session_id}/export`
- Purpose: Export deduplicated names CSV and occurrences CSV.
- Response 200:
```json
{
  "session_id": "sess_match01",
  "deduplicated_names_csv_path": "C:/output/match01.names.csv",
  "occurrences_csv_path": "C:/output/match01.occurrences.csv",
  "confirmed_count": 42,
  "deduplicated_count": 16
}
```

## Sidecar Persistence Invariant
- Every successful mutating action must write sidecar JSON before returning success.
- Sidecar filename convention: `<result>.review.json` adjacent to source CSV.
