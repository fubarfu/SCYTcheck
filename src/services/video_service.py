from __future__ import annotations

import os
import shutil
from collections.abc import Iterator

import cv2
from yt_dlp import YoutubeDL


class VideoAccessError(RuntimeError):
    pass


class InvalidURLError(ValueError):
    pass


class VideoService:
    def __init__(self) -> None:
        # Cache extracted (stream_url, info) per YouTube URL to avoid repeated network lookups.
        self._stream_cache: dict[str, tuple[str, dict]] = {}

    @staticmethod
    def _is_supported_youtube_url(url: str) -> bool:
        lowered = url.lower().strip()
        return "youtube.com/watch?v=" in lowered or "youtu.be/" in lowered

    # Map UI quality labels to yt-dlp format selectors.
    # Prefer mp4 for OpenCV compatibility; fall through to any format as a last resort.
    _QUALITY_FORMAT_MAP: dict[str, str] = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "720p": (
            "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/"
            "best[height<=720][ext=mp4]/best[height<=720]/best"
        ),
        "480p": (
            "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/"
            "best[height<=480][ext=mp4]/best[height<=480]/best"
        ),
        "360p": (
            "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/"
            "best[height<=360][ext=mp4]/best[height<=360]/best"
        ),
    }

    @staticmethod
    def _build_ydl_opts(quality: str = "best") -> dict[str, object]:
        fmt = VideoService._QUALITY_FORMAT_MAP.get(
            quality, VideoService._QUALITY_FORMAT_MAP["best"]
        )
        ydl_opts: dict[str, object] = {
            "quiet": True,
            "skip_download": True,
            "format": fmt,
        }

        # yt-dlp >= 2026 expects js_runtimes as {runtime: {config}} dict
        js_runtimes: dict[str, dict] = {"deno": {}}
        for runtime in ("node", "quickjs", "bun"):
            runtime_path = shutil.which(runtime)
            if runtime_path:
                js_runtimes[runtime] = {"path": runtime_path}

        deno_path = shutil.which("deno")
        if deno_path:
            js_runtimes["deno"] = {"path": deno_path}
        else:
            user_profile = os.getenv("USERPROFILE")
            if user_profile:
                scoop_deno = os.path.join(user_profile, "scoop", "shims", "deno.exe")
                if os.path.exists(scoop_deno):
                    js_runtimes["deno"] = {"path": scoop_deno}

        ydl_opts["js_runtimes"] = js_runtimes
        return ydl_opts

    def validate_youtube_url(self, url: str) -> tuple[bool, str]:
        """Validate URL format and accessibility before analysis starts."""
        if not url or not self._is_supported_youtube_url(url):
            return False, "Please provide a valid YouTube video URL."

        try:
            self._extract_media_url(url)
        except InvalidURLError as exc:
            return False, str(exc)
        except Exception as exc:
            return False, f"Video could not be accessed: {exc}"

        return True, ""

    def _extract_media_url(self, url: str, quality: str = "best") -> tuple[str, dict]:
        if not url or not self._is_supported_youtube_url(url):
            raise InvalidURLError("Please provide a valid YouTube URL.")

        cache_key = f"{url}|{quality}"
        if cache_key in self._stream_cache:
            return self._stream_cache[cache_key]

        with YoutubeDL(self._build_ydl_opts(quality)) as ydl:
            info = ydl.extract_info(url, download=False)

        stream_url = info.get("url")
        if not stream_url:
            # Merged formats (e.g. bestvideo+bestaudio) store the URL inside requested_formats.
            for fmt in info.get("requested_formats") or []:
                if fmt.get("url"):
                    stream_url = fmt["url"]
                    break
        if not stream_url:
            raise VideoAccessError("No playable stream URL found for this video.")

        self._stream_cache[cache_key] = (stream_url, info)
        return stream_url, info

    def get_video_info(self, url: str) -> dict:
        _, info = self._extract_media_url(url)
        return {
            "title": info.get("title"),
            "duration": info.get("duration"),
            "width": info.get("width"),
            "height": info.get("height"),
        }

    def get_frame_at_time(self, url: str, time_seconds: float, quality: str = "best"):
        last_error: Exception | None = None
        for _attempt in range(3):
            try:
                stream_url, _ = self._extract_media_url(url, quality=quality)
                cap = cv2.VideoCapture(stream_url)
                if not cap.isOpened():
                    raise VideoAccessError("Could not open video stream.")

                cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, time_seconds) * 1000)
                ok, frame = cap.read()
                cap.release()
                if not ok:
                    raise VideoAccessError("Could not retrieve frame from requested timestamp.")
                return frame
            except Exception as exc:
                last_error = exc
        raise VideoAccessError(
            str(last_error) if last_error else "Could not retrieve frame from requested timestamp."
        )

    def open_stream(self, url: str, quality: str = "best") -> cv2.VideoCapture:
        """Open and return a persistent VideoCapture for repeated seeks (e.g. region selector).
        Caller is responsible for calling close_stream() when done."""
        stream_url, _ = self._extract_media_url(url, quality=quality)
        cap = cv2.VideoCapture(stream_url)
        if not cap.isOpened():
            raise VideoAccessError("Could not open video stream.")
        return cap

    @staticmethod
    def get_frame_from_cap(cap: cv2.VideoCapture, time_seconds: float):
        """Read a frame from an already-open VideoCapture by seeking to time_seconds."""
        cap.set(cv2.CAP_PROP_POS_MSEC, max(0.0, time_seconds) * 1000)
        ok, frame = cap.read()
        if not ok:
            raise VideoAccessError("Could not retrieve frame from requested timestamp.")
        return frame

    @staticmethod
    def close_stream(cap: cv2.VideoCapture) -> None:
        """Release a VideoCapture opened with open_stream()."""
        cap.release()

    def get_frames_in_range(
        self, url: str, start_time: float, end_time: float, fps: int, quality: str = "best"
    ) -> Iterator:
        for _, frame in self.iterate_frames_with_timestamps(
            url, start_time, end_time, fps, quality=quality
        ):
            yield frame

    def iterate_frames_with_timestamps(
        self,
        url: str,
        start_time: float,
        end_time: float,
        fps: int,
        quality: str = "best",
    ) -> Iterator[tuple[float, object]]:
        stream_url, _ = self._extract_media_url(url, quality=quality)
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
