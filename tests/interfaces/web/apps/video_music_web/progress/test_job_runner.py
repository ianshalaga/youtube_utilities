
from unittest.mock import MagicMock, patch

from applications.video_music.input import VideoMusicInput

from interfaces.web.apps.video_music_web.progress.job_runner import (
    run_video_music_job,
)


@patch(
    "interfaces.web.apps.video_music_web.progress.job_runner."
    "WebVideoMusicProgressReporter"
)
@patch(
    "interfaces.web.apps.video_music_web.progress.job_runner."
    "VideoMusicProcessorFactory.create_processor"
)
@patch(
    "interfaces.web.apps.video_music_web.progress.job_runner."
    "ConfigManager"
)
def test_run_video_music_job_executes_processor(
    config_manager_class,
    create_processor,
    reporter_class,
):
    job_id = "job-123"
    input_data = MagicMock(spec=VideoMusicInput)

    config = config_manager_class.return_value
    reporter = reporter_class.return_value
    processor = create_processor.return_value

    with patch(
        "interfaces.web.apps.video_music_web.progress.job_runner."
        "job_registry"
    ) as registry:
        run_video_music_job(job_id, input_data)

    reporter_class.assert_called_once_with(
        job_id=job_id,
        registry=registry,
    )
    create_processor.assert_called_once_with(
        config,
        console=reporter,
    )
    processor.process.assert_called_once_with(input_data)
    registry.job_failed.assert_not_called()


@patch(
    "interfaces.web.apps.video_music_web.progress.job_runner."
    "WebVideoMusicProgressReporter"
)
@patch(
    "interfaces.web.apps.video_music_web.progress.job_runner."
    "VideoMusicProcessorFactory.create_processor"
)
@patch(
    "interfaces.web.apps.video_music_web.progress.job_runner."
    "ConfigManager"
)
def test_run_video_music_job_records_unexpected_error(
    config_manager_class,
    create_processor,
    reporter_class,
):
    job_id = "job-456"
    input_data = MagicMock(spec=VideoMusicInput)
    error = RuntimeError("Error inesperado")

    processor = create_processor.return_value
    processor.process.side_effect = error

    with patch(
        "interfaces.web.apps.video_music_web.progress.job_runner."
        "job_registry"
    ) as registry:
        run_video_music_job(job_id, input_data)

    registry.job_failed.assert_called_once_with(job_id, error)
