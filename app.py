from pathlib import Path
from apps.video_music.processor import VideoMusicProcessor
from core.config_manager import ConfigManager

config = ConfigManager()

video_music_processor = VideoMusicProcessor()

video_path = config.video_music_default_video_path
audios_dir = config.video_music_default_audios_dir
output_dir = config.video_music_default_output_dir

video_music_processor.process(
    video_path=Path(video_path),
    audios_dir=Path(audios_dir),
    output_dir=Path(audios_dir) / Path(output_dir)
)
