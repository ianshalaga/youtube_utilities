from pathlib import Path

from apps.video_music.processor import VideoMusicProcessor
from apps.video_joiner.processor import VideoJoinerProcessor
from core.config_manager import ConfigManager
from services.media.video.converter import VideoConverter
from services.media.ffprobe_provider import FFProbeProvider


config = ConfigManager()

video_music = False
video_joiner = True
video_converter = False

if video_music:
    video_music_processor = VideoMusicProcessor()

    audios_dir = config.video_music_default_audios_dir

    video_music_processor.process(
        video_path=Path(config.video_music_default_video_path),
        audios_dir=Path(audios_dir),
        output_dir=Path(audios_dir) /
        Path(config.video_music_default_output_dir)
    )

if video_joiner:
    video_joiner_processor = VideoJoinerProcessor()

    videos_dir = Path(config.video_joiner_default_videos_dir)
    output_dir = videos_dir / Path(config.video_joiner_default_output_dir)
    end_screens_dir = Path(
        config.video_joiner_default_end_screens_dir) if config.video_joiner_default_end_screens_dir else None

    video_joiner_processor.process(
        videos_dir=videos_dir,
        output_dir=output_dir,
        base_name=config.video_joiner_default_video_name,
        target_duration=config.video_joiner_default_target_duration,
        end_screens_dir=end_screens_dir,
        random_end_screen=config.video_joiner_default_random_end_screen,
        timestamps_prefix=config.video_joiner_default_timestamps_prefix,
        timestamps_secuence=config.video_joiner_default_timestamps_secuence,
        extra_description=config.video_joiner_default_extra_description
    )

if video_converter:
    probe_provider = FFProbeProvider()
    video_converter = VideoConverter(probe_provider=probe_provider)

    src = Path(config.video_converter_src)
    dst_dir = Path(config.video_converter_dst_dir)
    output_format = config.video_converter_output_format
    reference_video = Path(config.video_converter_reference_video)

    video_converter.convert(
        src=src,
        dst_dir=dst_dir,
        output_format=output_format,
        reference_video=reference_video
    )
