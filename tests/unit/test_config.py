from __future__ import annotations

from pathlib import Path

from src.config import AdvancedSettings, load_advanced_settings, load_config, save_advanced_settings


def test_load_config_prefers_explicit_tesseract_env(monkeypatch) -> None:
    monkeypatch.setenv("SCYTCHECK_TESSERACT_CMD", r"C:\custom\tesseract.exe")
    monkeypatch.setenv("TESSDATA_PREFIX", r"C:\custom\tessdata")
    monkeypatch.setenv("SCYTCHECK_SAMPLE_FPS", "2")
    monkeypatch.setenv("SCYTCHECK_OCR_CONFIDENCE", "55")

    config = load_config()

    assert config.sample_fps == 2
    assert config.confidence_threshold == 55
    assert config.tesseract_cmd == r"C:\custom\tesseract.exe"
    assert config.tessdata_prefix == r"C:\custom\tessdata"


def test_load_config_discovers_scoop_tesseract(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SCYTCHECK_TESSERACT_CMD", raising=False)
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)

    scoop_root = tmp_path / "profile"
    tesseract_dir = scoop_root / "scoop" / "apps" / "tesseract" / "current"
    tessdata_dir = tesseract_dir / "tessdata"
    tessdata_dir.mkdir(parents=True)
    tesseract_exe = tesseract_dir / "tesseract.exe"
    tesseract_exe.write_text("", encoding="utf-8")

    monkeypatch.setenv("USERPROFILE", str(scoop_root))
    monkeypatch.setattr("src.config.shutil.which", lambda _name: None)

    config = load_config()

    assert config.tesseract_cmd == str(tesseract_exe)
    assert config.tessdata_prefix == str(tessdata_dir)


def test_load_config_discovers_bundled_tesseract_in_frozen_portable_layout(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SCYTCHECK_TESSERACT_CMD", raising=False)
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.delenv("ProgramFiles", raising=False)
    monkeypatch.delenv("ProgramFiles(x86)", raising=False)

    app_dir = tmp_path / "SCYTcheck"
    app_dir.mkdir(parents=True)
    app_executable = app_dir / "SCYTcheck.exe"
    app_executable.write_text("", encoding="utf-8")
    tesseract_exe = app_dir / "tesseract" / "tesseract.exe"
    tesseract_exe.parent.mkdir(parents=True)
    tesseract_exe.write_text("", encoding="utf-8")
    tessdata_dir = tesseract_exe.parent / "tessdata"
    tessdata_dir.mkdir()

    monkeypatch.setattr("src.config.sys.frozen", True, raising=False)
    monkeypatch.setattr("src.config.sys.executable", str(app_executable), raising=False)
    monkeypatch.setattr("src.config.shutil.which", lambda _name: None)

    config = load_config()

    assert config.tesseract_cmd == str(tesseract_exe)
    assert config.tessdata_prefix == str(tessdata_dir)


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
