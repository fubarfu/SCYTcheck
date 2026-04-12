from __future__ import annotations

from pathlib import Path


def test_fr010_to_fr013_release_bundle_requirements_are_wired() -> None:
    build_script = Path("scripts/release/build.ps1")
    text = build_script.read_text(encoding="utf-8")

    # FR-010/011: portable ZIP artifacts are created and architecture is explicit.
    assert "ValidateSet('x64', 'x86')" in text
    assert "SCYTcheck-{0}.zip" in text
    assert "Compress-Archive" in text

    # FR-012/013: bundled Tesseract and FFmpeg payloads are staged into bundle.
    assert "ffmpeg" in text
    assert "tesseract" in text
    assert "Copy-OptionalTree -Source $ffmpegSource" in text
    assert "Copy-OptionalTree -Source $tesseractSource" in text
