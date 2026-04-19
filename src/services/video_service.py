from __future__ import annotations

import logging
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
    _ITERATION_MODE_SEQUENTIAL = "sequential"
    _ITERATION_MODE_LEGACY_SEEK = "legacy_seek"
    _FALLBACK_REASON_NONE = "none"
    _FALLBACK_REASON_DECODE_ERROR = "decode_error"
    _FALLBACK_REASON_PERFORMANCE_PROBE = "performance_probe"
    _PROBE_FRAME_BUDGET = 30
    _PROBE_SLOWDOWN_FACTOR = 1.6

    def __init__(self) -> None:
        # Cache extracted (stream_url, info) per YouTube URL to avoid repeated network lookups.
        self._stream_cache: dict[str, tuple[str, dict]] = {}
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def _is_supported_youtube_url(url: str) -> bool:
        lowered = url.lower().strip()
        return "youtube.com/watch?v=" in lowered or "youtu.be/" in lowered

    # Map UI quality labels to yt-dlp format selectors.
    # OpenCV consumes video frames only, so avoid merged video+audio selectors.
    # Prefer higher-quality video-only MP4/H.264 streams first, then progressively
    # relax constraints for compatibility.
    _QUALITY_FORMAT_MAP: dict[str, str] = {
        "best": (
            "bestvideo[ext=mp4][vcodec^=avc1]/"
            "best[ext=mp4][vcodec^=avc1]/"
            "bestvideo[ext=mp4]/"
            "best[ext=mp4]/"
            "bestvideo/best"
        ),
        "720p": (
            "bestvideo[height<=720][ext=mp4][vcodec^=avc1]/"
            "best[height<=720][ext=mp4][vcodec^=avc1]/"
            "bestvideo[height<=720][ext=mp4]/"
            "best[height<=720][ext=mp4]/"
            "best[height<=720]/best"
        ),
        "480p": (
            "bestvideo[height<=480][ext=mp4][vcodec^=avc1]/"
            "best[height<=480][ext=mp4][vcodec^=avc1]/"
            "bestvideo[height<=480][ext=mp4]/"
            "best[height<=480][ext=mp4]/"
            "best[height<=480]/best"
        ),
        "360p": (
            "bestvideo[height<=360][ext=mp4][vcodec^=avc1]/"
            "best[height<=360][ext=mp4][vcodec^=avc1]/"
            "bestvideo[height<=360][ext=mp4]/"
            "best[height<=360][ext=mp4]/"
            "best[height<=360]/best"
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
            "remote_components": ["ejs:github"],
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

    def get_video_info(self, url: str, quality: str = "best") -> dict:
        _, info = self._extract_media_url(url, quality=quality)
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

    @staticmethod
    def _compute_sampling_parameters(
        start_time: float,
        end_time: float,
        fps: int,
        native_fps: float,
    ) -> tuple[int, int, int]:
        effective_native_fps = native_fps if native_fps and native_fps > 0 else 30.0
        start_frame = int(max(0.0, start_time) * effective_native_fps)
        end_frame = int(max(start_time, end_time) * effective_native_fps)
        step = max(1, int(effective_native_fps / max(1, fps)))
        return start_frame, end_frame, step

    @staticmethod
    def _build_target_frame_indexes(start_frame: int, end_frame: int, step: int) -> list[int]:
        if start_frame > end_frame:
            return []
        frame_indexes = list(range(start_frame, end_frame + 1, max(1, step)))
        return frame_indexes or [start_frame]

    def _emit_iteration_event(
        self,
        event_type: str,
        message: str,
        frame_index: int | None = None,
        timestamp_sec: float | None = None,
        reason: str | None = None,
        source_id: str | None = None,
    ) -> None:
        if not self._logger.isEnabledFor(logging.DEBUG):
            return
        payload = {
            "event_type": event_type,
            "message": message,
            "frame_index": frame_index,
            "timestamp_sec": timestamp_sec,
            "reason": reason,
            "source_id": source_id,
        }
        self._logger.debug("video_iteration", extra={"video_iteration": payload})

    def _should_fallback(
        self,
        reason: str,
        source_id: str,
    ) -> bool:
        decision = reason in {
            self._FALLBACK_REASON_DECODE_ERROR,
            self._FALLBACK_REASON_PERFORMANCE_PROBE,
        }
        if decision:
            self._emit_iteration_event(
                event_type="fallback",
                message="Activating guarded legacy fallback.",
                reason=reason,
                source_id=source_id,
            )
        return decision

    def _run_startup_performance_probe(
        self,
        cap: cv2.VideoCapture,
        frame_indexes: list[int],
    ) -> bool:
        del cap
        if len(frame_indexes) < 2:
            return False

        budget = min(self._PROBE_FRAME_BUDGET, len(frame_indexes))
        if budget <= 1:
            return False

        probe_start = frame_indexes[0]
        probe_end = frame_indexes[budget - 1]
        sequential_distance = max(1, probe_end - probe_start)

        inferred_step = max(1, frame_indexes[1] - frame_indexes[0])
        baseline_random_cost = budget * max(10, inferred_step)
        sequential_cost = sequential_distance
        return sequential_cost > (baseline_random_cost * self._PROBE_SLOWDOWN_FACTOR)

    def _iterate_frames_legacy_seek(
        self,
        cap: cv2.VideoCapture,
        native_fps: float,
        frame_indexes: list[int],
        fail_fast: bool = True,
    ) -> Iterator[tuple[float, object]]:
        for frame_index in frame_indexes:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok:
                if fail_fast:
                    raise VideoAccessError("Could not retrieve frame from requested timestamp.")
                self._emit_iteration_event(
                    event_type="error",
                    message="Skipping unreadable fallback sample and continuing.",
                    frame_index=frame_index,
                    timestamp_sec=self._resolve_timestamp_sec(cap, frame_index, native_fps),
                    reason=self._FALLBACK_REASON_DECODE_ERROR,
                )
                continue
            timestamp_sec = self._resolve_timestamp_sec(cap, frame_index, native_fps)
            yield timestamp_sec, frame

    @staticmethod
    def _resolve_timestamp_sec(
        cap: cv2.VideoCapture,
        frame_index: int,
        native_fps: float,
    ) -> float:
        pos_msec = float(cap.get(cv2.CAP_PROP_POS_MSEC) or 0.0)
        if pos_msec > 0.0:
            return pos_msec / 1000.0
        return frame_index / native_fps

    def _iterate_frames_sequential(
        self,
        cap: cv2.VideoCapture,
        native_fps: float,
        frame_indexes: list[int],
    ) -> Iterator[tuple[float, object]]:
        if not frame_indexes:
            return

        start_frame = frame_indexes[0]
        target_idx = 0

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current_frame = start_frame

        self._emit_iteration_event(
            event_type="init",
            message="Initialized sequential decode from start frame.",
            frame_index=start_frame,
            timestamp_sec=start_frame / native_fps,
        )

        while target_idx < len(frame_indexes):
            ok, frame = cap.read()
            if not ok:
                raise VideoAccessError("Could not retrieve frame from requested timestamp.")

            target_frame = frame_indexes[target_idx]
            if current_frame == target_frame:
                timestamp_sec = self._resolve_timestamp_sec(cap, current_frame, native_fps)
                yield timestamp_sec, frame
                target_idx += 1
                if target_idx % 100 == 0:
                    self._emit_iteration_event(
                        event_type="milestone",
                        message="Sequential iteration milestone reached.",
                        frame_index=current_frame,
                        timestamp_sec=timestamp_sec,
                    )
            current_frame += 1

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

        try:
            native_fps = cap.get(cv2.CAP_PROP_FPS) or 30
            start_frame, end_frame, step = self._compute_sampling_parameters(
                start_time=start_time,
                end_time=end_time,
                fps=fps,
                native_fps=native_fps,
            )

            frame_indexes = self._build_target_frame_indexes(start_frame, end_frame, step)
            if not frame_indexes:
                return

            fallback_reason = self._FALLBACK_REASON_NONE
            source_id = f"{url}|{quality}"

            if self._run_startup_performance_probe(cap, frame_indexes):
                fallback_reason = self._FALLBACK_REASON_PERFORMANCE_PROBE

            if self._should_fallback(fallback_reason, source_id):
                yield from self._iterate_frames_legacy_seek(cap, native_fps, frame_indexes)
                return

            sequential_yield_count = 0
            try:
                for item in self._iterate_frames_sequential(cap, native_fps, frame_indexes):
                    sequential_yield_count += 1
                    yield item
            except VideoAccessError as exc:
                remaining_frame_indexes = frame_indexes[sequential_yield_count:]
                if (
                    remaining_frame_indexes
                    and self._should_fallback(self._FALLBACK_REASON_DECODE_ERROR, source_id)
                ):
                    recovery_cap = cv2.VideoCapture(stream_url)
                    if not recovery_cap.isOpened():
                        raise VideoAccessError("Could not open video stream.") from exc
                    try:
                        yield from self._iterate_frames_legacy_seek(
                            recovery_cap,
                            native_fps,
                            remaining_frame_indexes,
                            fail_fast=False,
                        )
                    finally:
                        recovery_cap.release()
                    return
                raise
        finally:
            cap.release()
