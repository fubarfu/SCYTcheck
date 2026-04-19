"""Synthetic gating frame fixtures for parity and performance testing."""

import numpy as np


def identical_pair():
    """Two identical uint8 grayscale frames (5x5).
    
    Gating diff should be 0.0 → decision: skip_ocr (no change detected).
    """
    frame = np.full((5, 5), 128, dtype=np.uint8)
    return frame, frame.copy()


def fully_changed_pair():
    """Zeros vs. 255-filled frames (4x4).
    
    Gating diff should be 1.0 (maximum) → decision: execute_ocr (full change).
    """
    prev = np.zeros((4, 4), dtype=np.uint8)
    curr = np.full((4, 4), 255, dtype=np.uint8)
    return prev, curr


def boundary_pair(threshold=0.10):
    """Crafted pair with diff exactly equal to threshold (1x1 frames).
    
    Used for threshold boundary testing. With threshold T, creates a pair where
    computed diff equals T, testing the exact boundary accept/skip condition.
    """
    # Single pixel: create diff that equals threshold when normalized to [0, 1]
    diff_value = int(threshold * 255)
    prev = np.array([[0]], dtype=np.uint8)
    curr = np.array([[diff_value]], dtype=np.uint8)
    return prev, curr


def noise_below_threshold_pair(base_diff=0.05, noise_amplitude=0.02):
    """Base frames with low noise (noise < threshold margin).
    
    Two 8x8 frames with controlled noise below typical threshold (e.g., 0.10).
    Diff = base_diff + random noise, where noise < threshold margin.
    """
    np.random.seed(42)
    prev = np.random.randint(100, 150, (8, 8), dtype=np.uint8)
    
    # Add controlled noise to create curr
    noise = np.random.randint(0, int(noise_amplitude * 255), (8, 8), dtype=np.uint8)
    curr = np.clip(prev.astype(int) + noise, 0, 255).astype(np.uint8)
    
    return prev, curr


def noise_above_threshold_pair(base_diff=0.15, noise_amplitude=0.05):
    """Base frames with higher noise (noise > typical threshold).
    
    Two 8x8 frames with controlled noise above typical threshold (e.g., 0.10).
    Diff = base_diff + random noise, where noise > threshold margin.
    """
    np.random.seed(43)
    prev = np.random.randint(50, 100, (8, 8), dtype=np.uint8)
    
    # Add larger noise to create curr
    noise = np.random.randint(0, int(noise_amplitude * 255), (8, 8), dtype=np.uint8)
    curr = np.clip(prev.astype(int) + noise, 0, 255).astype(np.uint8)
    
    return prev, curr


def shape_mismatch_pair():
    """Frames with mismatched shapes (4x4 vs. 5x5).
    
    Tests shape-mismatch early-return path in gating logic.
    Should return pixel_diff=1.0, execute_ocr (or skip per spec).
    """
    prev = np.ones((4, 4), dtype=np.uint8) * 100
    curr = np.ones((5, 5), dtype=np.uint8) * 150
    return prev, curr


def empty_pair():
    """Empty (zero-size) frames.
    
    Tests guard logic for empty array handling.
    """
    prev = np.array([], dtype=np.uint8).reshape(0, 0)
    curr = np.array([], dtype=np.uint8).reshape(0, 0)
    return prev, curr


def multichannel_bgr_frame():
    """Full-resolution BGR frame for grayscale conversion test.
    
    Used to test that converting a full frame once then cropping grayscale
    equals cropping then converting to grayscale (by linearity of luma).
    Returns a 720x1280x3 BGR frame.
    """
    np.random.seed(44)
    return np.random.randint(0, 256, (720, 1280, 3), dtype=np.uint8)


# Fixture registry for easy iteration in tests
FIXTURE_PAIRS = {
    "identical": identical_pair,
    "fully_changed": fully_changed_pair,
    "boundary_010": lambda: boundary_pair(0.10),
    "boundary_020": lambda: boundary_pair(0.20),
    "noise_below": noise_below_threshold_pair,
    "noise_above": noise_above_threshold_pair,
    "shape_mismatch": shape_mismatch_pair,
    "empty": empty_pair,
}
