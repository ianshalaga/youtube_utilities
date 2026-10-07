from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoMusicResult:
    """Result returned after executing the Video Music application."""

    output_dir: Path
    processed_tracks: int
    failed_tracks: int