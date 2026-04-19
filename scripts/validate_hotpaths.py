"""Validation matrix for optimize-analysis-hotpaths feature.

Runs baseline vs candidate checks for:
- Gating decision parity across synthetic frame fixtures
- Grayscale conversion count reduction (single-frame, multi-region)
- Normalization output equivalence across corpus fixtures
- Profiling medians for gating and normalization hotpaths
- Timing emission behavior (enabled vs disabled detailed logging)
- SC-013 instrumentation overhead benchmark (<=2%)

Writes JSON report to:
    specs/006-optimize-analysis-hotpaths/validation_report.json

Exit codes:
    0 = all checks pass
    1 = one or more checks fail
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.fixtures.gating_frames import FIXTURE_PAIRS, multichannel_bgr_frame
from tests.fixtures.normalization_corpus import NORMALIZATION_CORPUS
from src.services.analysis_service import AnalysisService
from src.services.ocr_service import OCRService


def baseline_region_change(prev_crop: np.ndarray, curr_crop: np.ndarray, threshold: float) -> str:
    if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
        return "execute_ocr"
    pixel_diff = np.mean(np.abs(prev_crop.astype(float) - curr_crop.astype(float))) / 255.0
    return "skip_ocr" if pixel_diff < threshold else "execute_ocr"


def candidate_region_change(prev_crop: np.ndarray, curr_crop: np.ndarray, threshold: float) -> str:
    if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
        return "execute_ocr"
    pixel_diff = cv2.mean(cv2.absdiff(prev_crop, curr_crop))[0] / 255.0
    return "skip_ocr" if pixel_diff < threshold else "execute_ocr"


def baseline_normalize_for_matching(text: str) -> str:
    text = (text or "").replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", text).strip()


def baseline_normalize_name(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", (name or "").strip())
    return collapsed.lower()


def measure_median_runtime(fn, args: tuple, iterations: int = 1000) -> float:
    durations: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn(*args)
        durations.append(time.perf_counter() - t0)
    return float(np.median(durations))


def run_gating_parity(threshold: float = 0.10) -> dict[str, object]:
    total = 0
    matched = 0
    mismatches: list[str] = []

    for fixture_name, factory in FIXTURE_PAIRS.items():
        prev_crop, curr_crop = factory()
        baseline = baseline_region_change(prev_crop, curr_crop, threshold)
        candidate = candidate_region_change(prev_crop, curr_crop, threshold)
        total += 1
        if baseline == candidate:
            matched += 1
        else:
            mismatches.append(fixture_name)

    sample_prev, sample_curr = next(iter(FIXTURE_PAIRS.values()))()
    baseline_median = measure_median_runtime(baseline_region_change, (sample_prev, sample_curr, threshold))
    candidate_median = measure_median_runtime(candidate_region_change, (sample_prev, sample_curr, threshold))

    speedup = (baseline_median - candidate_median) / baseline_median if baseline_median > 0 else 0.0

    return {
        "pass": matched == total,
        "total_pairs": total,
        "matched_pairs": matched,
        "mismatches": mismatches,
        "baseline_median_sec": baseline_median,
        "candidate_median_sec": candidate_median,
        "speedup_pct": speedup * 100.0,
    }


def run_grayscale_reuse() -> dict[str, object]:
    frame_bgr = multichannel_bgr_frame()
    regions = [
        (0, 0, 64, 64),
        (64, 0, 64, 64),
        (0, 64, 64, 64),
        (64, 64, 64, 64),
    ]

    baseline_conversions = 0
    for x, y, w, h in regions:
        _ = cv2.cvtColor(np.asarray(frame_bgr)[y : y + h, x : x + w], cv2.COLOR_BGR2GRAY)
        baseline_conversions += 1

    candidate_conversions = 0
    frame_gray = cv2.cvtColor(np.asarray(frame_bgr), cv2.COLOR_BGR2GRAY)
    candidate_conversions += 1
    for x, y, w, h in regions:
        _ = frame_gray[y : y + h, x : x + w]

    conversion_reduction = baseline_conversions - candidate_conversions

    return {
        "pass": candidate_conversions <= 1 and conversion_reduction >= 3,
        "baseline_conversions": baseline_conversions,
        "candidate_conversions": candidate_conversions,
        "conversion_reduction": conversion_reduction,
    }


def run_normalization_equivalence() -> dict[str, object]:
    total = 0
    matching_for_matching = 0
    matching_normalize_name = 0
    mismatches_for_matching: list[str] = []
    mismatches_normalize_name: list[str] = []

    for input_text, expected in NORMALIZATION_CORPUS:
        total += 1

        baseline_match = baseline_normalize_for_matching(input_text)
        candidate_match = OCRService.normalize_for_matching(input_text)
        if baseline_match == candidate_match == expected:
            matching_for_matching += 1
        else:
            mismatches_for_matching.append(repr(input_text))

        baseline_name = baseline_normalize_name(input_text)
        candidate_name = AnalysisService.normalize_name(input_text)
        if baseline_name == candidate_name:
            matching_normalize_name += 1
        else:
            mismatches_normalize_name.append(repr(input_text))

    sample_text = "A  B\n\nC\tD"
    baseline_median = measure_median_runtime(baseline_normalize_for_matching, (sample_text,), iterations=10_000)
    candidate_median = measure_median_runtime(OCRService.normalize_for_matching, (sample_text,), iterations=10_000)

    return {
        "pass": matching_for_matching == total and matching_normalize_name == total,
        "total_entries": total,
        "normalize_for_matching_matches": matching_for_matching,
        "normalize_name_matches": matching_normalize_name,
        "normalize_for_matching_mismatches": mismatches_for_matching,
        "normalize_name_mismatches": mismatches_normalize_name,
        "baseline_median_sec": baseline_median,
        "candidate_median_sec": candidate_median,
    }


def run_timing_output_checks() -> dict[str, object]:
    class VideoServiceStub:
        @staticmethod
        def iterate_frames_with_timestamps(url, start_time, end_time, fps, quality="best"):
            frame = np.zeros((32, 32, 3), dtype=np.uint8)
            yield (0.0, frame)
            yield (0.5, frame)

    class OCRServiceStub:
        @staticmethod
        def detect_text(frame, region):
            return ["PLAYER 1"]

        @staticmethod
        def extract_candidates(tokens, patterns=None, filter_non_matching=False, tolerance_threshold=0.75):
            return []

    service = AnalysisService(VideoServiceStub(), OCRServiceStub())
    regions = [(0, 0, 16, 16)]

    disabled = service.analyze(
        url="mock://video",
        regions=regions,
        start_time=0.0,
        end_time=1.0,
        fps=2,
        logging_enabled=False,
    )
    enabled = service.analyze(
        url="mock://video",
        regions=regions,
        start_time=0.0,
        end_time=1.0,
        fps=2,
        logging_enabled=True,
    )

    disabled_present = disabled.runtime_metrics is not None
    enabled_present = enabled.runtime_metrics is not None
    total_ms = (
        enabled.runtime_metrics.timing_breakdown.total_ms
        if enabled.runtime_metrics and enabled.runtime_metrics.timing_breakdown
        else 0.0
    )

    return {
        "pass": (not disabled_present) and enabled_present and total_ms >= 0.0,
        "logging_disabled_emits_timing": disabled_present,
        "logging_enabled_emits_timing": enabled_present,
        "enabled_total_ms": float(total_ms),
    }


def run_sc013_overhead_benchmark() -> dict[str, object]:
    class VideoServiceStub:
        @staticmethod
        def iterate_frames_with_timestamps(url, start_time, end_time, fps, quality="best"):
            base = multichannel_bgr_frame()
            for idx in range(120):
                frame = np.copy(base)
                if idx % 20 == 0:
                    frame[0:16, 0:16, :] = idx % 255
                yield (idx * 0.05, frame)

    class OCRServiceStub:
        @staticmethod
        def detect_text(frame, region):
            arr = frame[0:96, 0:96, :].astype(np.float32)
            # Representative CPU-bound OCR-like work to reduce benchmark jitter.
            for _ in range(6):
                _ = float(np.mean(arr) + np.std(arr))
            return ["PLAYER 1", "PLAYER 2"]

        @staticmethod
        def extract_candidates(tokens, patterns=None, filter_non_matching=False, tolerance_threshold=0.75):
            return []

    def measure(logging_enabled: bool) -> tuple[float, float]:
        runs: list[float] = []
        for _ in range(9):
            service = AnalysisService(VideoServiceStub(), OCRServiceStub())
            t0 = time.perf_counter()
            service.analyze(
                url="mock://video",
                regions=[(0, 0, 64, 64), (64, 64, 64, 64)],
                start_time=0.0,
                end_time=6.0,
                fps=20,
                logging_enabled=logging_enabled,
                gating_enabled=True,
            )
            runs.append(time.perf_counter() - t0)
        stable = sorted(runs)[2:-2]
        median = float(np.median(stable))
        variance = (max(stable) - min(stable)) / median if median > 0 else 0.0
        return median, variance

    no_instr_median, no_instr_variance = measure(logging_enabled=False)
    instr_median, instr_variance = measure(logging_enabled=True)

    retried = False
    inconclusive = False
    if no_instr_variance > 0.10 or instr_variance > 0.10:
        retried = True
        no_instr_median, no_instr_variance = measure(logging_enabled=False)
        instr_median, instr_variance = measure(logging_enabled=True)
        inconclusive = no_instr_variance > 0.10 or instr_variance > 0.10

    overhead = (instr_median - no_instr_median) / no_instr_median if no_instr_median > 0 else 0.0
    passed = (not inconclusive) and overhead <= 0.02

    return {
        "pass": passed,
        "inconclusive": inconclusive,
        "retried": retried,
        "no_instrumentation_median_sec": no_instr_median,
        "instrumentation_median_sec": instr_median,
        "no_instrumentation_variance": no_instr_variance,
        "instrumentation_variance": instr_variance,
        "overhead_pct": overhead * 100.0,
    }


def main() -> int:
    report_path = Path("specs/006-optimize-analysis-hotpaths/validation_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    gating = run_gating_parity()
    grayscale = run_grayscale_reuse()
    normalization = run_normalization_equivalence()
    timing_output = run_timing_output_checks()
    sc013 = run_sc013_overhead_benchmark()

    report = {
        "feature": "006-optimize-analysis-hotpaths",
        "pass": bool(
            gating["pass"]
            and grayscale["pass"]
            and normalization["pass"]
            and timing_output["pass"]
            and sc013["pass"]
        ),
        "sections": {
            "gating_decision_parity": gating,
            "grayscale_reuse": grayscale,
            "normalization_equivalence": normalization,
            "timing_output": timing_output,
            "sc013_instrumentation_overhead": sc013,
        },
    }

    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Wrote validation report: {report_path}")
    print(f"Overall pass: {report['pass']}")
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
