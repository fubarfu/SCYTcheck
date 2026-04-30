from __future__ import annotations

import json
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


def test_settings_get_backfills_new_default_context_pattern(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    legacy_payload = {
        "context_patterns": [
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
        ]
    }
    settings_path.write_text(json.dumps(legacy_payload), encoding="utf-8")
    handler = SettingsHandler(store=SettingsStore(settings_path=settings_path))

    payload = handler.get_settings()

    context_patterns = payload.get("context_patterns", [])
    assert len(context_patterns) == 5
    assert any(
        pattern.get("id") == "default-party-bracket-colon"
        and pattern.get("before_text") == "Party]"
        and pattern.get("after_text") == ":"
        for pattern in context_patterns
    )
