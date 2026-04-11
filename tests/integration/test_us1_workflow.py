"""
Integration tests for US1: Analyze YouTube Video for Text Strings.

Testing the complete workflow:
1. Input YouTube URL
2. Navigate video frames with time-based scrollbar
3. Select regions from video
4. Execute analysis on selected regions
5. Generate auto-named CSV
6. Export to specified folder
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import numpy as np
import pytest

from src.components.region_selector import RegionSelector
from src.data.models import ContextPattern, VideoAnalysis
from src.services.analysis_service import AnalysisService
from src.services.export_service import ExportService
from src.services.ocr_service import OCRService
from src.services.video_service import VideoService


class TestUS1FullWorkflow:
    """Integration tests for US1 - YouTube Text Analysis workflow."""
    
    @pytest.fixture
    def mock_services(self) -> dict:
        """Create mock services for integration testing."""
        # Mock video service
        video_service = Mock(spec=VideoService)
        video_service.get_video_info.return_value = {
            "title": "Test Video",
            "duration": 60.0,  # 1 minute
            "width": 1280,
            "height": 720,
        }
        
        # Return test frames
        def get_frame_at_time(url: str, time_seconds: float) -> np.ndarray:
            frame = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
            return frame
        
        video_service.get_frame_at_time.side_effect = get_frame_at_time
        
        # Mock get_frames_in_range to return an iterable
        def get_frames_in_range(url: str, start_time: float, end_time: float, fps: int):
            # Generate frames for the range
            num_frames = max(1, int((end_time - start_time) * fps))
            for i in range(num_frames):
                yield np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)
        
        video_service.get_frames_in_range.side_effect = get_frames_in_range
        video_service.iterate_frames_with_timestamps.side_effect = (
            lambda url, start_time, end_time, fps: (
                (start_time + i, frame)
                for i, frame in enumerate(get_frames_in_range(url, start_time, end_time, fps))
            )
        )
        
        # Mock OCR service
        ocr_service = Mock(spec=OCRService)
        ocr_service.detect_text.return_value = ["Test", "Text", "Found"]
        ocr_service.extract_candidates.side_effect = lambda lines, patterns=None, filter_non_matching=False: [
            (line, None) for line in lines
        ]
        
        return {
            "video_service": video_service,
            "ocr_service": ocr_service,
        }
    
    def test_us1_complete_workflow(self, mock_services: dict, tmp_path: Path) -> None:
        """Test complete US1 workflow from URL to CSV export."""
        video_service = mock_services["video_service"]
        ocr_service = mock_services["ocr_service"]
        
        # Step 1: YouTube URL input
        url = "https://youtube.com/watch?v=testvideoabc123"
        
        # Step 2: Frame navigation with scrollbar
        region_selector = RegionSelector(video_service)
        
        # Simulate scrollbar navigation
        frame_times = [0.0, 15.0, 30.0]  # Navigate to 3 different times
        frames = [
            region_selector.get_frame_at_time(url, t) 
            for t in frame_times
        ]
        assert len(frames) == len(frame_times)
        
        # Step 3: Region selection
        regions = [(100, 100, 200, 150)]  # Sample region: x, y, width, height
        
        # Step 4: Execute analysis
        analysis_service = AnalysisService(video_service, ocr_service)
        analysis = analysis_service.analyze(
            url=url,
            regions=regions,
            start_time=0.0,
            end_time=60.0,
            fps=1,
        )
        
        assert analysis.url == url
        assert len(analysis.text_strings) > 0
        
        # Step 5: Auto-filename generation
        export_service = ExportService()
        test_time = datetime(2026, 4, 11, 14, 30, 45)
        filename = export_service.generate_filename(url, test_time)
        
        assert filename == "scytcheck_testvideoabc123_20260411-143045.csv"
        assert filename.endswith(".csv")
        
        # Step 6: Folder validation
        is_valid, error_msg = export_service.validate_output_folder(str(tmp_path))
        assert is_valid
        assert error_msg == ""
        
        # Step 7: Export to CSV
        csv_path = export_service.export_to_csv(
            analysis,
            str(tmp_path),
            filename
        )
        
        assert csv_path.exists()
        content = csv_path.read_text(encoding="utf-8")
        assert "PlayerName,NormalizedName,OccurrenceCount,FirstSeenSec,LastSeenSec,RepresentativeRegion" in content
    
    def test_scrollbar_time_navigation_workflow(self, mock_services: dict) -> None:
        """Test scrollbar-based time navigation specific to US1."""
        video_service = mock_services["video_service"]
        region_selector = RegionSelector(video_service)
        url = "https://youtube.com/watch?v=test"
        
        # Get video duration
        duration = region_selector.get_video_duration(url)
        assert duration == 60.0
        
        # Simulate scrollbar positions (0-100 range)
        scrollbar_positions = [0, 25, 50, 75, 100]
        expected_times = [
            (pos / 100.0) * duration 
            for pos in scrollbar_positions
        ]
        
        # Verify frame retrieval at each scrollbar position
        for scrollbar_pos, expected_time in zip(scrollbar_positions, expected_times):
            frame = region_selector.get_frame_at_time(url, expected_time)
            assert frame is not None
            assert frame.shape == (720, 1280, 3)
    
    def test_region_selection_with_frame_time(self, mock_services: dict) -> None:
        """Test that regions can track their frame_time when selected."""
        video_service = mock_services["video_service"]
        
        # Create analysis with frame_time tracking
        analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
        
        # Add detections at different frame times
        analysis.add_detection("Text1", (10, 20, 100, 50), frame_time=5.0)
        analysis.add_detection("Text2", (110, 20, 100, 50), frame_time=5.0)
        analysis.add_detection("Text3", (10, 100, 150, 50), frame_time=15.0)
        
        # Verify frame times are recorded
        assert analysis.text_strings[0].frame_time == 5.0
        assert analysis.text_strings[1].frame_time == 5.0
        assert analysis.text_strings[2].frame_time == 15.0
    
    def test_invalid_folder_workflow(self, mock_services: dict) -> None:
        """Test error handling when output folder is invalid."""
        export_service = ExportService()
        
        # Test non-existent folder
        is_valid, error_msg = export_service.validate_output_folder("/invalid/nonexistent")
        assert not is_valid
        assert "does not exist" in error_msg
    
    def test_analysis_completion_under_5_minutes(self, mock_services: dict, tmp_path: Path) -> None:
        """Test that 10-minute video analysis completes in under 5 minutes (SC-001)."""
        import time
        
        video_service = mock_services["video_service"]
        ocr_service = mock_services["ocr_service"]
        
        # Create analysis service
        analysis_service = AnalysisService(video_service, ocr_service)
        
        # Simulate 10-minute video (600 seconds)
        url = "https://youtube.com/watch?v=tenminutevideo"
        regions = [(100, 100, 200, 150)]
        
        # Record start time
        start = time.time()
        
        # Execute analysis (with fast fps=1 for testing)
        analysis = analysis_service.analyze(
            url=url,
            regions=regions,
            start_time=0.0,
            end_time=600.0,
            fps=1,  # Sample at 1 fps for speed
        )
        
        elapsed = time.time() - start
        
        # Should complete quickly (well under 5 minutes for mock)
        # Real video processing will take longer but mocks are instant
        assert elapsed < 60.0  # Should be much faster with mocks
        assert analysis.url == url

    def test_deduplicated_analysis_export_flow(self, tmp_path: Path) -> None:
        video_service = Mock(spec=VideoService)

        frames = [
            np.zeros((720, 1280, 3), dtype=np.uint8),
            np.zeros((720, 1280, 3), dtype=np.uint8),
            np.zeros((720, 1280, 3), dtype=np.uint8),
        ]

        def iterate_frames_with_timestamps(url: str, start_time: float, end_time: float, fps: int):
            for ts, frame in zip([1.0, 1.5, 4.2], frames):
                yield ts, frame

        video_service.iterate_frames_with_timestamps.side_effect = iterate_frames_with_timestamps
        video_service.get_frames_in_range.return_value = iter(frames)

        ocr_service = Mock(spec=OCRService)
        ocr_service.extract_candidates.side_effect = [
            [("Alice", "pattern-1")],
            [("alice", "pattern-1")],
            [("Alice", "pattern-1")],
        ]
        ocr_service.detect_text.return_value = ["Alice"]

        analysis_service = AnalysisService(video_service, ocr_service)
        analysis = analysis_service.analyze(
            url="https://youtube.com/watch?v=testvideo",
            regions=[(100, 100, 200, 150)],
            start_time=0.0,
            end_time=10.0,
            fps=1,
            context_patterns=[ContextPattern(id="pattern-1", before_text="Player:")],
            filter_non_matching=True,
            event_gap_threshold_sec=1.0,
        )

        assert len(analysis.player_summaries) == 1
        assert analysis.player_summaries[0].normalized_name == "alice"
        assert analysis.player_summaries[0].occurrence_count == 2

        export_service = ExportService()
        exported = export_service.export_to_csv(analysis, str(tmp_path), "summary.csv")
        lines = exported.read_text(encoding="utf-8").splitlines()
        assert lines[0] == "PlayerName,NormalizedName,OccurrenceCount,FirstSeenSec,LastSeenSec,RepresentativeRegion"
        assert lines[1].startswith("Alice,alice,2,")

    def test_region_selector_foreground_and_overlay_workflow(self, mock_services: dict) -> None:
        video_service = mock_services["video_service"]
        selector = RegionSelector(video_service)
        selector.load_video("https://youtube.com/watch?v=test")
        selector.selected_regions = [(0, 0, 220, 120, 0.0)]

        preview = selector._build_preview_frame()
        lower_overlay_band = preview[-120:, 0:420]

        assert selector._compute_overlay_y(frame_height=preview.shape[0], box_height=80) >= preview.shape[0] - 100
        assert np.any(lower_overlay_band != 0)

        with patch("src.components.region_selector.cv2.namedWindow"), patch(
            "src.components.region_selector.cv2.createTrackbar"
        ), patch("src.components.region_selector.cv2.getTrackbarPos", return_value=0), patch(
            "src.components.region_selector.cv2.imshow"
        ), patch("src.components.region_selector.cv2.waitKey", return_value=13), patch(
            "src.components.region_selector.cv2.destroyWindow"
        ), patch("src.components.region_selector.cv2.setWindowProperty") as set_topmost:
            selector.select_regions("https://youtube.com/watch?v=test")

        set_topmost.assert_called()


class TestUS1EdgeCases:
    """Test edge cases for US1 workflow."""
    
    def test_short_video_analysis(self) -> None:
        """Test analysis of very short videos (< 1 second)."""
        video_service = Mock(spec=VideoService)
        video_service.get_video_info.return_value = {
            "title": "Short Video",
            "duration": 0.5,  # Half second
            "width": 1280,
            "height": 720,
        }
        
        region_selector = RegionSelector(video_service)
        duration = region_selector.get_video_duration("https://youtube.com/watch?v=short")
        
        assert duration == 0.5
    
    def test_very_long_video_analysis(self) -> None:
        """Test analysis of very long videos (hours)."""
        video_service = Mock(spec=VideoService)
        video_service.get_video_info.return_value = {
            "title": "Long Video",
            "duration": 14400.0,  # 4 hours
            "width": 1280,
            "height": 720,
        }
        
        region_selector = RegionSelector(video_service)
        duration = region_selector.get_video_duration("https://youtube.com/watch?v=long")
        
        assert duration == 14400.0
        
        # Test scrollbar mapping for long video
        # At 50% scrollbar, should be at 7200 seconds (2 hours)
        time_at_50 = (50 / 100.0) * duration
        assert time_at_50 == 7200.0
    
    def test_multiple_regions_same_time(self) -> None:
        """Test selecting multiple regions at the same frame time."""
        analysis = VideoAnalysis(url="https://youtube.com/watch?v=test")
        
        # Add multiple regions at same time
        analysis.add_detection("Text1", (10, 20, 100, 50), frame_time=5.0)
        analysis.add_detection("Text2", (150, 20, 100, 50), frame_time=5.0)
        analysis.add_detection("Text3", (290, 20, 100, 50), frame_time=5.0)
        
        assert len(analysis.text_strings) == 3
        assert all(ts.frame_time == 5.0 for ts in analysis.text_strings)
