from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


SETTINGS_FILE = "scytcheck_settings.json"


@dataclass(frozen=True)
class AppConfig:
    sample_fps: int = 1
    confidence_threshold: int = 40
    tesseract_cmd: str | None = None


@dataclass
class AdvancedSettings:
    context_patterns: list[dict[str, object]]
    filter_non_matching: bool = False
    event_gap_threshold_sec: float = 1.0


def _default_advanced_settings() -> AdvancedSettings:
    return AdvancedSettings(
        context_patterns=[
            {"id": "default-joined", "before_text": None, "after_text": "joined", "enabled": True},
            {
                "id": "default-connected",
                "before_text": None,
                "after_text": "connected",
                "enabled": True,
            },
        ],
        filter_non_matching=False,
        event_gap_threshold_sec=1.0,
    )


def load_config() -> AppConfig:
    sample_fps = int(os.getenv("SCYTCHECK_SAMPLE_FPS", "1"))
    confidence_threshold = int(os.getenv("SCYTCHECK_OCR_CONFIDENCE", "40"))
    tesseract_cmd = os.getenv("SCYTCHECK_TESSERACT_CMD")

    return AppConfig(
        sample_fps=max(1, sample_fps),
        confidence_threshold=max(0, min(confidence_threshold, 100)),
        tesseract_cmd=tesseract_cmd,
    )


def _settings_path(base_dir: str | None = None) -> Path:
    root = Path(base_dir) if base_dir else Path.cwd()
    return root / SETTINGS_FILE


def load_advanced_settings(base_dir: str | None = None) -> AdvancedSettings:
    """Load persisted advanced settings or initialize defaults on first run."""
    path = _settings_path(base_dir)
    if not path.exists():
        defaults = _default_advanced_settings()
        save_advanced_settings(defaults, base_dir)
        return defaults

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        defaults = _default_advanced_settings()
        save_advanced_settings(defaults, base_dir)
        return defaults

    return AdvancedSettings(
        context_patterns=list(payload.get("context_patterns", _default_advanced_settings().context_patterns)),
        filter_non_matching=bool(payload.get("filter_non_matching", False)),
        event_gap_threshold_sec=float(payload.get("event_gap_threshold_sec", 1.0)),
    )


def save_advanced_settings(settings: AdvancedSettings, base_dir: str | None = None) -> None:
    """Persist advanced settings for next app startup."""
    path = _settings_path(base_dir)
    path.write_text(
        json.dumps(
            {
                "context_patterns": settings.context_patterns,
                "filter_non_matching": settings.filter_non_matching,
                "event_gap_threshold_sec": settings.event_gap_threshold_sec,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
