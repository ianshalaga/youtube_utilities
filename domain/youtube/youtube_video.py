from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PrivacyStatus(str, Enum):
    """YouTube video privacy status."""

    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"


@dataclass(frozen=True)
class YouTubeVideo:
    """Represents a video discovered on YouTube."""

    video_id: str
    title: str
    description: str | None
    privacy_status: PrivacyStatus

    def __post_init__(self) -> None:
        if not isinstance(self.video_id, str) or not self.video_id.strip():
            raise ValueError("video_id must be a non-empty string.")

        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string.")