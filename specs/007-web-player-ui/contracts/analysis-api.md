# Contract: Analysis API (Web UI 007)

## Scope
Contracts between Web UI Analysis view and local Python server for launch, settings, region selection, and run control.

## Base
- Base URL: `http://127.0.0.1:<port>` (local only)
- Content type: `application/json`

## Endpoint: `GET /api/settings`
- Purpose: Load persisted user settings from existing `scytcheck_settings.json`.
- Response 200:
```json
{
  "theme": "dark",
  "video_quality": "best",
  "ocr_sensitivity": 70,
  "matching_tolerance": 80,
  "event_merge_gap_seconds": 2.0,
  "gating_enabled": true,
  "gating_threshold": 12,
  "filter_non_matching": false,
  "detailed_sidecar_log": false,
  "context_patterns": [
    {"id": "p1", "before_text": "Played by", "after_text": "Rank", "enabled": true}
  ],
  "scan_region": {"x": 120, "y": 40, "width": 480, "height": 60}
}
```

## Endpoint: `PUT /api/settings`
- Purpose: Persist settings updates.
- Request body:
```json
{
  "theme": "light",
  "ocr_sensitivity": 75,
  "scan_region": {"x": 90, "y": 50, "width": 520, "height": 65}
}
```
- Response 200: full merged settings payload.
- Errors:
  - 400 for invalid ranges/types.
  - 500 for persistence failure.

## Endpoint: `POST /api/analysis/preview-frame`
- Purpose: Capture and return representative frame for region selector.
- Request body:
```json
{
  "source_type": "youtube_url",
  "source_value": "https://youtube.com/watch?v=abc123"
}
```
- Response 200:
```json
{
  "frame_id": "f_001",
  "frame_width": 1920,
  "frame_height": 1080,
  "image_url": "/api/assets/frames/f_001.png"
}
```

## Endpoint: `POST /api/analysis/start`
- Purpose: Start analysis run from Analysis view.
- Request body (subset shown):
```json
{
  "source_type": "local_file",
  "source_value": "C:/videos/match01.mp4",
  "output_folder": "C:/output",
  "output_filename": "match01.csv",
  "scan_region": {"x": 120, "y": 40, "width": 480, "height": 60},
  "video_quality": "best",
  "ocr_sensitivity": 70,
  "matching_tolerance": 80,
  "event_merge_gap_seconds": 2.0,
  "gating_enabled": true,
  "gating_threshold": 12,
  "filter_non_matching": false,
  "detailed_sidecar_log": false,
  "context_patterns": []
}
```
- Response 202:
```json
{
  "run_id": "run_20260421_001",
  "status": "running"
}
```
- Errors:
  - 400 invalid input
  - 409 analysis already running

## Endpoint: `GET /api/analysis/progress/{run_id}`
- Purpose: Poll or stream progress state.
- Response 200:
```json
{
  "run_id": "run_20260421_001",
  "status": "running",
  "stage_label": "Extracting frames",
  "frames_processed": 312,
  "frames_estimated_total": 520
}
```

## Endpoint: `POST /api/analysis/stop/{run_id}`
- Purpose: Request graceful stop.
- Response 202:
```json
{
  "run_id": "run_20260421_001",
  "status": "stopping"
}
```

## Endpoint: `GET /api/analysis/result/{run_id}`
- Purpose: Resolve produced CSV and openable review session metadata.
- Response 200:
```json
{
  "run_id": "run_20260421_001",
  "status": "completed",
  "csv_path": "C:/output/match01.csv",
  "partial": false
}
```

## Compatibility Notes
- Local-only contract intended for desktop browser UI and packaged executable.
- No auth/session cookies required.
