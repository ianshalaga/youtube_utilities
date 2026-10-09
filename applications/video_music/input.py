from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoMusicInput:
    """Input required to execute the Video Music application."""

    max_items_per_dir: int
    audios_dir: Path
    video_path: Path
    output_dir: Path