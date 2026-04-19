from __future__ import annotations

from pathlib import Path


def test_fr010_ocr_path_has_no_cloud_or_account_dependencies() -> None:
    ocr_service_path = Path("src/services/ocr_service.py")
    text = ocr_service_path.read_text(encoding="utf-8").lower()

    forbidden_fragments = [
        "api_key",
        "openai",
        "aws",
        "azure",
        "gcp",
        "cloud",
        "http://",
        "https://",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in text
