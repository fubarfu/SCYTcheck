# Research: Sequential Video Frame Decode Sampling Optimization

## Decision 1: Use Sequential Decode With Sample Filtering As Primary Strategy
- Decision: Replace repeated random seeks (`CAP_PROP_POS_FRAMES` per sample) with one initial seek plus sequential `read()` progression, yielding only frames aligned to sampling step.
- Rationale: Random seek cost dominates long videos and network sources; sequential decode avoids repeated decoder repositioning and GOP re-entry overhead.
- Alternatives considered:
  - Keep random seek strategy and tune seek intervals: rejected due to still-high seek overhead.
  - Pre-extract all sampled frames to memory/disk: rejected for memory/storage pressure and added complexity.

## Decision 2: Preserve Timestamp Semantics Exactly
- Decision: Keep timestamp computation semantics aligned to frame index / native fps and preserve frame ordering/count behavior (within existing +-1 variance tolerance).
- Rationale: Downstream OCR aggregation and player correlation depend on deterministic timing.
- Alternatives considered:
  - Time-based wall-clock sampling: rejected due to drift and non-determinism.
  - Decoder-reported timestamp-only sampling: rejected due to container-dependent inconsistencies.

## Decision 3: Guarded Fallback To Legacy Seek Path
- Decision: Add guarded fallback to current seek-based iteration only when sequential decode fails or startup probe detects severe underperformance.
- Rationale: Maintains resilience for edge codecs/streams while preserving optimized default path.
- Alternatives considered:
  - No fallback (fail-fast only): rejected due to avoidable user-facing failures on problematic sources.
  - Always dual-path probing: rejected due to unnecessary runtime cost.

## Decision 4: Keep Fail-Fast Behavior On Mid-Stream Read Errors
- Decision: On read failures in active path, raise promptly (with fallback trigger where policy applies) rather than silently skipping frames.
- Rationale: Frame dropping can corrupt OCR continuity and timestamp-linked results.
- Alternatives considered:
  - Skip unreadable frames: rejected due to data quality degradation.
  - Retry loops on every failure: rejected for complexity and potential long stalls.

## Decision 5: Scope Validation To Real Workload Codecs
- Decision: Explicitly validate behavior on H.264/MP4 and VP9/WebM.
- Rationale: Matches dominant Twitch/YouTube game-session source formats.
- Alternatives considered:
  - Exhaustive codec matrix: rejected for disproportionate maintenance burden.
  - Mock-only validation: rejected because decode behavior is codec/container dependent.

## Decision 6: Add Lightweight Debug Observability
- Decision: Emit structured debug logs for initialization, sampling milestones, fallback events, and failures; logging remains disabled by default.
- Rationale: Enables verification of no-seek-loop behavior and fallback causality without changing public APIs.
- Alternatives considered:
  - No logs: rejected due to poor diagnosability of performance regressions.
  - Always-on metrics: rejected to avoid noise and overhead.

## Decision 7: Memory Stability Validation Method
- Decision: Validate RSS stability checkpoints at 0%, 50%, and 100% during 2-hour iteration with acceptable +-10% variance.
- Rationale: Practical, repeatable indicator for leaked frame accumulation in long runs.
- Alternatives considered:
  - Heap-only metrics: rejected because native buffers may dominate memory usage.
  - End-only measurement: rejected due to missed transient growth patterns.
