"""
Unit tests for RegionSelector component - frame navigation and time-based seeking.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import cv2
import numpy as np
import pytest

from src.components.region_selector import RegionSelector
from src.services.video_service import VideoService


@pytest.fixture
def mock_video_service() -> Mock:
    """Create a mock VideoService for testing."""
    service = Mock(spec=VideoService)

    # Mock video info
    service.get_video_info.return_value = {
        "title": "Test Video",
        "duration": 600.0,  # 10 minutes
        "width": 1280,
        "height": 720,
    }

    # Mock frame at time
    def get_frame_at_time_mock(url: str, time_seconds: float, quality: str = "best") -> np.ndarray:
        # Return a mock frame (all black)
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        return frame

    service.get_frame_at_time.side_effect = get_frame_at_time_mock

    return service


@pytest.fixture
def region_selector(mock_video_service: Mock) -> RegionSelector:
    """Create a RegionSelector instance with mocked VideoService."""
    return RegionSelector(mock_video_service)


class TestRegionSelectorSeeking:
    """Test time-based seeking and frame navigation."""

    def test_get_frame_at_time(self, region_selector: RegionSelector) -> None:
        """Test retrieving a frame at a specific time."""
        frame = region_selector.get_frame_at_time("https://youtube.com/watch?v=test", 5.0)
        assert frame is not None
        assert frame.shape == (720, 1280, 3)

    def test_get_frame_at_time_zero(self, region_selector: RegionSelector) -> None:
        """Test retrieving first frame (time=0)."""
        frame = region_selector.get_frame_at_time("https://youtube.com/watch?v=test", 0.0)
        assert frame is not None
        assert frame.shape == (720, 1280, 3)

    def test_get_video_duration(self, region_selector: RegionSelector) -> None:
        """Test retrieving video duration."""
        duration = region_selector.get_video_duration(
            "https://youtube.com/watch?v=test",
            quality="720p",
        )
        assert duration == 600.0  # 10 minutes
        region_selector.video_service.get_video_info.assert_called_with(
            "https://youtube.com/watch?v=test",
            quality="720p",
        )

    def test_frame_time_mapping(self, region_selector: RegionSelector) -> None:
        """Test mapping between scrollbar position and frame time."""
        # For a 600-second video with scrollbar range 0-100
        # scrollbar_pos=0 -> frame_time=0
        # scrollbar_pos=100 -> frame_time=600
        # scrollbar_pos=50 -> frame_time=300

        duration = region_selector.get_video_duration("https://youtube.com/watch?v=test")

        # Test mapping function
        def scrollbar_to_time(scrollbar_value: int, duration: float) -> float:
            """Convert scrollbar position (0-100) to frame time (0-duration)."""
            return (scrollbar_value / 100.0) * duration

        assert scrollbar_to_time(0, duration) == 0.0
        assert scrollbar_to_time(50, duration) == 300.0
        assert scrollbar_to_time(100, duration) == 600.0

    def test_multiple_sequential_seeks(self, region_selector: RegionSelector) -> None:
        """Test seeking to multiple frames in sequence."""
        frames = []
        times = [0.0, 5.0, 10.0, 15.0, 20.0]

        for time in times:
            frame = region_selector.get_frame_at_time("https://youtube.com/watch?v=test", time)
            frames.append(frame)

        # All frames should have same shape
        for frame in frames:
            assert frame.shape == (720, 1280, 3)

        # Verify seek was called for each time
        assert region_selector.video_service.get_frame_at_time.call_count == len(times)


class TestRegionSelectorRegionTracking:
    """Test region selection and frame_time tracking."""

    def test_selected_regions_initialization(self, region_selector: RegionSelector) -> None:
        """Test that selected regions list is initialized."""
        assert region_selector.selected_regions == []

    def test_current_frame_time_tracking(self, region_selector: RegionSelector) -> None:
        """Test tracking current frame time."""
        region_selector.current_frame_time = 5.5
        assert region_selector.current_frame_time == 5.5

    def test_frame_boundaries(self, region_selector: RegionSelector) -> None:
        """Test seeking to frame boundaries (start and end)."""
        url = "https://youtube.com/watch?v=test"

        # Get first frame
        first_frame = region_selector.get_frame_at_time(url, 0.0)
        assert first_frame is not None

        # Get last frame
        duration = region_selector.get_video_duration(url)
        last_frame = region_selector.get_frame_at_time(url, duration - 1.0)
        assert last_frame is not None

    def test_create_adjust_confirm_region_flow(self, region_selector: RegionSelector) -> None:
        url = "https://youtube.com/watch?v=test"
        region_selector.load_video(url)
        region_selector.current_frame_time = 12.0

        region_selector.start_region(10, 15)
        region_selector.update_region(70, 65)
        region = region_selector.confirm_region()

        assert region == (10, 15, 60, 50)
        assert len(region_selector.selected_regions) == 1
        assert region_selector.selected_regions[0] == (10, 15, 60, 50, 12.0)

    def test_confirm_region_requires_valid_box(self, region_selector: RegionSelector) -> None:
        region_selector.start_region(20, 20)
        region_selector.update_region(20, 20)

        assert region_selector.confirm_region() is None
        assert region_selector.selected_regions == []


class TestRegionSelectorScrollbarMapping:
    """Test scrollbar to frame time conversion."""

    def test_scrollbar_linear_mapping(self) -> None:
        """Test linear mapping from scrollbar position to frame time."""
        durations = [60, 300, 600, 3600]  # Various video lengths

        for duration in durations:
            # At scrollbar_value=0, time should be 0
            time_0 = (0 / 100.0) * duration
            assert time_0 == 0.0

            # At scrollbar_value=100, time should be duration
            time_100 = (100 / 100.0) * duration
            assert time_100 == duration

            # At scrollbar_value=50, time should be duration/2
            time_50 = (50 / 100.0) * duration
            assert time_50 == duration / 2

    def test_scrollbar_precision(self) -> None:
        """Test scrollbar mapping precision for frame-accurate seeking."""
        duration = 600.0  # 10 minute video

        # Test various scrollbar positions
        positions = [0, 10, 25, 50, 75, 90, 100]
        expected_times = [pos / 100.0 * duration for pos in positions]

        for pos, expected_time in zip(positions, expected_times, strict=True):
            actual_time = (pos / 100.0) * duration
            assert abs(actual_time - expected_time) < 0.01  # Within 10ms

    def test_scrollbar_navigation_updates_current_frame(
        self, region_selector: RegionSelector
    ) -> None:
        url = "https://youtube.com/watch?v=test"
        region_selector.load_video(url)

        region_selector.seek_by_scrollbar(50.0)

        assert region_selector.current_frame is not None
        assert region_selector.current_frame_time == 300.0

    def test_frame_stepping_is_disabled(self, region_selector: RegionSelector) -> None:
        assert region_selector.supports_frame_stepping is False

    def test_fixed_region_helper_text_is_present(self, region_selector: RegionSelector) -> None:
        assert "Define your region where text appears consistently" in region_selector.helper_text


class TestRegionSelectorOverlayAndFocus:
    def test_preview_frame_stacks_instruction_panel_below_video(
        self, region_selector: RegionSelector
    ) -> None:
        region_selector.current_frame = np.zeros((120, 200, 3), dtype=np.uint8)

        preview = region_selector._build_preview_frame()

        assert preview.shape[1] == 200
        assert preview.shape[0] > 120

    def test_overlay_moves_to_bottom_when_top_overlaps_selected_region(
        self, region_selector: RegionSelector
    ) -> None:
        region_selector.selected_regions = [(0, 0, 200, 120, 0.0)]

        y = region_selector._compute_overlay_y(frame_height=480, box_height=80)

        assert y > 300

    def test_overlay_defaults_to_top_when_clear(self, region_selector: RegionSelector) -> None:
        region_selector.selected_regions = [(0, 250, 200, 120, 0.0)]

        y = region_selector._compute_overlay_y(frame_height=480, box_height=80)

        assert y == 10

    def test_overlay_legibility_constants_are_configured(
        self, region_selector: RegionSelector
    ) -> None:
        assert region_selector.overlay_min_effective_font_px >= 14
        assert region_selector.overlay_thickness >= 2

    def test_overlay_text_wraps_within_frame_width(self, region_selector: RegionSelector) -> None:
        frame_width = 320
        x = 10
        max_text_width = frame_width - (x + 10 + (region_selector.overlay_padding * 2))
        lines = region_selector._wrap_overlay_lines(
            [
                "Define your region where text appears consistently across the video.",
                "Use time scrollbar. Press A=add region, Enter/Q=confirm, ESC=cancel",
            ],
            max_text_width,
        )

        assert len(lines) >= 3
        for line in lines:
            width = cv2.getTextSize(
                line,
                cv2.FONT_HERSHEY_SIMPLEX,
                region_selector.overlay_font_scale,
                region_selector.overlay_thickness,
            )[0][0]
            assert width <= max_text_width

    def test_select_regions_requests_foreground_window(
        self, region_selector: RegionSelector
    ) -> None:
        with (
            patch("src.components.region_selector.cv2.namedWindow"),
            patch("src.components.region_selector.cv2.createTrackbar"),
            patch("src.components.region_selector.cv2.getTrackbarPos", return_value=0),
            patch("src.components.region_selector.cv2.imshow"),
            patch("src.components.region_selector.cv2.waitKey", return_value=13),
            patch("src.components.region_selector.cv2.destroyWindow"),
            patch("src.components.region_selector.cv2.setWindowProperty") as set_topmost,
        ):
            region_selector.select_regions("https://youtube.com/watch?v=test")

        set_topmost.assert_called()

    def test_select_regions_uses_time_scrollbar_only(self, region_selector: RegionSelector) -> None:
        with (
            patch("src.components.region_selector.cv2.namedWindow"),
            patch("src.components.region_selector.cv2.createTrackbar") as create_trackbar,
            patch("src.components.region_selector.cv2.getTrackbarPos", return_value=0),
            patch("src.components.region_selector.cv2.imshow"),
            patch("src.components.region_selector.cv2.waitKey", return_value=13),
            patch("src.components.region_selector.cv2.destroyWindow"),
            patch("src.components.region_selector.cv2.setWindowProperty"),
        ):
            region_selector.select_regions("https://youtube.com/watch?v=test")

        create_trackbar.assert_called_once()
        assert create_trackbar.call_args.args[0] == "Time (s)"


class TestRegionSelectorQualityPropagation:
    """Test that stream quality is passed through to VideoService calls."""

    def test_select_regions_opens_stream_with_specified_quality(
        self, region_selector: RegionSelector, mock_video_service: Mock
    ) -> None:
        with (
            patch("src.components.region_selector.cv2.namedWindow"),
            patch("src.components.region_selector.cv2.createTrackbar"),
            patch("src.components.region_selector.cv2.getTrackbarPos", return_value=0),
            patch("src.components.region_selector.cv2.imshow"),
            patch("src.components.region_selector.cv2.waitKey", return_value=13),
            patch("src.components.region_selector.cv2.destroyWindow"),
            patch("src.components.region_selector.cv2.setWindowProperty"),
        ):
            region_selector.select_regions("https://youtube.com/watch?v=test", quality="720p")

        mock_video_service.open_stream.assert_called_once_with(
            "https://youtube.com/watch?v=test", quality="720p"
        )

    def test_select_regions_fetches_initial_frame_with_specified_quality(
        self, region_selector: RegionSelector, mock_video_service: Mock
    ) -> None:
        with (
            patch("src.components.region_selector.cv2.namedWindow"),
            patch("src.components.region_selector.cv2.createTrackbar"),
            patch("src.components.region_selector.cv2.getTrackbarPos", return_value=0),
            patch("src.components.region_selector.cv2.imshow"),
            patch("src.components.region_selector.cv2.waitKey", return_value=13),
            patch("src.components.region_selector.cv2.destroyWindow"),
            patch("src.components.region_selector.cv2.setWindowProperty"),
        ):
            region_selector.select_regions("https://youtube.com/watch?v=test", quality="480p")

        # get_frame_at_time is called by load_video (0.0) and then again for the initial frame
        calls = mock_video_service.get_frame_at_time.call_args_list
        for call in calls:
            assert call.kwargs.get("quality") == "480p" or (
                len(call.args) >= 3 and call.args[2] == "480p"
            )

    def test_load_video_stores_quality(self, region_selector: RegionSelector) -> None:
        region_selector.load_video("https://youtube.com/watch?v=test", quality="360p")
        assert region_selector.quality == "360p"
        region_selector.video_service.get_video_info.assert_called_with(
            "https://youtube.com/watch?v=test",
            quality="360p",
        )
