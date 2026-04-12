# Contract: Video Iteration Service Behavior

## Scope
Defines behavioral contract for `VideoService.iterate_frames_with_timestamps(url, start_time, end_time, fps, quality="best")` for sequential-sampling optimization.

## Public Interface Contract
- Signature remains unchanged.
- Return type remains iterator of `(timestamp_sec, frame)` tuples.
- Input semantics remain unchanged.

## Behavioral Guarantees
1. Deterministic ordering
- Frames are yielded in increasing timeline order.

2. Timestamp fidelity
- For each yielded sample, `timestamp_sec` matches baseline semantics (`selected_frame_index / native_fps`).
- No drift accumulation across long duration runs.

3. Sampling fidelity
- Sample density follows baseline step derivation from `fps` and `native_fps`.
- Total yielded frame count remains baseline-compatible within existing +-1 tolerance.

4. Error handling
- Mid-stream decode read failures follow fail-fast behavior unless guarded fallback policy is engaged.
- No silent frame drops.

5. Guarded fallback
- Legacy seek-based path may be activated only for:
  - decode failure in sequential path
  - severe underperformance determined by startup probe
- Fallback must preserve output parity expectations.

6. Observability
- With debug logging enabled, service emits structured events for:
  - initialization
  - sampling milestones
  - fallback trigger and reason
  - terminal errors
  - completion summary

## Non-Functional Contract
- Performance target: >=50% iteration speedup for 1-hour videos at fps=1 versus baseline random-seek.
- Memory target: RSS stability within +-10% between 0% / 50% / 100% checkpoints for 2-hour iteration.
- Validation scope: H.264/MP4 and VP9/WebM.

## Compatibility Contract
- Existing callers (`AnalysisService`) require no changes.
- Existing tests remain valid, with additive assertions allowed for new observability/fallback behavior.
