from __future__ import annotations

from pathlib import Path


def test_fr010_to_fr013_release_bundle_requirements_are_wired() -> None:
    build_script = Path("scripts/release/build.ps1")
    text = build_script.read_text(encoding="utf-8")

    # FR-010/011: portable ZIP artifacts are created and architecture is explicit.
    assert "ValidateSet('x64', 'x86')" in text
    assert "SCYTcheck-{0}-{1}.zip" in text
    assert "Resolve-AppVersion" in text
    assert "pyproject.toml" in text
    assert "New-ZipFromDirectory" in text
    assert "Removing stale ZIP" in text
    assert "SCYTcheck-*-{0}.zip" in text

    # FR-012/013: bundled OCR and FFmpeg payloads are staged into bundle.
    assert "ffmpeg" in text
    assert "paddleocr" in text
    assert "Test-RequiredPaddleOCRAssets" in text
    assert "Run scripts/download_paddleocr_models.ps1 first" in text
    assert "Resolve-PythonModuleFile" in text
    assert "decorator.py" in text
    assert "Copy-OptionalTree -Source $ffmpegSource" in text
    assert "Copy-OptionalTree -Source $paddleocrSource" in text

    spec_text = Path("build-config.spec").read_text(encoding="utf-8")
    assert 'collect_data_files("paddleocr", include_py_files=True)' in spec_text
    assert 'collect_data_files("paddle", include_py_files=True)' in spec_text
    assert 'collect_data_files("Cython", include_py_files=True)' in spec_text
    assert 'collect_dynamic_libs("paddle")' in spec_text
    assert '"decorator"' in spec_text
    assert 'collect_submodules("paddle")' in spec_text
    assert 'runtime_hook_paddleocr.py' in spec_text
    assert 'upx=False' in spec_text
    assert "Missing PaddleOCR model root for portable build" in spec_text
    assert "Missing det* PaddleOCR model directory" in spec_text
    assert "Missing rec* PaddleOCR model directory" in spec_text
    assert "Missing cls* PaddleOCR model directory" in spec_text

    hook_text = Path("scripts/release/runtime_hook_paddleocr.py").read_text(encoding="utf-8")
    assert 'bundle_root / "paddleocr"' in hook_text
    assert 'bundle_root / "paddle" / "base"' in hook_text
    assert 'bundle_root / "paddle" / "libs"' in hook_text
    assert 'endswith(".libs")' in hook_text
    assert "add_dll_directory" in hook_text
    assert 'executable_root / "paddleocr"' not in hook_text
