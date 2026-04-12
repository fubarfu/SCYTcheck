from __future__ import annotations

from tests.integration.helpers.codec_helpers import build_codec_source_id, is_supported_codec
from tests.integration.helpers.parity_helpers import assert_frame_count_parity, assert_timestamp_parity


def test_codec_source_ids_cover_h264_and_vp9() -> None:
    assert build_codec_source_id("h264", "mp4") == "h264_mp4"
    assert build_codec_source_id("vp9", "webm") == "vp9_webm"
    assert is_supported_codec("h264") is True
    assert is_supported_codec("vp9") is True


def test_timestamp_and_frame_count_parity_for_codec_targets() -> None:
    baseline = [0.0, 1.0, 2.0, 3.0]
    h264 = [0.0, 1.0, 2.0, 3.0]
    vp9 = [0.0, 1.0, 2.0, 3.0]

    assert_timestamp_parity(baseline, h264)
    assert_timestamp_parity(baseline, vp9)
    assert_frame_count_parity(len(baseline), len(h264), tolerance=1)
    assert_frame_count_parity(len(baseline), len(vp9), tolerance=1)
