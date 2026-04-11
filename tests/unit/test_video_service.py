from unittest.mock import patch

from src.services.video_service import VideoService


def test_validate_youtube_url_rejects_invalid_format() -> None:
    service = VideoService()

    is_valid, error = service.validate_youtube_url("https://example.com/video")

    assert not is_valid
    assert "valid YouTube" in error


def test_build_ydl_opts_enables_node_runtime_when_available() -> None:
    service = VideoService()

    with patch("src.services.video_service.shutil.which") as which_mock:
        which_mock.side_effect = lambda name: {
            "node": r"C:\Program Files\nodejs\node.exe",
            "deno": None,
            "quickjs": None,
            "bun": None,
        }.get(name)
        opts = service._build_ydl_opts()

    runtimes = opts["js_runtimes"]
    assert isinstance(runtimes, dict)
    assert "node" in runtimes
    assert runtimes["node"] == {"path": r"C:\Program Files\nodejs\node.exe"}
    assert "deno" in runtimes


def test_validate_youtube_url_accepts_accessible_video() -> None:
    service = VideoService()

    with patch.object(service, "_extract_media_url", return_value=("stream", {"id": "abc"})):
        is_valid, error = service.validate_youtube_url("https://youtube.com/watch?v=abc")

    assert is_valid
    assert error == ""


def test_validate_youtube_url_handles_unreachable_video() -> None:
    service = VideoService()

    with patch.object(service, "_extract_media_url", side_effect=RuntimeError("network issue")):
        is_valid, error = service.validate_youtube_url("https://youtu.be/abc")

    assert not is_valid
    assert "could not be accessed" in error
