
from core.config_manager import ConfigManager
from applications.video_music.input import VideoMusicInput
from composition.video_music import VideoMusicProcessorFactory

from .progress_reporter import WebVideoMusicProgressReporter
from .runtime import job_registry


def run_video_music_job(
    job_id: str,
    input_data: VideoMusicInput,
) -> None:
    """Execute a Video Music job and record unexpected failures."""

    reporter = WebVideoMusicProgressReporter(
        job_id=job_id,
        registry=job_registry,
    )

    try:
        config = ConfigManager()

        processor = VideoMusicProcessorFactory.create_processor(
            config,
            console=reporter,
        )

        processor.process(input_data)

    except Exception as error:
        job_registry.job_failed(job_id, error)
