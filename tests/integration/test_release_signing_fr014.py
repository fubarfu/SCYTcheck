from __future__ import annotations

from pathlib import Path


def test_fr014_unsigned_packaging_and_optional_signing_behavior() -> None:
    sign_script = Path("scripts/release/sign.ps1")
    text = sign_script.read_text(encoding="utf-8")

    # FR-014: release flow must not require a certificate.
    assert "if (-not $CertificatePath)" in text
    assert "[sign] No certificate provided." in text
    assert "[sign] Skipping signing step." in text

    # FR-014: optional post-build signing remains available.
    assert "signtool.exe" in text
    assert "if ($CertificatePassword)" in text
