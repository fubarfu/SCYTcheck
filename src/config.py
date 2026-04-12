from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SETTINGS_FILE = "scytcheck_settings.json"


@dataclass(frozen=True)
class AppConfig:
    sample_fps: int = 1
    confidence_threshold: int = 40
    tesseract_cmd: str | None = None
    tessdata_prefix: str | None = None


def _candidate_tesseract_paths() -> list[Path]:
    candidates: list[Path] = []

    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "tesseract.exe")

    user_profile = os.getenv("USERPROFILE")
    if user_profile:
        candidates.append(
            Path(user_profile) / "scoop" / "apps" / "tesseract" / "current" / "tesseract.exe"
        )

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Tesseract-OCR" / "tesseract.exe")

    for env_key in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.getenv(env_key)
        if base:
            candidates.append(Path(base) / "Tesseract-OCR" / "tesseract.exe")

    return candidates


def _discover_tesseract_command() -> str | None:
    configured = os.getenv("SCYTCHECK_TESSERACT_CMD")
    if configured:
        return configured

    discovered_on_path = shutil.which("tesseract")
    if discovered_on_path:
        return discovered_on_path

    for candidate in _candidate_tesseract_paths():
        if candidate.exists():
            return str(candidate)

    return None


def _discover_tessdata_prefix(tesseract_cmd: str | None) -> str | None:
    configured = os.getenv("TESSDATA_PREFIX")
    if configured:
        return configured

    if not tesseract_cmd:
        return None

    tessdata_dir = Path(tesseract_cmd).resolve().parent / "tessdata"
    if tessdata_dir.exists():
        return str(tessdata_dir)

    return None


@dataclass
class AdvancedSettings:
    context_patterns: list[dict[str, object]]
    filter_non_matching: bool = True
    event_gap_threshold_sec: float = 1.0
    ocr_confidence_threshold: int = 40
    video_quality: str = "best"
    logging_enabled: bool = False


def _default_advanced_settings() -> AdvancedSettings:
    return AdvancedSettings(
        context_patterns=[
            {
                "id": "default-started-by",
                "before_text": "started by",
                "after_text": None,
                "enabled": True,
            },
            {"id": "default-joined", "before_text": None, "after_text": "joined", "enabled": True},
            {
                "id": "default-connected",
                "before_text": None,
                "after_text": "connected",
                "enabled": True,
            },
            {
                "id": "default-disconnected",
                "before_text": None,
                "after_text": "disconnected",
                "enabled": True,
            },
        ],
        filter_non_matching=True,
        event_gap_threshold_sec=1.0,
        ocr_confidence_threshold=40,
        video_quality="best",
        logging_enabled=False,
    )


def load_config() -> AppConfig:
    sample_fps = int(os.getenv("SCYTCHECK_SAMPLE_FPS", "1"))
    confidence_threshold = int(os.getenv("SCYTCHECK_OCR_CONFIDENCE", "40"))
    tesseract_cmd = _discover_tesseract_command()
    tessdata_prefix = _discover_tessdata_prefix(tesseract_cmd)

    return AppConfig(
        sample_fps=max(1, sample_fps),
        confidence_threshold=max(0, min(confidence_threshold, 100)),
        tesseract_cmd=tesseract_cmd,
        tessdata_prefix=tessdata_prefix,
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

    defaults = _default_advanced_settings()
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
        video_quality=str(payload.get("video_quality", defaults.video_quality) or "best"),
        logging_enabled=bool(payload.get("logging_enabled", defaults.logging_enabled)),
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
                "video_quality": settings.video_quality,
                "logging_enabled": settings.logging_enabled,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
