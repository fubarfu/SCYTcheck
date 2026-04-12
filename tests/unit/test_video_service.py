import numpy as np
from unittest.mock import patch

from src.services.video_service import VideoAccessError, VideoService


class _FakeCapture:
    def __init__(
        self,
        total_frames: int = 240,
        fps: float = 30.0,
        fail_at: int | None = None,
        fail_once: bool = False,
    ) -> None:
        self.total_frames = total_frames
        self.fps = fps
        self.fail_at = fail_at
        self.fail_once = fail_once
        self._failed_once = False
        self.current = 0
        self.set_calls: list[tuple[int, int]] = []
        self.released = False
        self.pos_msec = 0.0

    def isOpened(self) -> bool:
        return True

    def get(self, prop: int) -> float:
        if prop == 0:  # cv2.CAP_PROP_POS_MSEC
            return self.pos_msec
        if prop == 5:  # cv2.CAP_PROP_FPS
            return self.fps
        if prop == 7:  # cv2.CAP_PROP_FRAME_COUNT
            return float(self.total_frames)
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        self.set_calls.append((prop, int(value)))
        if prop == 1:  # cv2.CAP_PROP_POS_FRAMES
            self.current = int(value)
        return True

    def read(self):
        if (
            self.fail_at is not None
            and self.current >= self.fail_at
            and (not self.fail_once or not self._failed_once)
        ):
            self._failed_once = True
            return False, None
        if self.current >= self.total_frames:
            return False, None
        self.pos_msec = (self.current * 1000.0) / max(1e-6, self.fps)
        frame = np.zeros((4, 4, 3), dtype=np.uint8)
        self.current += 1
        return True, frame

    def release(self) -> None:
        self.released = True


def test_validate_youtube_url_rejects_invalid_format() -> None:
    service = VideoService()

    is_valid, error = service.validate_youtube_url("https://example.com/video")

    assert not is_valid
    assert "valid YouTube" in error


def test_build_ydl_opts_enables_node_runtime_when_available() -> None:
    service = VideoService()

    with patch("src.services.video_service.shutil.which") as which_mock:
        which_mock.side_effect = lambda name: {
            "node": r"C:\Program Files\nodejs\node.exe",
            "deno": None,
            "quickjs": None,
            "bun": None,
        }.get(name)
        opts = service._build_ydl_opts()

    runtimes = opts["js_runtimes"]
    assert isinstance(runtimes, dict)
    assert "node" in runtimes
    assert runtimes["node"] == {"path": r"C:\Program Files\nodejs\node.exe"}
    assert "deno" in runtimes


def test_validate_youtube_url_accepts_accessible_video() -> None:
    service = VideoService()

    with patch.object(service, "_extract_media_url", return_value=("stream", {"id": "abc"})):
        is_valid, error = service.validate_youtube_url("https://youtube.com/watch?v=abc")

    assert is_valid
    assert error == ""


def test_validate_youtube_url_handles_unreachable_video() -> None:
    service = VideoService()

    with patch.object(service, "_extract_media_url", side_effect=RuntimeError("network issue")):
        is_valid, error = service.validate_youtube_url("https://youtu.be/abc")

    assert not is_valid
    assert "could not be accessed" in error


def test_build_ydl_opts_selects_format_based_on_quality() -> None:
    opts_best = VideoService._build_ydl_opts("best")
    assert "height" not in opts_best["format"]

    opts_720 = VideoService._build_ydl_opts("720p")
    assert "720" in opts_720["format"]
    assert "height<=720" in opts_720["format"]

    opts_480 = VideoService._build_ydl_opts("480p")
    assert "height<=480" in opts_480["format"]

    opts_unknown = VideoService._build_ydl_opts("9999p")
    assert opts_unknown["format"] == opts_best["format"]


def test_compute_sampling_parameters_preserves_baseline_math() -> None:
    start_frame, end_frame, step = VideoService._compute_sampling_parameters(
        start_time=10.0,
        end_time=12.0,
        fps=2,
        native_fps=30.0,
    )

    assert start_frame == 300
    assert end_frame == 360
    assert step == 15


def test_build_target_frame_indexes_handles_empty_and_single_ranges() -> None:
    assert VideoService._build_target_frame_indexes(10, 5, 3) == []
    assert VideoService._build_target_frame_indexes(10, 10, 3) == [10]


def test_iterate_frames_with_timestamps_uses_sequential_read_without_per_sample_seek() -> None:
    service = VideoService()
    fake_cap = _FakeCapture(total_frames=300, fps=30.0)

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=fake_cap),
    ):
        frames = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=abc",
                start_time=1.0,
                end_time=2.0,
                fps=2,
            )
        )

    assert len(frames) == 3
    pos_frame_sets = [call for call in fake_cap.set_calls if call[0] == 1]
    # Exactly one seek to start frame, then pure sequential reads.
    assert len(pos_frame_sets) == 1
    assert pos_frame_sets[0][1] == 30
    assert fake_cap.released is True


def test_iterate_frames_with_timestamps_falls_back_on_decode_error() -> None:
    service = VideoService()
    fake_cap = _FakeCapture(total_frames=100, fps=10.0, fail_at=10, fail_once=True)

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=fake_cap),
    ):
        result = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=abc",
                start_time=1.0,
                end_time=3.0,
                fps=1,
            )
        )

    assert result
    pos_frame_sets = [call for call in fake_cap.set_calls if call[0] == 1]
    # One init seek + legacy fallback random seeks.
    assert len(pos_frame_sets) >= 2


def test_iterate_frames_with_timestamps_handles_unreadable_stream_without_crashing() -> None:
    service = VideoService()
    fake_cap = _FakeCapture(total_frames=5, fps=30.0, fail_at=0)

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=fake_cap),
    ):
        items = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=abc",
                start_time=0.0,
                end_time=1.0,
                fps=1,
            )
        )

    assert items == []


def test_should_fallback_accepts_supported_reasons_only() -> None:
    service = VideoService()
    assert service._should_fallback("decode_error", "id") is True
    assert service._should_fallback("performance_probe", "id") is True
    assert service._should_fallback("none", "id") is False


def test_startup_performance_probe_does_not_trigger_for_typical_sequence() -> None:
    service = VideoService()
    fake_cap = _FakeCapture(total_frames=500, fps=30.0)
    indexes = list(range(100, 140))
    assert service._run_startup_performance_probe(fake_cap, indexes) is False


def test_iterator_contract_signature_is_unchanged() -> None:
    service = VideoService()
    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=_FakeCapture()),
    ):
        output = service.iterate_frames_with_timestamps(
            "https://youtube.com/watch?v=abc", 0.0, 1.0, 1, quality="best"
        )
        first = next(iter(output))

    assert isinstance(first, tuple)
    assert len(first) == 2


def test_iterate_frames_with_timestamps_recovers_with_fallback_after_midstream_decode_error() -> None:
    service = VideoService()
    fake_cap = _FakeCapture(total_frames=120, fps=10.0, fail_at=40, fail_once=True)

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=fake_cap),
    ):
        samples = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=abc",
                start_time=2.0,
                end_time=10.0,
                fps=1,
            )
        )

    # Expected sampled indexes: 20,30,40,50,60,70,80,90,100
    assert len(samples) == 9
    assert samples[-1][0] == 10.0


def test_iterate_frames_with_timestamps_gracefully_finishes_when_tail_is_unreadable() -> None:
    service = VideoService()

    first_cap = _FakeCapture(total_frames=120, fps=10.0, fail_at=40, fail_once=True)
    recovery_cap = _FakeCapture(total_frames=120, fps=10.0, fail_at=40, fail_once=False)

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch(
            "src.services.video_service.cv2.VideoCapture",
            side_effect=[first_cap, recovery_cap],
        ),
    ):
        samples = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=abc",
                start_time=2.0,
                end_time=10.0,
                fps=1,
            )
        )

    # We still get frames up to the last readable sample and do not raise.
    assert samples
    assert samples[-1][0] == 3.0


def test_us2_timestamp_parity_matches_baseline_frame_selector() -> None:
    start_frame, end_frame, step = VideoService._compute_sampling_parameters(
        start_time=0.0,
        end_time=3.0,
        fps=2,
        native_fps=30.0,
    )
    baseline_indexes = list(range(start_frame, end_frame + 1, step))
    shared_indexes = VideoService._build_target_frame_indexes(start_frame, end_frame, step)
    baseline_timestamps = [idx / 30.0 for idx in baseline_indexes]
    shared_timestamps = [idx / 30.0 for idx in shared_indexes]
    assert shared_timestamps == baseline_timestamps


def test_us2_frame_count_parity_tolerance_within_one_frame() -> None:
    start_frame, end_frame, step = VideoService._compute_sampling_parameters(
        start_time=5.0,
        end_time=14.9,
        fps=3,
        native_fps=29.97,
    )
    baseline_count = len(list(range(start_frame, end_frame + 1, step)))
    candidate_count = len(VideoService._build_target_frame_indexes(start_frame, end_frame, step))
    assert abs(baseline_count - candidate_count) <= 1


def test_us2_deterministic_timestamp_fixture_across_repeated_calls() -> None:
    args = dict(start_time=2.0, end_time=10.0, fps=1, native_fps=24.0)
    first = VideoService._compute_sampling_parameters(**args)
    second = VideoService._compute_sampling_parameters(**args)
    assert first == second
    a = VideoService._build_target_frame_indexes(*first)
    b = VideoService._build_target_frame_indexes(*second)
    assert a == b


def test_us3_stream_cache_key_includes_quality_to_preserve_behavior() -> None:
    service = VideoService()

    with patch("src.services.video_service.YoutubeDL") as ydl_cls:
        ydl = ydl_cls.return_value.__enter__.return_value
        ydl.extract_info.side_effect = [
            {"url": "stream-best"},
            {"url": "stream-720"},
        ]
        stream_best, _ = service._extract_media_url("https://youtube.com/watch?v=abc", quality="best")
        stream_720, _ = service._extract_media_url("https://youtube.com/watch?v=abc", quality="720p")

    assert stream_best == "stream-best"
    assert stream_720 == "stream-720"
    assert "https://youtube.com/watch?v=abc|best" in service._stream_cache
    assert "https://youtube.com/watch?v=abc|720p" in service._stream_cache


def test_resolve_timestamp_prefers_capture_msec_when_available() -> None:
    service = VideoService()
    fake_cap = _FakeCapture(total_frames=120, fps=10.0)

    with (
        patch.object(service, "_extract_media_url", return_value=("stream", {})),
        patch("src.services.video_service.cv2.VideoCapture", return_value=fake_cap),
    ):
        samples = list(
            service.iterate_frames_with_timestamps(
                "https://youtube.com/watch?v=abc",
                start_time=2.0,
                end_time=2.0,
                fps=1,
            )
        )

    assert samples
    timestamp, _frame = samples[0]
    assert timestamp == 2.0
