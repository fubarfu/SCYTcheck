"""SC-008 player summary parity gate for hotpath optimizations."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from src.services.analysis_service import AnalysisService
from tests.fixtures import gating_frames


class _VideoServiceStub:
    def __init__(self, frames: list[tuple[float, np.ndarray]]) -> None:
        self._frames = frames

    def iterate_frames_with_timestamps(self, url, start_time, end_time, fps, quality="best"):
        for item in self._frames:
            yield item


class _OCRServiceStub:
    @staticmethod
    def detect_text(frame, region):
        region_names = {
            (0, 0, 64, 64): "ALPHA",
            (64, 0, 64, 64): "BRAVO",
            (0, 64, 64, 64): "CHARLIE",
            (64, 64, 64, 64): "DELTA",
        }
        return [region_names.get(region, "UNKNOWN")]

    @staticmethod
    def extract_candidates(tokens, patterns=None, filter_non_matching=False, tolerance_threshold=0.75):
        cleaned = [str(token).strip() for token in tokens if str(token).strip()]
        return [(name, None) for name in cleaned]


def _build_frames(frame_count: int = 40) -> list[tuple[float, np.ndarray]]:
    base = gating_frames.multichannel_bgr_frame()
    frames: list[tuple[float, np.ndarray]] = []
    for idx in range(frame_count):
        frame = np.copy(base)
        if idx % 10 == 0:
            frame[2:6, 2:6, :] = (idx * 7) % 255
        frames.append((idx * 0.1, frame))
    return frames


def _patch_baseline_hotpaths(service: AnalysisService) -> None:
    def baseline_crop(frame, region, frame_gray=None):
        array = np.asarray(frame)
        if array.size == 0:
            return None
        x, y, width, height = region
        if width <= 0 or height <= 0:
            return None
        cropped = array[y : y + height, x : x + width]
        if cropped.size == 0:
            return None
        if cropped.ndim == 3:
            return cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        return cropped

    def baseline_change(prev_crop, curr_crop, gating_threshold=0.02):
        if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
            return {
                "pixel_diff": 1.0,
                "decision_action": "execute_ocr",
                "reason": "shape_mismatch",
            }
        pixel_diff = np.mean(np.abs(prev_crop.astype(float) - curr_crop.astype(float))) / 255.0
        return {
            "pixel_diff": float(pixel_diff),
            "decision_action": "skip_ocr" if pixel_diff < gating_threshold else "execute_ocr",
            "reason": "computed",
        }

    service._crop_region_gray = staticmethod(baseline_crop)  # type: ignore[method-assign]
    service._compute_frame_region_change = staticmethod(baseline_change)  # type: ignore[method-assign]


def _summaries_key(analysis) -> list[tuple[str, str, str, int, str]]:
    return [
        (
            summary.player_name,
            summary.start_timestamp,
            summary.normalized_name,
            summary.occurrence_count,
            summary.representative_region,
        )
        for summary in analysis.player_summaries
    ]


@pytest.mark.parametrize(
    "gating_enabled,gating_threshold",
    [
        (True, 0.02),
        (True, 0.10),
        (False, 0.02),
    ],
)
def test_hotpath_player_summary_parity_sc008(gating_enabled: bool, gating_threshold: float):
    """SC-008: player identity/count/order must match baseline exactly."""
    regions = [
        (0, 0, 64, 64),
        (64, 0, 64, 64),
        (0, 64, 64, 64),
        (64, 64, 64, 64),
    ]

    baseline_frames = _build_frames()
    candidate_frames = _build_frames()

    baseline_service = AnalysisService(_VideoServiceStub(baseline_frames), _OCRServiceStub())
    candidate_service = AnalysisService(_VideoServiceStub(candidate_frames), _OCRServiceStub())
    _patch_baseline_hotpaths(baseline_service)

    baseline_analysis = baseline_service.analyze(
        url="mock://video",
        regions=regions,
        start_time=0.0,
        end_time=4.0,
        fps=10,
        gating_enabled=gating_enabled,
        gating_threshold=gating_threshold,
    )
    candidate_analysis = candidate_service.analyze(
        url="mock://video",
        regions=regions,
        start_time=0.0,
        end_time=4.0,
        fps=10,
        gating_enabled=gating_enabled,
        gating_threshold=gating_threshold,
    )

    baseline_key = _summaries_key(baseline_analysis)
    candidate_key = _summaries_key(candidate_analysis)

    assert candidate_key == baseline_key, (
        "Player summary parity failed: identity/count/order differs between baseline and candidate"
    )
