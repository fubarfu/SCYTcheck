"""
Pytest configuration and shared fixtures for SCYTcheck tests.
Provides mock video frames and utilities for offline testing.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.data.models import Region, VideoAnalysis


@pytest.fixture
def mock_video_frame() -> np.ndarray:
    """
    Generate a mock video frame as a numpy array.
    Simulates a 1280x720 frame from a video (BGR format for OpenCV compatibility).
    """
    # Create a realistic-looking frame with some variation
    frame = np.random.randint(50, 200, (720, 1280, 3), dtype=np.uint8)

    # Add a white rectangle to simulate text region
    frame[100:150, 200:400] = 255

    return frame


@pytest.fixture
def mock_video_frames(mock_video_frame: np.ndarray) -> list[np.ndarray]:
    """
    Generate a sequence of mock video frames.
    Useful for testing scrollbar navigation and frame transitions.
    """
    frames = []
    for i in range(10):
        # Create slight variations to simulate video progression
        frame = mock_video_frame.copy()
        frame[50 + i : 60 + i, 100 + i : 200 + i] = (100 + i * 10, 100 + i * 10, 100 + i * 10)
        frames.append(frame)

    return frames


@pytest.fixture
def mock_region() -> Region:
    """Fixture providing a mock Region with spatial and temporal data."""
    return Region(x=10, y=20, width=300, height=100, frame_time=2.5)


@pytest.fixture
def mock_video_analysis() -> VideoAnalysis:
    """
    Fixture providing a VideoAnalysis with sample detections.
    Useful for testing export and processing pipelines.
    """
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=testid")

    # Add sample detections at different times
    analysis.add_detection("Hello", (10, 20, 100, 50), frame_time=1.0)
    analysis.add_detection("World", (120, 20, 100, 50), frame_time=1.0)
    analysis.add_detection("Test", (10, 100, 150, 50), frame_time=2.5)
    analysis.add_detection("Hello", (10, 20, 100, 50), frame_time=3.0)  # Duplicate text

    return analysis


class MockFrameGenerator:
    """Utility class for generating test video frames with specific characteristics."""

    @staticmethod
    def create_blank_frame(
        height: int = 720, width: int = 1280, bg_color: tuple[int, int, int] = (0, 0, 0)
    ) -> np.ndarray:
        """Create a blank frame with specified dimensions and background color."""
        frame = np.full((height, width, 3), bg_color, dtype=np.uint8)
        return frame

    @staticmethod
    def create_frame_with_region(
        height: int = 720,
        width: int = 1280,
        region_color: tuple[int, int, int] = (255, 255, 255),
        region_coords: tuple[int, int, int, int] = (10, 20, 100, 50),
    ) -> np.ndarray:
        """Create a frame with a colored rectangular region."""
        frame = MockFrameGenerator.create_blank_frame(height, width)
        x, y, w, h = region_coords
        frame[y : y + h, x : x + w] = region_color
        return frame


@pytest.fixture
def mock_frame_generator() -> MockFrameGenerator:
    """Fixture providing access to the MockFrameGenerator utility."""
    return MockFrameGenerator()
