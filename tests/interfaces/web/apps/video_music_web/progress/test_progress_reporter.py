
from interfaces.web.apps.video_music_web.progress.job_progress import (
    VideoMusicJobRegistry,
)
from interfaces.web.apps.video_music_web.progress.progress_reporter import (
    WebVideoMusicProgressReporter,
)


def create_reporter(registry, tmp_path):
    job_id = registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=2,
    )

    reporter = WebVideoMusicProgressReporter(
        job_id=job_id,
        registry=registry,
    )

    return job_id, reporter


def test_reporter_forwards_job_and_track_events(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id, reporter = create_reporter(registry, tmp_path)

    video_path = tmp_path / "base.mkv"
    audios_dir = tmp_path / "audio"
    output_dir = tmp_path / "output"
    audio_path = audios_dir / "theme.flac"
    converted_audio_path = output_dir / "theme.wav"
    generated_video_path = output_dir / "theme.mkv"

    reporter.job_started(
        video_path=video_path,
        audios_dir=audios_dir,
        output_dir=output_dir,
        total_tracks=1,
        max_items_per_dir=2,
    )
    reporter.partition_started(
        total_tracks=1,
        max_items_per_dir=2,
        total_directories=1,
    )
    reporter.processing_started()
    reporter.track_started(
        index=1,
        total=1,
        audio_path=audio_path,
        output_dir=output_dir,
    )

    reporter.audio_converted(audio_path, converted_audio_path)
    reporter.duration_detected(audio_path, "03:25.000")
    reporter.video_created(audio_path, generated_video_path)
    reporter.temporary_files_cleaned(audio_path)

    reporter.track_completed(
        index=1,
        total=1,
        audio_path=audio_path,
    )
    reporter.job_completed(
        total_tracks=1,
        output_dir=output_dir,
    )

    job = registry.get_job(job_id)

    assert job is not None
    assert job.status == "completed"
    assert job.total_tracks == 1
    assert job.completed_tracks == 1
    assert job.failed_tracks == 0
    assert job.running_tracks == 0

    track = job.tracks[0]
    assert track.status == "completed"
    assert track.name == "theme"
    assert track.duration == "03:25.000"
    assert track.output_path == str(generated_video_path)


def test_reporter_forwards_track_failure(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id, reporter = create_reporter(registry, tmp_path)

    audio_path = tmp_path / "audio" / "theme.flac"
    output_dir = tmp_path / "output"

    reporter.job_started(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=output_dir,
        total_tracks=1,
        max_items_per_dir=2,
    )
    reporter.track_started(
        index=1,
        total=1,
        audio_path=audio_path,
        output_dir=output_dir,
    )
    reporter.track_failed(
        index=1,
        total=1,
        audio_path=audio_path,
        error=RuntimeError("No se pudo generar el vídeo"),
    )

    job = registry.get_job(job_id)

    assert job is not None
    assert job.status == "running"
    assert job.failed_tracks == 1
    assert job.tracks[0].status == "failed"
    assert (
        job.tracks[0].error_message
        == "No se pudo generar el vídeo"
    )


def test_reporter_forwards_job_level_failure(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id, reporter = create_reporter(registry, tmp_path)

    reporter.job_failed(RuntimeError("Error global"))

    job = registry.get_job(job_id)

    assert job is not None
    assert job.status == "failed"
    assert job.error_message == "Error global"
