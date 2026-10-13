
from unittest.mock import MagicMock, patch

from composition.video_music import VideoMusicProcessorFactory


def test_create_processor_passes_console_reporter():
    config = MagicMock()
    config.audio_supported_extensions = [".mp3", ".flac"]
    config.paths_mkvmerge = "mkvmerge"

    reporter = MagicMock()

    with (
        patch("composition.video_music.ProcessRunner"),
        patch("composition.video_music.AudioConverter"),
        patch("composition.video_music.MKVMergeRunner"),
        patch("composition.video_music.FFProbeProvider"),
        patch("composition.video_music.VideoMusicProcessor") as processor_class,
    ):
        VideoMusicProcessorFactory.create_processor(
            config,
            console=reporter,
        )

    processor_class.assert_called_once_with(
        mkvmerge_runner=processor_class.call_args.kwargs["mkvmerge_runner"],
        audio_converter=processor_class.call_args.kwargs["audio_converter"],
        ffprobe_provider=processor_class.call_args.kwargs["ffprobe_provider"],
        audio_supported_extensions=[".mp3", ".flac"],
        paths_mkvmerge="mkvmerge",
        console=reporter,
    )
