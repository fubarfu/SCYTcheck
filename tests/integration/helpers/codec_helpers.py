from __future__ import annotations


def build_codec_source_id(codec: str, container: str) -> str:
    return f"{codec.lower()}_{container.lower()}"


def is_supported_codec(codec: str) -> bool:
    return codec.lower() in {"h264", "vp9"}
