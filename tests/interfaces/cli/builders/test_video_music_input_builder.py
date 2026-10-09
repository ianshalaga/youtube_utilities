from pathlib import Path
from types import SimpleNamespace

from applications.video_music.input import VideoMusicInput
from interfaces.cli.builders.video_music_input_builder import (
    build_video_music_input,
)


def test_build_video_music_input_uses_config_values_and_path_objects() -> None:
    config = SimpleNamespace(
        video_music_max_items_per_dir=15,
        video_music_default_video_path="assets/template.mp4",
        video_music_default_audios_dir="assets/audio",
        video_music_default_output_dir="rendered",
    )

    result = build_video_music_input(config)

    assert isinstance(result, VideoMusicInput)
    assert result.max_items_per_dir == 15
    assert result.video_path == Path("assets/template.mp4")
    assert result.audios_dir == Path("assets/audio")
    assert result.output_dir == Path("assets/audio") / "rendered"


def test_build_video_music_input_joins_output_directory_to_audio_directory() -> None:
    config = SimpleNamespace(
        video_music_max_items_per_dir=8,
        video_music_default_video_path="template.mp4",
        video_music_default_audios_dir="D:/media/music",
        video_music_default_output_dir="output",
    )

    result = build_video_music_input(config)

    assert result.output_dir == Path("D:/media/music") / "output"
