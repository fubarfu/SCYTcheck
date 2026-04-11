# Contract: Video Streaming Service

**Purpose**: Interface for validating and accessing on-demand YouTube video frames for analysis.

**Methods**:
- `validate_youtube_url(url: str) -> tuple[bool, str]`
	- Performs format validation and accessibility preflight check.
- `get_video_info(url: str) -> dict`: Returns video metadata (duration, resolution)
- `get_frame_at_time(url: str, time_seconds: float, quality: str = "best") -> np.ndarray`: Returns frame image at specific time
- `get_frames_in_range(url: str, start_time: float, end_time: float, fps: int, quality: str = "best") -> Iterator[np.ndarray]`: Yields frames in time range
- `iter_frames_with_timestamps(url: str, start_time: float, end_time: float, fps: int) -> Iterator[tuple[float, np.ndarray]]`
	- Yields `(frame_time_sec, frame)` tuples to support event merging and first/last seen tracking.
- `open_region_selector(url: str, initial_time_sec: float, quality: str = "best") -> tuple[list[tuple[int, int, int, int]], bool]`
	- Opens region-selection popup in foreground and returns selected regions plus a confirmation flag.

**Exceptions**:
- `VideoAccessError`: When video cannot be accessed
- `InvalidURLError`: When URL is invalid

**Dependencies**: yt-dlp, opencv-python

**Behavioral Guarantees**:
- Time seeks are best-effort and monotonic for increasing requests.
- Returned timestamps are within a practical decode tolerance of requested times.
- Service supports on-demand frame retrieval without full video download.
- Requested quality is respected for retrieval attempts in the current run; if unavailable for a video, retrieval falls through to the next lower available quality and reports requested vs actual quality used.
- Validation method distinguishes malformed URL and unreachable/private video conditions.
- Region-selection popup is raised to foreground when launched.
- Selector instructions are shown in a dedicated area below the video preview and do not overlay video content.