from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.config import default_advanced_settings, default_project_location
DEFAULT_SETTINGS_FILENAME = "scytcheck_settings.json"


class SettingsStore:
    """Persistence adapter for reading and writing SCYTcheck settings."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self.settings_path = settings_path or self._resolve_default_settings_path()

    @staticmethod
    def _resolve_default_settings_path() -> Path:
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "SCYTcheck" / DEFAULT_SETTINGS_FILENAME
        return Path(DEFAULT_SETTINGS_FILENAME)

    def load(self) -> dict[str, Any]:
        defaults = self._default_settings_payload()
        self._ensure_default_project_location(defaults)
        if not self.settings_path.exists():
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            with self.settings_path.open("w", encoding="utf-8") as handle:
                json.dump(defaults, handle, ensure_ascii=True, indent=2)
            return defaults
        with self.settings_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if not isinstance(data, dict):
                return defaults
            merged = self._deep_merge(defaults, data)
            self._ensure_default_project_location(merged)
            return merged

    def save(self, partial_update: dict[str, Any]) -> dict[str, Any]:
        current = self.load()
        merged = self._deep_merge(current, partial_update)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.settings_path.open("w", encoding="utf-8") as handle:
            json.dump(merged, handle, ensure_ascii=True, indent=2)
        return merged

    def _deep_merge(self, base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base)
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                merged[key] = self._deep_merge(base[key], value)
            else:
                merged[key] = value
        return merged

    @staticmethod
    def _ensure_default_project_location(settings: dict[str, Any]) -> None:
        project_location = str(settings.get("project_location", "")).strip()
        if not project_location:
            project_location = str(default_project_location())
            settings["project_location"] = project_location
        Path(project_location).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _default_settings_payload() -> dict[str, Any]:
        advanced = default_advanced_settings()
        return {
            "video_quality": advanced.video_quality,
            "ocr_confidence_threshold": advanced.ocr_confidence_threshold,
            "tolerance_value": advanced.tolerance_value,
            "event_gap_threshold_sec": advanced.event_gap_threshold_sec,
            "gating_enabled": advanced.gating_enabled,
            "gating_threshold": advanced.gating_threshold,
            "filter_non_matching": advanced.filter_non_matching,
            "logging_enabled": advanced.logging_enabled,
            "context_patterns": list(advanced.context_patterns),
            "project_location": advanced.project_location or str(default_project_location()),
        }
