
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class TrackStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class VideoMusicTrackResult:
    """Result of processing one audio track."""

    source_path: Path
    output_path: Path | None
    status: TrackStatus
    duration_seconds: float | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class VideoMusicResult:
    """Summary of a Video Music execution."""

    output_dir: Path
    total_tracks: int
    tracks: tuple[VideoMusicTrackResult, ...]
    total_directories: int

    @property
    def processed_tracks(self) -> int:
        return sum(
            track.status == TrackStatus.COMPLETED
            for track in self.tracks
        )

    @property
    def failed_tracks(self) -> int:
        return sum(
            track.status == TrackStatus.FAILED
            for track in self.tracks
        )
