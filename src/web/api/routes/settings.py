from __future__ import annotations

from src.web.app.settings_store import SettingsStore


class SettingsHandler:
    """HTTP-style handler wrapping SettingsStore for API routes."""

    def __init__(self, store: SettingsStore | None = None) -> None:
        self.store = store or SettingsStore()

    def get_settings(self) -> dict:
        return self.store.load()

    def put_settings(self, partial_update: dict) -> tuple[int, dict]:
        allowed_types = {str, int, float, bool, list, type(None)}
        for key, value in partial_update.items():
            if type(value) not in allowed_types and not isinstance(value, dict):
                return 400, {"error": "validation_error", "message": f"Invalid type for '{key}'"}
        merged = self.store.save(partial_update)
        return 200, merged
