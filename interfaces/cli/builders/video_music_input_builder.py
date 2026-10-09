
"""Build the input required by the Video Music CLI command."""

from pathlib import Path

from applications.video_music.input import VideoMusicInput
from core.config_manager import ConfigManager


def build_video_music_input(config: ConfigManager) -> VideoMusicInput:
    """Build VideoMusicInput from the application configuration."""
    audios_dir = Path(config.video_music_default_audios_dir)

    return VideoMusicInput(
        max_items_per_dir=config.video_music_max_items_per_dir,
        video_path=Path(config.video_music_default_video_path),
        audios_dir=audios_dir,
        output_dir=audios_dir / config.video_music_default_output_dir,
    )
