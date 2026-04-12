# Feature Specification: Sequential Video Frame Decode Sampling Optimization

**Feature Branch**: `002-sequential-frame-sampling`  
**Created**: 2026-04-12  
**Status**: Draft  
**Input**: Video frame iteration optimization for performance

## Clarifications

### Session 2026-04-12

- Q: When `VideoCapture.read()` fails mid-stream (network hiccup, codec error), what should the function do? → A: Raise exception immediately (fail-fast); let caller handle retry or fallback
- Q: How should memory stability be measured and verified during 2-hour video iteration? → A: Peak resident memory via `psutil.Process().memory_info()` should stay flat (±10% variance)
- Q: Which video codecs and container formats must be explicitly tested? → A: H.264 (MP4) and VP9 (WebM)—covers Twitch and YouTube
- Q: How should sequential iteration be instrumented for verification? → A: Structured debug logging at key checkpoints, disabled by default
- Q: If sequential decoding underperforms or fails on specific sources, what fallback strategy should apply? → A: Auto-fallback to legacy seek-based path when sequential decode fails or startup probe indicates severe underperformance

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Analyze Multi-Hour Game Sessions Without Prohibitive Seeking Overhead (Priority: P1)

A user is analyzing a 2–4 hour recorded League of Legends/Valorant/CS2 game stream to extract player names and match statistics from overlay regions (scoreboard, killfeed, player list). The current frame-by-frame seeking approach causes cumulative delays that grow with video length—a 2-hour video at 1 fps sampling (7,200 frames) creates 7,200+ seek operations, making the full analysis take 45+ minutes. Sequential decoding would reduce this to ~3–5 minutes.

**Why this priority**: This is the core differentiator. Game session analysis on long content (30 min to 4+ hours) is the actual user workload. Performance directly determines whether users can analyze vods in a reasonable time or abandon the tool. Network streams (Twitch VODs, YouTube) are especially impacted by seeking cost on remote sources.

**Independent Test**: Run full OCR analysis on a 1-hour test game video with both implementations (old random-seek vs. new sequential), measure elapsed time, and compare detected player names. Results must be identical.

**Acceptance Scenarios**:

1. **Given** a 1-hour game session video (180,000 frames @ 30fps), **When** analyzing with sample rate fps=1, **Then** frame iteration completes in under 10 seconds and yields 3,600 frames at exact timestamps, vs. current ~20+ seconds with repeated seeks
2. **Given** a Twitch VOD source (network stream with high seek latency), **When** iterating frames fps=1, **Then** sequential pull completes without repeated seek stalls and maintains exact timestamp accuracy throughout
3. **Given** a 2-hour video with 24 fps native and sample fps=1, **When** yielding frames, **Then** the extracted player names (aggregated by timestamp) are identical to the current random-seek implementation

---

### User Story 2 - Maintain Exact Timestamp Fidelity for Player Name Correlation (Priority: P1)

Game session analysis depends on exact frame timestamps to correlate player names with in-game events (kills, objectives, joins). A 1-frame timestamp error on a 2-hour video could misattribute text to the wrong event. The optimization must preserve timestamp accuracy to ±0 milliseconds so that all downstream player name aggregation and event correlation continues to work without recalibration or data loss.

**Why this priority**: Loss of timestamp precision would require revalidation of all detection logic and could introduce subtle bugs in player appearance tracking (e.g., same name marked as two different players if timestamps drift). This is a hard correctness constraint that affects data integrity.

**Independent Test**: Compare frame-by-frame timestamps from both implementations on a synthetic 10-frame test dataset. Timestamps must match to the microsecond across all fps and duration parameters.

**Acceptance Scenarios**:

1. **Given** a 10-frame test video with 10 fps native rate and sample fps=1, **When** iterating frames, **Then** every yielded frame_time_sec matches the current implementation exactly (0 ms variance)
2. **Given** a 1-hour video with 30 fps native, **When** sampling fps=1 and collecting all frame timestamps, **Then** the 3,600 timestamps are spaced exactly 1.0 second apart with no drift or rounding accumulation
3. **Given** the same start_time, end_time, fps parameters run in sequence, **When** comparing frame timestamps, **Then** results are bit-identical across runs (deterministic)

---

### User Story 3 - Preserve System Integration and Backward Compatibility (Priority: P1)

The optimization must work transparently within the existing codebase without requiring changes to callers, test mocks, or interface signatures. All integration tests, unit tests, and downstream code that uses `iterate_frames_with_timestamps()` must continue to work without modification.

**Why this priority**: Backward compatibility ensures zero refactoring burden on the rest of the codebase and makes the change a drop-in improvement with no adoption friction.

**Independent Test**: Can be tested by running the complete existing test suite (`tests/unit/test_video_service.py`, `tests/integration/`) without any code changes outside `video_service.py`. All tests must pass.

**Acceptance Scenarios**:

1. **Given** the existing `test_video_service.py` unit test suite, **When** running with the optimized implementation, **Then** all tests pass without modification
2. **Given** the existing integration test `test_us1_workflow.py`, **When** running the full video analysis workflow, **Then** the test passes with identical OCR detection results
3. **Given** any caller of `iterate_frames_with_timestamps()`, **When** calling with the same parameters, **Then** the function signature remains unchanged and yields are compatible with existing code

---

### Edge Cases

- **Very long videos (2+ hours)**: At 30 fps native and 1 fps sample rate, a 2-hour video yields 7,200 frames. System MUST iterate all frames without memory accumulation, decode stalls, or stream timeouts. Previous random-seek approach caused multiple timeouts on network streams; sequential pull should improve stability.
- **Empty range**: start_time >= end_time → System MUST return empty iterator (0 frames), matching current behavior
- **Single frame in range**: start_time and end_time span exactly one frame → System MUST yield exactly one frame with correct timestamp
- **Stream connectivity issues during long decode**: Long sequential decode may encounter temporary network hiccups on Twitch/YouTube VODs. System MUST raise exception immediately on `read()` failure (fail-fast); caller is responsible for retry/fallback logic. This preserves backward compatibility with current error handling behavior.
- **Native fps detection failure**: get_frame_rate() returns 0, None, or invalid → System MUST fall back to 30 fps default, matching current behavior
- **Quality parameter variations**: Different quality settings ("best", "360p", "480p", "720p") MUST NOT affect frame timestamp calculation; only decoding strategy changes. Timestamp sequence must be identical regardless of quality
- **Negative or out-of-bounds timestamps**: Negative start_time or end_time > video duration → System MUST clamp or handle per current implementation behavior, with no timestamp distortion

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST decode and yield video frames in exact order at exact timestamps as the current implementation; player name extraction results aggregated by timestamp MUST be identical
- **FR-002**: System MUST maintain sample rate fidelity: given fps parameter, yield frames at intervals of `native_fps / fps` frames, matching current step calculation to ±0 ms
- **FR-003**: System MUST iterate video frames sequentially without seeking to random frame positions after the initial start_time seek; this is the key performance optimization for long videos
- **FR-004**: System MUST yield same frame count (within ±1 frame) as current implementation for all input ranges and fps values; frame count MUST NOT vary based on video length or quality
- **FR-005**: System MUST preserve all frame data integrity: no frame skipping due to decoder errors, no quality degradation. For multi-hour videos, cumulative bit-fidelity MUST be maintained throughout the entire stream
- **FR-006**: System MUST maintain interface compatibility: function signature, parameters, return types, exception behavior MUST remain unchanged for all callers
- **FR-007**: System MUST support long-running analysis on multi-hour videos without memory accumulation, connection timeouts, or intermediate state corruption
- **FR-008**: System MUST preserve `_stream_cache` behavior for repeated analysis of the same url/quality combination on long videos (avoid re-downloading/seeking from remote source)
- **FR-009**: System MUST handle all edge cases (empty range, single frame, invalid fps, stream errors) identically to current implementation, with special attention to network stream stability on long VODs
- **FR-010**: System MUST maintain identical frame iteration and timestamp accuracy across H.264 (MP4) and VP9 (WebM) containers
- **FR-011**: System MUST emit structured debug logs for seek initialization, sampling loop progress checkpoints, and read failures; logs MUST be disabled by default and enabled only through existing logging configuration
- **FR-012**: System MUST include an internal guarded fallback to the legacy seek-based iteration path that activates only when sequential decoding fails or a startup probe detects severe underperformance
- **FR-013**: When fallback is activated, system MUST preserve timestamp fidelity and OCR output parity with baseline behavior, and emit a debug log event indicating fallback trigger reason

### Key Entities *(include if feature involves data)*

- **Video Frame**: A decoded image buffer (numpy array or cv2 Mat) at a specific frame index, with associated timestamp in seconds
- **Frame Timestamp**: Calculated as frame_index / native_fps; must be identical between implementations
- **Sample Rate**: Derived from fps parameter; controls which frames are yielded (every N frames where N = native_fps / fps)
- **Stream**: OpenCV VideoCapture object representing a video file or stream; maintains internal position state

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Frame iteration time for a 1-hour 30fps video with fps=1 sampling MUST be reduced by at least 50% (target: <10 seconds, current: ~20+ seconds with random seeks)
- **SC-002**: Frame iteration time for a 2-hour 30fps video with fps=1 MUST scale sub-linearly (target: <20 seconds, showing stability up to multi-hour lengths)
- **SC-003**: Frame timestamp accuracy MUST match current implementation exactly (0 ms deviation) for 100% of yielded frames across all test videos, fps parameters, and duration ranges (10 seconds to 4 hours)
- **SC-004**: No seek operations inside the sample loop: profiling MUST confirm sequential frame read pattern (only one `VideoCapture.set()` call at initialization, then continuous `read()` calls)
- **SC-005**: All existing unit tests in `tests/unit/test_video_service.py` MUST pass without modification
- **SC-006**: Integration test `test_us1_workflow.py` on a 30-minute game session video MUST yield identical OCR player name detections (same text regions, same confidence scores, same aggregated counts) with both implementations
- **SC-007**: Frame count variance MUST be within ±1 frame for all input combinations; multi-hour videos MUST NOT show cumulative frame drift
- **SC-008**: Performance test `test_sc001_analysis_of_ten_minute_video_completes_within_target` MUST pass with optimized implementation
- **SC-009**: Network stream handling (Twitch/YouTube VODs) MUST not introduce stream re-seeks or timeout failures for long videos when using sequential iteration
- **SC-010**: Memory usage during 2-hour video iteration MUST remain stable (no linear accumulation with video length): peak resident memory measured via `psutil.Process().memory_info().rss` at 0%, 50%, and 100% iteration progress MUST vary by ≤±10% across these checkpoints
- **SC-011**: Implementation MUST be validated with H.264 (MP4) and VP9 (WebM) videos; frame count, timestamps, and OCR detection results MUST remain identical across both containers
- **SC-012**: With debug logging enabled, logs MUST show exactly one initial seek setup and no repeated random seek operations inside the sampling loop
- **SC-013**: On sources where sequential decode fails or startup probe flags severe underperformance, fallback path MUST complete analysis successfully and produce identical frame timestamps and OCR detections to baseline
- **SC-014**: With debug logging enabled, fallback activation MUST be observable via structured log records including trigger category (`decode_error` or `performance_probe`) and source identifier

## Assumptions

- Game session videos range from 15 minutes to 4+ hours; performance must scale efficiently across this range without degradation or stream failures
- Current sequential-seek implementation (seeking to each sampled frame) is ground truth for timestamp calculation and frame selection behavior
- OpenCV VideoCapture.read() in sequential order is faster than random seeking for typical file-based and network-streamed videos; this is particularly true for:
  - Network streams (Twitch VODs, YouTube), where seeking incurs network round-trip latency
  - Large video files where seek operations require disk I/O or codec buffer resets
  - Long GOP (Group of Pictures) structures common in game stream codecs (H.264, VP9)
- Network stream sources (YouTube, Twitch VODs) may experience temporary connectivity issues; sequential iteration must be more resilient than random seeking due to fewer seek operations
- Existing tests are complete and correct; all tests passing is sufficient verification of correctness for long videos
- The `quality` parameter ("best", "360p", "480p", "720p") only affects frame reading resolution/quality, not timestamp sequence; timestamp behavior must remain identical regardless of quality
- Frame count variance of ±1 frame is acceptable due to rounding inherent in fps/step calculations; variance MUST NOT increase with video length
- Player name extraction uses frame timestamps as correlation keys; timestamp drift or accumulation errors could cause missed or misattributed detections
- A startup probe can determine severe underperformance early enough to switch paths without materially increasing total runtime
