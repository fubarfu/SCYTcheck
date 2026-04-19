from __future__ import annotations

import json
from pathlib import Path

from src.config import AdvancedSettings, load_advanced_settings, load_config, save_advanced_settings


def test_load_config_prefers_explicit_paddle_model_root_env(monkeypatch) -> None:
    monkeypatch.setenv("SCYTCHECK_PADDLEOCR_MODEL_ROOT", r"C:\models\paddle")
    monkeypatch.setenv("SCYTCHECK_SAMPLE_FPS", "2")
    monkeypatch.setenv("SCYTCHECK_OCR_CONFIDENCE", "55")

    config = load_config()

    assert config.sample_fps == 2
    assert config.confidence_threshold == 55
    assert config.paddleocr_model_root == r"C:\models\paddle"


def test_load_config_discovers_bundled_paddle_models_in_frozen_layout(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SCYTCHECK_PADDLEOCR_MODEL_ROOT", raising=False)

    app_dir = tmp_path / "SCYTcheck"
    app_dir.mkdir(parents=True)
    app_executable = app_dir / "SCYTcheck.exe"
    app_executable.write_text("", encoding="utf-8")
    model_root = app_dir / "paddleocr"
    model_root.mkdir(parents=True)

    monkeypatch.setattr("src.config.sys.frozen", True, raising=False)
    monkeypatch.setattr("src.config.sys.executable", str(app_executable), raising=False)
    config = load_config()

    assert config.paddleocr_model_root == str(model_root)


def test_load_config_discovers_bundled_paddle_models_in_internal_layout(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SCYTCHECK_PADDLEOCR_MODEL_ROOT", raising=False)

    app_dir = tmp_path / "SCYTcheck"
    app_dir.mkdir(parents=True)
    app_executable = app_dir / "SCYTcheck.exe"
    app_executable.write_text("", encoding="utf-8")
    model_root = app_dir / "_internal" / "paddleocr"
    model_root.mkdir(parents=True)

    monkeypatch.setattr("src.config.sys.frozen", True, raising=False)
    monkeypatch.setattr("src.config.sys.executable", str(app_executable), raising=False)
    config = load_config()

    assert config.paddleocr_model_root == str(model_root)


def test_advanced_settings_roundtrip_includes_video_quality_and_logging(tmp_path: Path) -> None:
    settings = AdvancedSettings(
        context_patterns=[
            {"id": "p1", "before_text": None, "after_text": "joined", "enabled": True}
        ],
        filter_non_matching=False,
        event_gap_threshold_sec=2.0,
        ocr_confidence_threshold=33,
        video_quality="720p",
        logging_enabled=True,
    )

    save_advanced_settings(settings, base_dir=str(tmp_path))
    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.video_quality == "720p"
    assert loaded.logging_enabled is True
    assert loaded.event_gap_threshold_sec == 2.0
    assert loaded.ocr_confidence_threshold == 33


def test_load_advanced_settings_ignores_unknown_fields(tmp_path: Path) -> None:
    payload = {
        "ocr_confidence_threshold": 41,
        "obsolete_field": "legacy-value",
        "paddleocr_model_root": "C:/models/paddle",
    }
    settings_file = tmp_path / "scytcheck_settings.json"
    settings_file.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.ocr_confidence_threshold == 41
    assert loaded.paddleocr_model_root == "C:/models/paddle"


def test_advanced_settings_roundtrip_persists_tolerance_value(tmp_path: Path) -> None:
    settings = AdvancedSettings(
        context_patterns=[],
        tolerance_value=0.61,
    )

    save_advanced_settings(settings, base_dir=str(tmp_path))
    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.tolerance_value == 0.61


def test_advanced_settings_roundtrip_persists_gating_enabled(tmp_path: Path) -> None:
    settings = AdvancedSettings(
        context_patterns=[],
        gating_enabled=False,
    )

    save_advanced_settings(settings, base_dir=str(tmp_path))
    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.gating_enabled is False


def test_advanced_settings_roundtrip_persists_gating_threshold(tmp_path: Path) -> None:
    settings = AdvancedSettings(
        context_patterns=[],
        gating_threshold=0.33,
    )

    save_advanced_settings(settings, base_dir=str(tmp_path))
    loaded = load_advanced_settings(base_dir=str(tmp_path))

    assert loaded.gating_threshold == 0.33
