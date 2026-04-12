# Data Model: Sequential Frame Sampling Optimization

## Entity: FrameIterationRequest
- Purpose: Immutable request contract for frame iteration.
- Fields:
  - `url: str`
  - `start_time: float`
  - `end_time: float`
  - `fps: int`
  - `quality: str`
- Validation:
  - `fps >= 1`
  - `end_time >= start_time` (empty-range behavior preserved)
  - `quality` maps to known selector or defaults to `best`

## Entity: IterationRuntimeState
- Purpose: Internal state for active decode loop.
- Fields:
  - `native_fps: float`
  - `start_frame: int`
  - `end_frame: int`
  - `step: int`
  - `current_frame_index: int`
  - `sample_index: int`
- Invariants:
  - `step >= 1`
  - `current_frame_index` is monotonic non-decreasing
  - yielded frame indexes match baseline selection semantics

## Entity: SampledFrame
- Purpose: Output unit yielded to analysis pipeline.
- Fields:
  - `timestamp_sec: float`
  - `frame: object` (OpenCV frame buffer)
- Invariants:
  - `timestamp_sec == selected_frame_index / native_fps`
  - order is deterministic and stable across runs

## Entity: FallbackDecision
- Purpose: Records whether legacy seek path is activated.
- Fields:
  - `triggered: bool`
  - `reason: str` (`decode_error` | `performance_probe` | `none`)
  - `source_id: str`
- Rules:
  - fallback may activate only under guarded conditions from spec FR-012
  - fallback path must preserve timestamp/OCR parity (FR-013)

## Entity: IterationTelemetryEvent
- Purpose: Structured debug observability record.
- Fields:
  - `event_type: str` (`init`, `milestone`, `fallback`, `error`, `complete`)
  - `message: str`
  - `frame_index: int | None`
  - `timestamp_sec: float | None`
  - `reason: str | None`
- Rules:
  - emitted only when debug logging is enabled
  - must capture fallback reason category where applicable
