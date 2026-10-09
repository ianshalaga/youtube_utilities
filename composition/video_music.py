
from applications.video_music.processor import VideoMusicProcessor
from services.media.audio.converter import AudioConverter
from services.media.ffprobe_provider import FFProbeProvider
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.system.process_runner import ProcessRunner


class VideoMusicProcessorFactory:
    """Builds the dependencies required by Video Music."""

    @staticmethod
    def create_processor() -> VideoMusicProcessor:
        process_runner = ProcessRunner()

        audio_converter = AudioConverter(
            process_runner=process_runner,
        )

        mkvmerge_runner = MKVMergeRunner(
            process_runner=process_runner,
        )

        ffprobe_provider = FFProbeProvider(
            process_runner=process_runner,
        )

        return VideoMusicProcessor(
            mkvmerge_runner=mkvmerge_runner,
            audio_converter=audio_converter,
            ffprobe_provider=ffprobe_provider,
        )
