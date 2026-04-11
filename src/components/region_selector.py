from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from src.services.video_service import VideoService


class RegionSelector:
    """UI component for selecting analysis regions on video frames with time-based navigation."""
    
    def __init__(self, video_service: VideoService) -> None:
        self.video_service = video_service
        self.selected_regions: list[tuple[int, int, int, int, float]] = []
        self.current_frame: np.ndarray | None = None
        self.current_frame_time: float = 0.0
        self.video_duration: float = 0.0
        self.draw_mode = False
        self.start_x = 0
        self.start_y = 0
        self.rect_id: int | None = None
        self.url: str = ""
        self.pending_region: tuple[int, int, int, int] | None = None
        self.supports_frame_stepping = False

    def select_regions(
        self,
        url: str,
        frame_time_seconds: float = 0.0,
    ) -> list[tuple[int, int, int, int]]:
        """
        Select analysis regions from video frames.
        
        Args:
            url: YouTube video URL
            frame_time_seconds: Initial frame time to display
            
        Returns:
            List of (x, y, width, height) tuples for selected regions
        """
        # Use legacy mode for MVP - basic OpenCV region selection
        # Full scrollbar UI to be implemented in Phase 3+ with enhanced UI
        frame = self.video_service.get_frame_at_time(url, frame_time_seconds)
        selected: list[tuple[int, int, int, int]] = []

        while True:
            region = cv2.selectROI(
                "Select Region (ESC to finish)",
                frame,
                fromCenter=False,
                showCrosshair=True,
            )
            x, y, width, height = [int(value) for value in region]
            if width <= 0 or height <= 0:
                break
            selected.append((x, y, width, height))

            preview = frame.copy()
            cv2.rectangle(preview, (x, y), (x + width, y + height), (0, 255, 0), 2)
            cv2.imshow("Select Region (ESC to finish)", preview)
            if cv2.waitKey(200) == 27:
                break

        cv2.destroyAllWindows()
        return selected

    def get_frame_at_time(self, url: str, time_seconds: float) -> np.ndarray:
        """Get a video frame at specific time (supports seek-to-time)."""
        return self.video_service.get_frame_at_time(url, time_seconds)
    
    def get_video_duration(self, url: str) -> float:
        """Get video duration in seconds."""
        info = self.video_service.get_video_info(url)
        return info.get("duration", 0.0)

    def load_video(self, url: str) -> None:
        """Load video metadata for scrollbar-based navigation."""
        self.url = url
        self.video_duration = self.get_video_duration(url)
        self.current_frame_time = 0.0
        self.current_frame = self.get_frame_at_time(url, 0.0)

    def seek_by_scrollbar(self, scrollbar_value: float) -> np.ndarray:
        """Navigate by horizontal scrollbar position in [0, 100]."""
        if not self.url:
            raise ValueError("No video loaded. Call load_video first.")

        bounded = max(0.0, min(float(scrollbar_value), 100.0))
        if self.video_duration <= 0:
            target_time = 0.0
        else:
            target_time = (bounded / 100.0) * self.video_duration

        self.current_frame_time = target_time
        self.current_frame = self.get_frame_at_time(self.url, target_time)
        return self.current_frame

    def start_region(self, x: int, y: int) -> None:
        """Begin creating a selection rectangle at the current frame."""
        self.start_x = int(x)
        self.start_y = int(y)
        self.pending_region = (self.start_x, self.start_y, 0, 0)

    def update_region(self, x: int, y: int) -> None:
        """Adjust the pending rectangle while dragging."""
        if self.pending_region is None:
            return

        current_x = int(x)
        current_y = int(y)
        left = min(self.start_x, current_x)
        top = min(self.start_y, current_y)
        width = abs(current_x - self.start_x)
        height = abs(current_y - self.start_y)
        self.pending_region = (left, top, width, height)

    def confirm_region(self) -> tuple[int, int, int, int] | None:
        """Confirm current pending region and store it with frame-time context."""
        if self.pending_region is None:
            return None

        x, y, width, height = self.pending_region
        if width <= 0 or height <= 0:
            self.pending_region = None
            return None

        self.selected_regions.append((x, y, width, height, self.current_frame_time))
        self.pending_region = None
        return (x, y, width, height)
