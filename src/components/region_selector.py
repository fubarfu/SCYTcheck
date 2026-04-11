from __future__ import annotations

import cv2
import numpy as np

from src.services.video_service import VideoService


class RegionSelector:
    """UI component for selecting analysis regions on video frames with time-based navigation."""
    
    def __init__(self, video_service: VideoService) -> None:
        self.video_service = video_service
        self.selected_regions: list[tuple[int, int, int, int, float]] = []
        self.helper_text = "Define your region where text appears consistently across the video."
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
        self.overlay_font_scale = 0.7
        self.overlay_thickness = 2
        self.overlay_padding = 8
        self.overlay_line_height = 28
        self.overlay_min_effective_font_px = 14

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
        self.load_video(url)
        self.current_frame_time = max(0.0, frame_time_seconds)
        self.current_frame = self.get_frame_at_time(url, self.current_frame_time)
        self.selected_regions = []

        window_name = "Region Selector"
        trackbar_name = "Time (s)"
        max_seconds = max(1, int(self.video_duration))
        trackbar_value = max(0, min(int(self.current_frame_time), max_seconds))

        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        self._set_window_foreground(window_name)
        cv2.createTrackbar(trackbar_name, window_name, trackbar_value, max_seconds, lambda _: None)

        # Open a persistent stream connection so slider seeks don't re-authenticate with yt-dlp.
        cap = self.video_service.open_stream(url)

        last_trackbar = trackbar_value
        # Debounce: only fetch a new frame after the slider has been stable for this many
        # poll cycles (each cycle is ~50 ms, so 4 cycles ≈ 200 ms).
        _DEBOUNCE_CYCLES = 4
        pending_time: float | None = None
        stable_cycles = 0

        try:
            while True:
                current = cv2.getTrackbarPos(trackbar_name, window_name)
                if current != last_trackbar:
                    pending_time = float(current)
                    stable_cycles = 0
                    last_trackbar = current
                elif pending_time is not None:
                    stable_cycles += 1
                    if stable_cycles >= _DEBOUNCE_CYCLES:
                        try:
                            self.current_frame = self.video_service.get_frame_from_cap(cap, pending_time)
                        except Exception:
                            self.current_frame = self.get_frame_at_time(url, pending_time)
                        self.current_frame_time = pending_time
                        pending_time = None
                        stable_cycles = 0

                preview = self._build_preview_frame()
                cv2.imshow(window_name, preview)
                key = cv2.waitKey(50) & 0xFF

                # Press A to add a region from the currently shown frame.
                if key in (ord("a"), ord("A")):
                    region = cv2.selectROI(window_name, self.current_frame, fromCenter=False, showCrosshair=True)
                    x, y, width, height = [int(value) for value in region]
                    if width > 0 and height > 0:
                        self.selected_regions.append((x, y, width, height, self.current_frame_time))

                # Enter or Q confirms selection; ESC cancels and returns empty selection.
                if key in (13, ord("q"), ord("Q")):
                    break
                if key == 27:
                    self.selected_regions = []
                    break
        finally:
            self.video_service.close_stream(cap)
            cv2.destroyWindow(window_name)
        return [(x, y, width, height) for x, y, width, height, _ in self.selected_regions]

    def _build_preview_frame(self) -> np.ndarray:
        frame = self.current_frame.copy() if self.current_frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        for x, y, width, height, _ in self.selected_regions:
            cv2.rectangle(frame, (x, y), (x + width, y + height), (0, 255, 0), 2)

        overlay_lines = [
            self.helper_text,
            "Use time scrollbar. Press A=add region, Enter/Q=confirm, ESC=cancel",
        ]
        self._draw_instruction_overlay(frame, overlay_lines)

        return frame

    def _draw_instruction_overlay(self, frame: np.ndarray, lines: list[str]) -> None:
        """Draw a high-contrast overlay that avoids overlap with selected regions."""
        if not lines:
            return

        frame_height, frame_width = frame.shape[:2]
        x = 10
        max_text_width = max(10, frame_width - (x + 10 + (self.overlay_padding * 2)))
        wrapped_lines = self._wrap_overlay_lines(lines, max_text_width)
        if not wrapped_lines:
            return

        text_sizes = [
            cv2.getTextSize(
                text,
                cv2.FONT_HERSHEY_SIMPLEX,
                self.overlay_font_scale,
                self.overlay_thickness,
            )[0]
            for text in wrapped_lines
        ]
        max_width = max((size[0] for size in text_sizes), default=0)
        box_height = (self.overlay_line_height * len(wrapped_lines)) + (self.overlay_padding * 2)
        box_width = max_width + (self.overlay_padding * 2)

        y = self._compute_overlay_y(frame_height, box_height)
        box_width = min(box_width, frame_width - x - 10)

        cv2.rectangle(frame, (x, y), (x + box_width, y + box_height), (0, 0, 0), -1)
        cv2.rectangle(frame, (x, y), (x + box_width, y + box_height), (255, 255, 255), 1)

        for idx, text in enumerate(wrapped_lines):
            baseline_y = y + self.overlay_padding + ((idx + 1) * self.overlay_line_height) - 8
            cv2.putText(
                frame,
                text,
                (x + self.overlay_padding, baseline_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                self.overlay_font_scale,
                (255, 255, 255),
                self.overlay_thickness,
                cv2.LINE_AA,
            )

    def _wrap_overlay_lines(self, lines: list[str], max_text_width: int) -> list[str]:
        wrapped: list[str] = []
        for line in lines:
            wrapped.extend(self._wrap_overlay_line(line, max_text_width))
        return wrapped

    def _wrap_overlay_line(self, line: str, max_text_width: int) -> list[str]:
        """Wrap one overlay line so each rendered segment fits max_text_width."""
        text = line.strip()
        if not text:
            return [""]

        words = text.split()
        if not words:
            return [text]

        wrapped: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            candidate_width = cv2.getTextSize(
                candidate,
                cv2.FONT_HERSHEY_SIMPLEX,
                self.overlay_font_scale,
                self.overlay_thickness,
            )[0][0]
            if candidate_width <= max_text_width:
                current = candidate
            else:
                wrapped.append(current)
                current = word

        wrapped.append(current)
        return wrapped

    def _compute_overlay_y(self, frame_height: int, box_height: int) -> int:
        """Keep instructions clear of selected regions by moving overlay to bottom when needed."""
        top_y = 10
        top_bottom = top_y + box_height
        overlaps_top = any(
            y < top_bottom and (y + height) > top_y
            for _x, y, _width, height, _time in self.selected_regions
        )
        if not overlaps_top:
            return top_y

        return max(10, frame_height - box_height - 10)

    def _set_window_foreground(self, window_name: str) -> None:
        """Request region selector popup foreground visibility where backend supports it."""
        try:
            cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)
        except Exception:
            return

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
