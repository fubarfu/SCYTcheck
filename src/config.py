from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    sample_fps: int = 1
    confidence_threshold: int = 40
    tesseract_cmd: str | None = None


def load_config() -> AppConfig:
    sample_fps = int(os.getenv("SCYTCHECK_SAMPLE_FPS", "1"))
    confidence_threshold = int(os.getenv("SCYTCHECK_OCR_CONFIDENCE", "40"))
    tesseract_cmd = os.getenv("SCYTCHECK_TESSERACT_CMD")

    return AppConfig(
        sample_fps=max(1, sample_fps),
        confidence_threshold=max(0, min(confidence_threshold, 100)),
        tesseract_cmd=tesseract_cmd,
    )
