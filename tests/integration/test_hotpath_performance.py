"""Performance tests for gating hotpath optimization.

Tests SC-001 (total runtime ≥15%) and SC-005 (gating hotpath ≥20%).
"""

import numpy as np
import re
import time
import pytest
import cv2
from tests.fixtures import gating_frames
from src.services.analysis_service import AnalysisService
from src.services.ocr_service import OCRService


class TestGatingPerformance:
    """Verify that candidate gating produces ≥20% speedup (SC-005)."""
    
    def baseline_compute_frame_region_change(self, prev_crop, curr_crop, threshold):
        """Baseline: np.mean(np.abs(float diff))."""
        if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
            return 1.0, "execute_ocr"
        
        pixel_diff = np.mean(np.abs(prev_crop.astype(float) - curr_crop.astype(float))) / 255.0
        decision = "skip_ocr" if pixel_diff < threshold else "execute_ocr"
        return pixel_diff, decision
    
    def candidate_compute_frame_region_change(self, prev_crop, curr_crop, threshold):
        """Candidate: cv2.absdiff + cv2.mean."""
        import cv2
        
        if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
            return 1.0, "execute_ocr"
        
        pixel_diff = cv2.mean(cv2.absdiff(prev_crop, curr_crop))[0] / 255.0
        decision = "skip_ocr" if pixel_diff < threshold else "execute_ocr"
        return pixel_diff, decision
    
    def test_gating_hotpath_performance_sc005(self):
        """SC-005: Median gating time ≥20% faster with candidate.
        
        Runs 1000 iterations of gating on a (64, 64) frame pair.
        Measures baseline and candidate; asserts candidate is ≥20% faster.
        """
        prev, curr = np.ones((64, 64), dtype=np.uint8) * 100, np.ones((64, 64), dtype=np.uint8) * 110
        threshold = 0.10
        iterations = 1000
        
        # Baseline timing
        baseline_times = []
        for _ in range(5):  # Warm up
            self.baseline_compute_frame_region_change(prev, curr, threshold)
        
        for _ in range(iterations):
            t0 = time.perf_counter()
            self.baseline_compute_frame_region_change(prev, curr, threshold)
            baseline_times.append(time.perf_counter() - t0)
        
        baseline_median = np.median(baseline_times)
        
        # Candidate timing
        candidate_times = []
        for _ in range(5):  # Warm up
            self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        for _ in range(iterations):
            t0 = time.perf_counter()
            self.candidate_compute_frame_region_change(prev, curr, threshold)
            candidate_times.append(time.perf_counter() - t0)
        
        candidate_median = np.median(candidate_times)
        
        # Calculate speedup
        speedup = (baseline_median - candidate_median) / baseline_median
        speedup_pct = speedup * 100
        
        print(f"\n  Baseline median: {baseline_median*1e6:.2f} µs")
        print(f"  Candidate median: {candidate_median*1e6:.2f} µs")
        print(f"  Speedup: {speedup_pct:.1f}%")
        
        # SC-005: require ≥20% improvement
        assert speedup >= 0.20, f"Speedup {speedup_pct:.1f}% < 20% (SC-005 FAIL)"


class TestNormalizationPerformance:
    """Verify normalization precompile performance proxy (FR-007)."""

    @staticmethod
    def baseline_normalize_for_matching(text: str) -> str:
        text = (text or "").replace("\n", " ").replace("\r", " ")
        return re.sub(r"\s+", " ", text).strip()

    def test_normalization_precompile_proxy_fr007(self):
        """FR-007 proxy: 10k candidate calls <= baseline and 0 compile calls in candidate batch."""
        test_inputs = [
            "hello  world",
            "line1\nline2",
            "multi\t\tspace",
            "  leading",
            "trailing  ",
            "\u00A0unicode\u00A0space\u00A0",
        ] * (10_000 // 6 + 1)
        test_inputs = test_inputs[:10_000]

        for text in test_inputs[:100]:
            self.baseline_normalize_for_matching(text)
            OCRService.normalize_for_matching(text)

        baseline_start = time.perf_counter()
        for text in test_inputs:
            self.baseline_normalize_for_matching(text)
        baseline_elapsed = time.perf_counter() - baseline_start

        compile_calls = 0
        original_compile = re.compile

        def counting_compile(*args, **kwargs):
            nonlocal compile_calls
            compile_calls += 1
            return original_compile(*args, **kwargs)

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(re, "compile", counting_compile)
            candidate_start = time.perf_counter()
            for text in test_inputs:
                OCRService.normalize_for_matching(text)
            candidate_elapsed = time.perf_counter() - candidate_start

        print(f"\n  Baseline batch: {baseline_elapsed*1000:.2f} ms")
        print(f"  Candidate batch: {candidate_elapsed*1000:.2f} ms")
        print(f"  re.compile calls during candidate batch: {compile_calls}")

        assert compile_calls == 0, f"Expected 0 re.compile calls, got {compile_calls}"
        assert candidate_elapsed <= baseline_elapsed, (
            f"Candidate slower than baseline: {candidate_elapsed:.6f}s > {baseline_elapsed:.6f}s"
        )


class TestAnalyzeTotalRuntimePerformance:
    """SC-001: end-to-end analyze runtime gate with mocked services."""

    @staticmethod
    def _build_frames(frame_count: int = 100) -> list[tuple[float, np.ndarray]]:
        base = gating_frames.multichannel_bgr_frame()
        frames: list[tuple[float, np.ndarray]] = []
        for idx in range(frame_count):
            frame = np.copy(base)
            if idx % 25 == 0:
                frame[0:8, 0:8, :] = (idx % 255)
            frames.append((float(idx) * 0.1, frame))
        return frames

    @staticmethod
    def _make_service(frames: list[tuple[float, np.ndarray]]) -> AnalysisService:
        class VideoServiceStub:
            @staticmethod
            def iterate_frames_with_timestamps(url, start_time, end_time, fps, quality="best"):
                for item in frames:
                    yield item

        class OCRServiceStub:
            @staticmethod
            def detect_text(frame, region):
                return ["PLAYER 1"]

            @staticmethod
            def extract_candidates(tokens, patterns=None, filter_non_matching=False, tolerance_threshold=0.75):
                return []

        return AnalysisService(VideoServiceStub(), OCRServiceStub())

    @staticmethod
    def _patch_baseline_paths(service: AnalysisService) -> None:
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

    def test_total_runtime_speedup_sc001(self):
        """SC-001: candidate median runtime is >=15% faster than baseline median.

        Uses 4 regions x 100 frames and compares baseline-patched vs candidate service.
        Skips on high environment variance (>10%).
        """
        regions = [
            (0, 0, 64, 64),
            (64, 0, 64, 64),
            (0, 64, 64, 64),
            (64, 64, 64, 64),
        ]

        baseline_runs: list[float] = []
        candidate_runs: list[float] = []

        # Warm-up both code paths to reduce first-run noise from import/cache effects.
        warmup_frames = self._build_frames(100)
        warmup_baseline = self._make_service(warmup_frames)
        self._patch_baseline_paths(warmup_baseline)
        warmup_baseline.analyze(
            url="mock://video",
            regions=regions,
            start_time=0.0,
            end_time=10.0,
            fps=10,
            gating_enabled=True,
        )

        warmup_frames = self._build_frames(100)
        warmup_candidate = self._make_service(warmup_frames)
        warmup_candidate.analyze(
            url="mock://video",
            regions=regions,
            start_time=0.0,
            end_time=10.0,
            fps=10,
            gating_enabled=True,
        )

        for _ in range(7):
            frames = self._build_frames(100)
            baseline_service = self._make_service(frames)
            self._patch_baseline_paths(baseline_service)
            t0 = time.perf_counter()
            baseline_service.analyze(
                url="mock://video",
                regions=regions,
                start_time=0.0,
                end_time=10.0,
                fps=10,
                gating_enabled=True,
            )
            baseline_runs.append(time.perf_counter() - t0)

        for _ in range(7):
            frames = self._build_frames(100)
            candidate_service = self._make_service(frames)
            t0 = time.perf_counter()
            candidate_service.analyze(
                url="mock://video",
                regions=regions,
                start_time=0.0,
                end_time=10.0,
                fps=10,
                gating_enabled=True,
            )
            candidate_runs.append(time.perf_counter() - t0)

        baseline_stable = sorted(baseline_runs)[1:-1]
        candidate_stable = sorted(candidate_runs)[1:-1]

        baseline_median = float(np.median(baseline_stable))
        candidate_median = float(np.median(candidate_stable))
        speedup = (baseline_median - candidate_median) / baseline_median

        baseline_variance = (max(baseline_stable) - min(baseline_stable)) / baseline_median
        candidate_variance = (max(candidate_stable) - min(candidate_stable)) / candidate_median
        if baseline_variance > 0.10 or candidate_variance > 0.10:
            pytest.skip(
                f"Environment variance too high (baseline={baseline_variance:.2%}, candidate={candidate_variance:.2%})"
            )

        print(f"\n  Baseline median total runtime: {baseline_median*1000:.2f} ms")
        print(f"  Candidate median total runtime: {candidate_median*1000:.2f} ms")
        print(f"  Total runtime speedup: {speedup*100:.1f}%")

        assert speedup >= 0.15, f"SC-001 failed: speedup {speedup*100:.1f}% < 15%"


class TestTimingInstrumentationOverhead:
    """SC-013: timing instrumentation overhead remains <=2%."""

    @staticmethod
    def _build_frames(frame_count: int = 160) -> list[tuple[float, np.ndarray]]:
        base = gating_frames.multichannel_bgr_frame()
        frames: list[tuple[float, np.ndarray]] = []
        for idx in range(frame_count):
            frame = np.copy(base)
            if idx % 20 == 0:
                frame[0:16, 0:16, :] = (idx % 255)
            frames.append((idx * 0.05, frame))
        return frames

    @staticmethod
    def _make_service(frames: list[tuple[float, np.ndarray]]) -> AnalysisService:
        class VideoServiceStub:
            @staticmethod
            def iterate_frames_with_timestamps(url, start_time, end_time, fps, quality="best"):
                for item in frames:
                    yield item

        class OCRServiceStub:
            @staticmethod
            def detect_text(frame, region):
                # Representative OCR-like CPU work to avoid overstating timer overhead.
                arr = frame[0:32, 0:32, :].astype(np.float32)
                _ = float(np.mean(arr) + np.std(arr))
                return ["PLAYER 1", "PLAYER 2"]

            @staticmethod
            def extract_candidates(tokens, patterns=None, filter_non_matching=False, tolerance_threshold=0.75):
                return []

        return AnalysisService(VideoServiceStub(), OCRServiceStub())

    @staticmethod
    def _measure_runs(logging_enabled: bool, runs: int = 7) -> tuple[float, float]:
        timings: list[float] = []
        for _ in range(runs):
            frames = TestTimingInstrumentationOverhead._build_frames()
            service = TestTimingInstrumentationOverhead._make_service(frames)
            t0 = time.perf_counter()
            service.analyze(
                url="mock://video",
                regions=[(0, 0, 64, 64), (64, 64, 64, 64)],
                start_time=0.0,
                end_time=8.0,
                fps=20,
                logging_enabled=logging_enabled,
                gating_enabled=True,
            )
            timings.append(time.perf_counter() - t0)

        stable = sorted(timings)[1:-1]
        median = float(np.median(stable))
        variance = (max(stable) - min(stable)) / median if median > 0 else 0.0
        return median, variance

    def test_sc013_timing_instrumentation_overhead(self):
        """SC-013 protocol: warmup, 7 measured runs, median compare, variance retry."""
        warmup_frames = self._build_frames(120)
        self._make_service(warmup_frames).analyze(
            url="mock://video",
            regions=[(0, 0, 64, 64), (64, 64, 64, 64)],
            start_time=0.0,
            end_time=6.0,
            fps=20,
            logging_enabled=False,
            gating_enabled=True,
        )
        self._make_service(warmup_frames).analyze(
            url="mock://video",
            regions=[(0, 0, 64, 64), (64, 64, 64, 64)],
            start_time=0.0,
            end_time=6.0,
            fps=20,
            logging_enabled=True,
            gating_enabled=True,
        )

        no_instr_median, no_instr_var = self._measure_runs(logging_enabled=False)
        instr_median, instr_var = self._measure_runs(logging_enabled=True)

        if no_instr_var > 0.10 or instr_var > 0.10:
            no_instr_median, no_instr_var = self._measure_runs(logging_enabled=False)
            instr_median, instr_var = self._measure_runs(logging_enabled=True)
            if no_instr_var > 0.10 or instr_var > 0.10:
                pytest.skip(
                    "SC-013 inconclusive due to sustained benchmark variance "
                    f"(no-instr={no_instr_var:.2%}, instr={instr_var:.2%})"
                )

        overhead = (instr_median - no_instr_median) / no_instr_median if no_instr_median > 0 else 0.0

        print(f"\n  No instrumentation median: {no_instr_median*1000:.2f} ms")
        print(f"  Instrumentation median: {instr_median*1000:.2f} ms")
        print(f"  Instrumentation overhead: {overhead*100:.2f}%")

        assert overhead <= 0.02, f"SC-013 failed: instrumentation overhead {overhead*100:.2f}% > 2.00%"
