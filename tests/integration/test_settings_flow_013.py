from __future__ import annotations

from pathlib import Path

from src.web.api.routes.settings import SettingsHandler
from src.web.app.settings_store import SettingsStore


def test_settings_validate_and_save_flow(tmp_path: Path) -> None:
    handler = SettingsHandler(store=SettingsStore(settings_path=tmp_path / "settings.json"))

    target = tmp_path / "target-project-root"

    validate_status, validate_body = handler.post_validate_settings({"project_location": str(target)})
    assert validate_status == 200
    assert validate_body["location_status"] == "valid"

    save_status, save_body = handler.put_settings({"project_location": str(target)})
    assert save_status == 200
    assert save_body["project_location"] == str(target)
    assert save_body["location_status"] == "valid"


def test_settings_put_rejects_empty_location(tmp_path: Path) -> None:
    handler = SettingsHandler(store=SettingsStore(settings_path=tmp_path / "settings.json"))

    status, body = handler.put_settings({"project_location": ""})
    assert status == 422
    assert body["error"] == "invalid_project_location"
