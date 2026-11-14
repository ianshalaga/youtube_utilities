from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from domain.youtube.job import Job, JobStatus
from domain.youtube.job_repository import JobRepository
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from applications.youtube_video_manager.processor import (
    YouTubeVideoManagerProcessor,
)
from services.youtube.album_builder import AlbumBuilder
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.console import YouTubeConsole
from services.youtube.planner import Planner
from services.youtube.updater import Updater
from services.youtube.video_id_overrides_reader import VideoIdOverridesReader
from services.youtube.youtube_discovery import YouTubeDiscovery


def create_processor():
    repository = Mock(spec=JobRepository)
    updater = Mock(spec=Updater)
    console = Mock(spec=YouTubeConsole)
    processor = YouTubeVideoManagerProcessor(
        manifest_reader=Mock(spec=YamlReader),
        youtube_discovery=Mock(spec=YouTubeDiscovery),
        album_builder=Mock(spec=AlbumBuilder),
        planner=Mock(spec=Planner),
        updater=updater,
        job_repository=repository,
        console=console,
        video_id_overrides_reader=Mock(spec=VideoIdOverridesReader),
        video_id_overrides_path=Path("config/youtube/ids.yaml"),
    )
    return processor, repository, updater, console


def create_job(
    status: JobStatus = JobStatus.CREATED,
    operation_status: OperationStatus = OperationStatus.PENDING,
) -> Job:
    metadata = VideoMetadata(
        title="Video title",
        description="Description",
        tags=["tag"],
        playlists=[],
        game="Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 1, 1, 18, 0, tzinfo=timezone.utc),
        thumbnail=None,
    )
    video = Video(
        video_id="video-1",
        position=1,
        video_type=VideoType.SONG,
        metadata=metadata,
    )
    operation = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=metadata,
    )
    if operation_status in {OperationStatus.RUNNING, OperationStatus.FAILED}:
        operation.start()
    if operation_status is OperationStatus.FAILED:
        operation.fail()
    elif operation_status is OperationStatus.COMPLETED:
        operation.complete()

    publication = PublicationSettings(
        first_publish_at=datetime(2026, 1, 1, 18, 0),
        timezone="UTC",
        interval_days=1,
    )
    return Job(
        [operation],
        publication=publication,
        job_id=15,
        status=status,
        name="Test Album",
    )


def test_create_and_save_job_persists_and_reports_success(monkeypatch):
    processor, repository, _, console = create_processor()
    job = create_job()
    create = Mock(return_value=job)
    monkeypatch.setattr(processor, "_create_job", create)

    result = processor.create_and_save_job(Path("manifest.yaml"))

    assert result is job
    create.assert_called_once_with(Path("manifest.yaml"))
    repository.save.assert_called_once_with(job)
    console.job_created.assert_called_once_with(job)


def test_create_and_save_job_reports_failure_and_returns_none(monkeypatch):
    processor, repository, _, console = create_processor()
    error = ValueError("Invalid manifest")
    create = Mock(side_effect=error)
    monkeypatch.setattr(processor, "_create_job", create)

    result = processor.create_and_save_job(Path("manifest.yaml"))

    assert result is None
    repository.save.assert_not_called()
    console.job_creation_failed.assert_called_once_with(error)


def test_start_created_job_recalculates_schedule_before_updating():
    processor, repository, updater, _ = create_processor()
    job = create_job()
    publication = PublicationSettings(
        first_publish_at=datetime(2026, 5, 20, 10, 30),
        timezone="Europe/Paris",
        interval_days=4,
    )

    processor.start_created_job(job, publication)

    assert job.publication is publication
    assert job.operations[0].data.publish_at.isoformat() == (
        "2026-05-20T10:30:00+02:00"
    )
    repository.save.assert_called_once_with(job)
    updater.update.assert_called_once_with(job)


def test_retry_failed_job_retries_only_from_failed_operation():
    processor, _, updater, _ = create_processor()
    job = create_job(JobStatus.FAILED, OperationStatus.FAILED)

    processor.retry_failed_job(job)

    assert job.status is JobStatus.PENDING
    assert job.operations[0].status is OperationStatus.PENDING
    updater.update.assert_called_once_with(job)


def test_recover_running_job_resets_interrupted_operation_and_saves_pending():
    processor, repository, updater, _ = create_processor()
    job = create_job(JobStatus.RUNNING, OperationStatus.RUNNING)

    processor.recover_running_job(job)

    assert job.status is JobStatus.PENDING
    assert job.operations[0].status is OperationStatus.PENDING
    repository.save.assert_called_once_with(job)
    updater.update.assert_called_once_with(job)


def test_delete_job_delegates_to_repository_and_reports_result():
    processor, repository, _, console = create_processor()
    job = create_job(JobStatus.FAILED, OperationStatus.FAILED)

    processor.delete_job(job)

    repository.delete.assert_called_once_with(job)
    console.job_deleted.assert_called_once_with(job)
