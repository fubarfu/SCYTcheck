from __future__ import annotations

import os
from pathlib import Path

from src.web.app.settings_store import SettingsStore


class SettingsHandler:
    """HTTP-style handler wrapping SettingsStore for API routes."""

    def __init__(self, store: SettingsStore | None = None) -> None:
        self.store = store or SettingsStore()

    def get_settings(self) -> dict:
        payload = self.store.load()
        project_location = str(payload.get("project_location", "")).strip()
        payload["location_status"] = self._location_status(project_location)
        return payload

    def put_settings(self, partial_update: dict) -> tuple[int, dict]:
        allowed_types = {str, int, float, bool, list, type(None)}
        for key, value in partial_update.items():
            if type(value) not in allowed_types and not isinstance(value, dict):
                return 400, {"error": "validation_error", "message": f"Invalid type for '{key}'"}

        project_location = str(partial_update.get("project_location", "")).strip()
        if "project_location" in partial_update:
            status, message = self._validate_project_location(project_location)
            if status != "valid":
                return 422, {
                    "error": "invalid_project_location",
                    "message": message,
                    "location_status": status,
                }
            partial_update["project_location"] = project_location

        merged = self.store.save(partial_update)
        merged["location_status"] = self._location_status(str(merged.get("project_location", "")))
        return 200, merged

    def post_validate_settings(self, payload: dict) -> tuple[int, dict]:
        project_location = str(payload.get("project_location", "")).strip()
        status, message = self._validate_project_location(project_location)
        return 200, {
            "project_location": project_location,
            "location_status": status,
            "message": message,
        }

    @staticmethod
    def _location_status(project_location: str) -> str:
        path = Path(project_location)
        if not project_location:
            return "missing"
        if not path.exists():
            return "missing"
        if not os.access(path, os.W_OK):
            return "unwritable"
        return "valid"

    @staticmethod
    def _validate_project_location(project_location: str) -> tuple[str, str]:
        if not project_location:
            return "missing", "Project location cannot be empty."

        path = Path(project_location)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception:
            return "missing", f"Path {project_location} does not exist and could not be created."

        if not os.access(path, os.W_OK):
            return "unwritable", f"Path {project_location} is not writable."

        return "valid", "Project location is valid and writable."
