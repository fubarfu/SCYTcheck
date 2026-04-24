from __future__ import annotations

from pathlib import Path

from src.web.app.settings_store import SettingsStore


def test_settings_put_and_get_roundtrip(tmp_path: Path) -> None:
    store = SettingsStore(settings_path=tmp_path / "settings.json")
    saved = store.save({"theme": "dark", "ocr_sensitivity": 70})
    assert saved["theme"] == "dark"
    loaded = store.load()
    assert loaded["ocr_sensitivity"] == 70


def test_settings_partial_update_preserves_prior_values(tmp_path: Path) -> None:
    store = SettingsStore(settings_path=tmp_path / "settings.json")
    store.save({"theme": "dark", "ocr_sensitivity": 70, "matching_tolerance": 80})
    updated = store.save({"matching_tolerance": 65})
    assert updated["theme"] == "dark"
    assert updated["matching_tolerance"] == 65
