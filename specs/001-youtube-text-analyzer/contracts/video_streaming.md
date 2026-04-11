# Contract: Video Streaming Service

**Purpose**: Interface for accessing YouTube video frames for analysis.

**Methods**:
- `get_video_info(url: str) -> dict`: Returns video metadata (duration, resolution)
- `get_frame_at_time(url: str, time_seconds: float) -> np.ndarray`: Returns frame image at specific time
- `get_frames_in_range(url: str, start_time: float, end_time: float, fps: int) -> Iterator[np.ndarray]`: Yields frames in time range

**Exceptions**:
- `VideoAccessError`: When video cannot be accessed
- `InvalidURLError`: When URL is invalid

**Dependencies**: yt-dlp, opencv-python