from __future__ import annotations

from collections.abc import Iterator

import cv2
from yt_dlp import YoutubeDL


class VideoAccessError(RuntimeError):
    pass


class InvalidURLError(ValueError):
    pass


class VideoService:
    @staticmethod
    def _is_supported_youtube_url(url: str) -> bool:
        lowered = url.lower().strip()
        return (
            "youtube.com/watch?v=" in lowered
            or "youtu.be/" in lowered
        )

    def validate_youtube_url(self, url: str) -> tuple[bool, str]:
        """Validate URL format and accessibility before analysis starts."""
        if not url or not self._is_supported_youtube_url(url):
            return False, "Please provide a valid YouTube video URL."

        try:
            self._extract_media_url(url)
        except InvalidURLError as exc:
            return False, str(exc)
        except Exception:
            return False, "Video is not publicly reachable or could not be accessed."

        return True, ""

    def _extract_media_url(self, url: str) -> tuple[str, dict]:
        if not url or not self._is_supported_youtube_url(url):
            raise InvalidURLError("Please provide a valid YouTube URL.")

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "format": "best[ext=mp4]/best",
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        stream_url = info.get("url")
        if not stream_url:
            raise VideoAccessError("No playable stream URL found for this video.")

        return stream_url, info

    def get_video_info(self, url: str) -> dict:
        _, info = self._extract_media_url(url)
        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "width": info.get("width"),
            "height": info.get("height"),
        }

    def get_frame_at_time(self, url: str, time_seconds: float):
        stream_url, _ = self._extract_media_url(url)
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise VideoAccessError("Could not open video stream.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_index = int(max(0.0, time_seconds) * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise VideoAccessError("Could not retrieve frame from requested timestamp.")

        return frame

    def get_frames_in_range(
        self, url: str, start_time: float, end_time: float, fps: int
    ) -> Iterator:
        for _, frame in self.iterate_frames_with_timestamps(url, start_time, end_time, fps):
            yield frame

    def iterate_frames_with_timestamps(
        self,
        url: str,
        start_time: float,
        end_time: float,
        fps: int,
    ) -> Iterator[tuple[float, object]]:
        stream_url, _ = self._extract_media_url(url)
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise VideoAccessError("Could not open video stream.")

        native_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        start_frame = int(max(0.0, start_time) * native_fps)
        end_frame = int(max(start_time, end_time) * native_fps)
        step = max(1, int(native_fps / max(1, fps)))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current = start_frame

        while current <= end_frame:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current)
            ok, frame = cap.read()
            if not ok:
                break
            timestamp_sec = current / native_fps
            yield timestamp_sec, frame
            current += step

        cap.release()
