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


def test_build_ydl_opts_selects_format_based_on_quality() -> None:
    opts_best = VideoService._build_ydl_opts("best")
    assert "height" not in opts_best["format"]

    opts_720 = VideoService._build_ydl_opts("720p")
    assert "720" in opts_720["format"]
    assert "height<=720" in opts_720["format"]

    opts_480 = VideoService._build_ydl_opts("480p")
    assert "height<=480" in opts_480["format"]

    opts_unknown = VideoService._build_ydl_opts("9999p")
    assert opts_unknown["format"] == opts_best["format"]
