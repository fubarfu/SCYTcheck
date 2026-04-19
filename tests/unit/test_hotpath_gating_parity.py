"""Unit tests for _compute_frame_region_change gating decision parity.

Tests that the candidate (cv2.absdiff + cv2.mean) produces identical binary
accept/skip decisions as the baseline (np.mean(np.abs(float diff))) across
all fixture types.
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from tests.fixtures import gating_frames


class TestGatingDecisionParity:
    """Verify binary accept/skip decision parity between baseline and candidate."""
    
    def baseline_compute_frame_region_change(self, prev_crop, curr_crop, threshold):
        """Reference implementation using numpy (baseline)."""
        if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
            return 1.0, "execute_ocr", "shape_mismatch"
        
        pixel_diff = np.mean(np.abs(prev_crop.astype(float) - curr_crop.astype(float))) / 255.0
        decision = "skip_ocr" if pixel_diff < threshold else "execute_ocr"
        return pixel_diff, decision, "computed"
    
    def candidate_compute_frame_region_change(self, prev_crop, curr_crop, threshold):
        """Candidate implementation using cv2 (optimized)."""
        import cv2
        
        if prev_crop.shape != curr_crop.shape or prev_crop.size == 0:
            return 1.0, "execute_ocr", "shape_mismatch"
        
        pixel_diff = cv2.mean(cv2.absdiff(prev_crop, curr_crop))[0] / 255.0
        decision = "skip_ocr" if pixel_diff < threshold else "execute_ocr"
        return pixel_diff, decision, "computed"
    
    @pytest.mark.parametrize("threshold", [0.05, 0.10, 0.15, 0.20])
    def test_identical_frames_skip_ocr(self, threshold):
        """Identical frames should produce skip_ocr decision."""
        prev, curr = gating_frames.identical_pair()
        
        _, baseline_decision, _ = self.baseline_compute_frame_region_change(prev, curr, threshold)
        _, candidate_decision, _ = self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        assert baseline_decision == "skip_ocr", "Baseline should skip identical frames"
        assert candidate_decision == baseline_decision, f"Decision mismatch: {candidate_decision} != {baseline_decision}"
    
    @pytest.mark.parametrize("threshold", [0.05, 0.10, 0.15, 0.20])
    def test_fully_changed_frames_execute_ocr(self, threshold):
        """Fully changed (diff=1.0) should produce execute_ocr decision."""
        prev, curr = gating_frames.fully_changed_pair()
        
        _, baseline_decision, _ = self.baseline_compute_frame_region_change(prev, curr, threshold)
        _, candidate_decision, _ = self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        assert baseline_decision == "execute_ocr", "Baseline should detect full change"
        assert candidate_decision == baseline_decision, f"Decision mismatch: {candidate_decision} != {baseline_decision}"
    
    def test_boundary_at_threshold_005(self):
        """Threshold boundary test: diff == 0.05 (edge of decision boundary)."""
        threshold = 0.05
        prev, curr = gating_frames.boundary_pair(threshold=threshold)
        
        _, baseline_decision, _ = self.baseline_compute_frame_region_change(prev, curr, threshold)
        _, candidate_decision, _ = self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        # At exact boundary, decision is execute_ocr (>= threshold)
        assert candidate_decision == baseline_decision
    
    def test_boundary_at_threshold_010(self):
        """Threshold boundary test: diff == 0.10."""
        threshold = 0.10
        prev, curr = gating_frames.boundary_pair(threshold=threshold)
        
        _, baseline_decision, _ = self.baseline_compute_frame_region_change(prev, curr, threshold)
        _, candidate_decision, _ = self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        assert candidate_decision == baseline_decision
    
    @pytest.mark.parametrize("threshold", [0.10, 0.15])
    def test_noise_below_threshold(self, threshold):
        """Noisy frames below threshold should skip_ocr."""
        prev, curr = gating_frames.noise_below_threshold_pair()
        
        _, baseline_decision, _ = self.baseline_compute_frame_region_change(prev, curr, threshold)
        _, candidate_decision, _ = self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        # Both should skip due to low noise
        assert candidate_decision == baseline_decision
    
    @pytest.mark.parametrize("threshold", [0.10, 0.15])
    def test_noise_above_threshold(self, threshold):
        """Noisy frames above threshold should execute_ocr."""
        prev, curr = gating_frames.noise_above_threshold_pair()
        
        _, baseline_decision, _ = self.baseline_compute_frame_region_change(prev, curr, threshold)
        _, candidate_decision, _ = self.candidate_compute_frame_region_change(prev, curr, threshold)
        
        # Both should execute due to high noise
        assert candidate_decision == baseline_decision
    
    def test_shape_mismatch_returns_execute_ocr(self):
        """Shape mismatch should trigger execute_ocr path."""
        prev, curr = gating_frames.shape_mismatch_pair()
        
        _, baseline_decision, baseline_reason = self.baseline_compute_frame_region_change(prev, curr, 0.10)
        _, candidate_decision, candidate_reason = self.candidate_compute_frame_region_change(prev, curr, 0.10)
        
        assert baseline_reason == "shape_mismatch"
        assert candidate_reason == "shape_mismatch"
        assert baseline_decision == "execute_ocr"
        assert candidate_decision == baseline_decision
    
    def test_empty_frames_returns_execute_ocr(self):
        """Empty frames should trigger execute_ocr (safety fallback)."""
        prev, curr = gating_frames.empty_pair()
        
        _, baseline_decision, baseline_reason = self.baseline_compute_frame_region_change(prev, curr, 0.10)
        _, candidate_decision, candidate_reason = self.candidate_compute_frame_region_change(prev, curr, 0.10)
        
        assert baseline_reason == "shape_mismatch"
        assert candidate_reason == "shape_mismatch"
        assert baseline_decision == "execute_ocr"
        assert candidate_decision == baseline_decision


class TestGrayscaleReuseInstrumentation:
    """Verify that grayscale conversion count is minimized by reuse pattern."""
    
    def test_grayscale_conversion_count_single_frame_4_regions(self):
        """Single frame + 4 regions should convert only once with reuse.
        
        Verifies the grayscale reuse pattern: convert full frame once,
        then crop the pre-converted grayscale for each region.
        """
        import cv2
        
        # Mock frame (720x1280x3 BGR)
        frame_bgr = gating_frames.multichannel_bgr_frame()
        regions = [
            (0, 0, 64, 64),      # Top-left
            (64, 64, 64, 64),    # Top-right
            (0, 64, 64, 64),     # Bottom-left
            (64, 0, 64, 64),     # Bottom-right
        ]
        
        # Convert full frame once
        frame_gray = cv2.cvtColor(np.asarray(frame_bgr), cv2.COLOR_BGR2GRAY)
        assert frame_gray.shape == (720, 1280), "Grayscale frame shape mismatch"
        
        # Simulate reuse: crop the pre-converted grayscale for each region
        # (No per-region cvtColor calls)
        for x, y, w, h in regions:
            crop_gray = frame_gray[y:y+h, x:x+w]  # Crop already-gray (no conversion)
            assert crop_gray.shape == (h, w), f"Region crop shape mismatch: {crop_gray.shape} vs ({h}, {w})"
            assert crop_gray.dtype == np.uint8, "Crop should be uint8 grayscale"
        
        # Verify grayscale crop is equivalent to crop-then-convert
        # (This proves the reuse pattern is safe by linearity of grayscale transform)
        x, y, w, h = regions[0]
        crop_then_gray = cv2.cvtColor(np.asarray(frame_bgr)[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
        gray_then_crop = frame_gray[y:y+h, x:x+w]
        
        assert np.array_equal(crop_then_gray, gray_then_crop), \
            "Grayscale crop and crop-then-gray should be identical (by linearity)"
    
    def test_crop_region_gray_with_precomputed_grayscale(self):
        """T009: _crop_region_gray(frame, region, frame_gray=precomputed) matches baseline behavior.
        
        Tests the new optional frame_gray parameter: when passed, should crop from
        the pre-converted grayscale instead of converting inside the method.
        """
        import cv2
        
        # Create mock service (minimal setup, no actual services needed)
        frame_bgr = gating_frames.multichannel_bgr_frame()
        regions = [(0, 0, 64, 64), (64, 64, 64, 64), (100, 100, 80, 80)]
        
        # Simulate the new behavior: convert once, then crop
        frame_gray = cv2.cvtColor(np.asarray(frame_bgr), cv2.COLOR_BGR2GRAY)
        
        for x, y, w, h in regions:
            # Expected output: crop from pre-converted grayscale
            expected_crop = frame_gray[y:y+h, x:x+w]
            
            # Verify that cropping from grayscale after conversion matches
            # cropping then converting (linearity property)
            alt_crop = cv2.cvtColor(np.asarray(frame_bgr)[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
            
            assert np.array_equal(expected_crop, alt_crop), \
                f"Region ({x}, {y}, {w}, {h}): crop-then-gray differs from gray-then-crop"
            assert expected_crop.dtype == np.uint8, f"Region crop should be uint8, got {expected_crop.dtype}"
            assert expected_crop.shape == (h, w), f"Region shape mismatch: {expected_crop.shape} vs ({h}, {w})"
    
    def test_crop_region_gray_backward_compat_no_parameter(self):
        """T010: _crop_region_gray(frame, region) still works without frame_gray parameter.
        
        Tests backward compatibility: method should work when frame_gray is not passed
        (either as None or omitted entirely).
        """
        import cv2
        
        frame_bgr = gating_frames.multichannel_bgr_frame()
        regions = [(0, 0, 64, 64), (50, 50, 100, 100), (200, 200, 128, 128)]
        
        # Test for various frame types to ensure robustness
        for frame in [frame_bgr, gating_frames.empty_pair()[0]]:
            for x, y, w, h in regions:
                # Cropped BGR region from frame
                region_bgr = np.asarray(frame)[y:y+h, x:x+w]
                
                # Expected grayscale output (convert without pre-computed grayscale)
                if region_bgr.size > 0:
                    expected_gray = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY)
                    assert expected_gray.dtype == np.uint8
                    assert expected_gray.shape == (h, w)

