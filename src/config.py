from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

SETTINGS_FILE = "scytcheck_settings.json"
HISTORY_INDEX_FILE = "video_history.json"


@dataclass(frozen=True)
class AppConfig:
    sample_fps: int = 1
    confidence_threshold: int = 40
    paddleocr_model_root: str | None = None


def _candidate_paddleocr_model_roots() -> list[Path]:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        internal_dir = executable_dir / "_internal"
        candidates.append(executable_dir / "paddleocr_models")
        candidates.append(executable_dir / "paddleocr")
        candidates.append(internal_dir / "paddleocr")
        candidates.append(executable_dir / "third_party" / "paddleocr" / "x64")

    repo_root = Path(__file__).resolve().parent.parent
    candidates.append(repo_root / "third_party" / "paddleocr" / "x64")
    candidates.append(Path.cwd() / "third_party" / "paddleocr" / "x64")

    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(candidate)

    return deduped


def _discover_paddleocr_model_root() -> str | None:
    configured = os.getenv("SCYTCHECK_PADDLEOCR_MODEL_ROOT")
    if configured:
        return configured

    for candidate in _candidate_paddleocr_model_roots():
        if candidate.exists() and candidate.is_dir():
            return str(candidate)

    return None


@dataclass
class AdvancedSettings:
    context_patterns: list[dict[str, object]]
    filter_non_matching: bool = True
    event_gap_threshold_sec: float = 1.0
    ocr_confidence_threshold: int = 40
    paddleocr_model_root: str | None = None
    video_quality: str = "best"
    logging_enabled: bool = False
    tolerance_value: float = 0.75
    gating_enabled: bool = False
    gating_threshold: float = 0.02


def default_advanced_settings() -> AdvancedSettings:
    return AdvancedSettings(
        context_patterns=[
            {
                "id": "default-has-joined",
                "before_text": None,
                "after_text": "has joined",
                "enabled": True,
            },
            {
                "id": "default-party-connected",
                "before_text": "Party",
                "after_text": "connected",
                "enabled": True,
            },
            {
                "id": "default-party-disconnected",
                "before_text": "Party",
                "after_text": "disconnected",
                "enabled": True,
            },
            {
                "id": "default-started-by",
                "before_text": "started by",
                "after_text": None,
                "enabled": True,
            },
        ],
        filter_non_matching=True,
        event_gap_threshold_sec=1.0,
        ocr_confidence_threshold=40,
        paddleocr_model_root=_discover_paddleocr_model_root(),
        video_quality="best",
        logging_enabled=False,
        tolerance_value=0.75,
        gating_enabled=False,
        gating_threshold=0.02,
    )


def load_config() -> AppConfig:
    sample_fps = int(os.getenv("SCYTCHECK_SAMPLE_FPS", "1"))
    confidence_threshold = int(os.getenv("SCYTCHECK_OCR_CONFIDENCE", "40"))
    paddleocr_model_root = _discover_paddleocr_model_root()

    return AppConfig(
        sample_fps=max(1, sample_fps),
        confidence_threshold=max(0, min(confidence_threshold, 100)),
        paddleocr_model_root=paddleocr_model_root,
    )


def _settings_path(base_dir: str | None = None) -> Path:
    if base_dir:
        return Path(base_dir) / SETTINGS_FILE

    appdata = os.getenv("APPDATA")
    if appdata:
        appdata_dir = Path(appdata) / "SCYTcheck"
        try:
            appdata_dir.mkdir(parents=True, exist_ok=True)
            test_file = appdata_dir / ".write_test"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            return appdata_dir / SETTINGS_FILE
        except Exception:
            pass

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / SETTINGS_FILE
    return Path.cwd() / SETTINGS_FILE


def history_index_path(base_dir: str | None = None) -> Path:
    """Return persistent path for video history index.

    Uses the same APPDATA/fallback strategy as settings persistence.
    """
    settings_path = _settings_path(base_dir)
    return settings_path.with_name(HISTORY_INDEX_FILE)


def load_advanced_settings(base_dir: str | None = None) -> AdvancedSettings:
    """Load persisted advanced settings or initialize defaults on first run."""
    path = _settings_path(base_dir)
    if not path.exists():
        defaults = default_advanced_settings()
        save_advanced_settings(defaults, base_dir)
        return defaults

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        defaults = default_advanced_settings()
        save_advanced_settings(defaults, base_dir)
        return defaults

    if not isinstance(payload, dict):
        payload = {}

    defaults = default_advanced_settings()
    return AdvancedSettings(
        context_patterns=list(payload.get("context_patterns", defaults.context_patterns)),
        filter_non_matching=bool(payload.get("filter_non_matching", defaults.filter_non_matching)),
        event_gap_threshold_sec=float(
            payload.get("event_gap_threshold_sec", defaults.event_gap_threshold_sec)
        ),
        ocr_confidence_threshold=int(
            max(
                0,
                min(
                    int(payload.get("ocr_confidence_threshold", defaults.ocr_confidence_threshold)),
                    100,
                ),
            )
        ),
        paddleocr_model_root=(
            str(payload["paddleocr_model_root"])
            if payload.get("paddleocr_model_root") not in (None, "")
            else defaults.paddleocr_model_root
        ),
        video_quality=str(payload.get("video_quality", defaults.video_quality) or "best"),
        logging_enabled=bool(payload.get("logging_enabled", defaults.logging_enabled)),
        tolerance_value=float(
            max(0.60, min(float(payload.get("tolerance_value", defaults.tolerance_value)), 0.95))
        ),
        gating_enabled=bool(payload.get("gating_enabled", defaults.gating_enabled)),
        gating_threshold=float(
            max(
                0.0,
                min(float(payload.get("gating_threshold", defaults.gating_threshold)), 1.0),
            )
        ),
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
                "ocr_confidence_threshold": int(
                    max(0, min(settings.ocr_confidence_threshold, 100))
                ),
                "paddleocr_model_root": settings.paddleocr_model_root,
                "video_quality": settings.video_quality,
                "logging_enabled": settings.logging_enabled,
                "tolerance_value": float(max(0.60, min(settings.tolerance_value, 0.95))),
                "gating_enabled": settings.gating_enabled,
                "gating_threshold": float(max(0.0, min(settings.gating_threshold, 1.0))),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
