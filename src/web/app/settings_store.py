from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

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
        if not self.settings_path.exists():
            return {}
        with self.settings_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
            if not isinstance(data, dict):
                return {}
            return data

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
