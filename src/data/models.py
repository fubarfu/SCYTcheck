from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class Region:
    """Represents a rectangular region in a video frame with temporal context."""
    x: int
    y: int
    width: int
    height: int
    frame_time: float = 0.0  # Time in seconds when region was selected

    @property
    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return region as (x, y, width, height) tuple for backwards compatibility."""
        return (self.x, self.y, self.width, self.height)


@dataclass
class TextString:
    content: str
    x: int
    y: int
    width: int
    height: int
    frequency: int = 1
    frame_time: float = 0.0  # Time in seconds when text was detected

    @property
    def region(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)


@dataclass
class VideoAnalysis:
    url: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    text_strings: list[TextString] = field(default_factory=list)
    _index: dict[tuple[str, int, int, int, int], TextString] = field(
        default_factory=dict,
        init=False,
    )

    def add_detection(self, content: str, region: tuple[int, int, int, int], frame_time: float = 0.0) -> None:
        cleaned = content.strip()
        if not cleaned:
            return

        x, y, width, height = region
        key = (cleaned.lower(), x, y, width, height)
        existing = self._index.get(key)
        if existing:
            existing.frequency += 1
            return

        text_string = TextString(
            content=cleaned,
            x=x,
            y=y,
            width=width,
            height=height,
            frequency=1,
            frame_time=frame_time,
        )
        self.text_strings.append(text_string)
        self._index[key] = text_string
