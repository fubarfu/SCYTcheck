from src.data.models import VideoAnalysis


def test_add_detection_groups_same_region_and_text() -> None:
    analysis = VideoAnalysis(url="https://youtube.com/watch?v=abc")

    analysis.add_detection("PlayerOne", (10, 20, 100, 30))
    analysis.add_detection("playerone", (10, 20, 100, 30))

    assert len(analysis.text_strings) == 1
    assert analysis.text_strings[0].frequency == 2
