from pathlib import Path
from unittest.mock import Mock, call

import pytest

from domain.youtube.job import Job, JobStatus
from services.youtube.album_builder import AlbumBuilder
from services.youtube.planner import Planner
from services.youtube.youtube_discovery import YouTubeDiscovery
from services.youtube.album_manifest.yaml_reader import YamlReader
from applications.youtube_video_manager.processor import (
    JobRepository,
    Updater,
    YouTubeVideoManagerProcessor,
)
from services.youtube.console import YouTubeConsole


@pytest.fixture
def manifest_path() -> Path:
    return Path("manifests/test.yaml")


@pytest.fixture
def manifest() -> Mock:
    value = Mock(name="manifest")
    value.videos = [Mock(name="manifest_video")]
    return value


@pytest.fixture
def youtube_videos() -> list:
    return [Mock(name="youtube_video")]


@pytest.fixture
def album() -> Mock:
    return Mock(name="album")


@pytest.fixture
def job() -> Mock:
    value = Mock(spec=Job)
    value.status = JobStatus.PENDING
    return value


@pytest.fixture
def pending_job() -> Mock:
    value = Mock(spec=Job)
    value.status = JobStatus.PENDING
    return value


@pytest.fixture
def failed_job() -> Mock:
    value = Mock(spec=Job)
    value.status = JobStatus.FAILED
    return value


@pytest.fixture
def manifest_reader() -> Mock:
    return Mock(spec=YamlReader)


@pytest.fixture
def youtube_discovery() -> Mock:
    return Mock(spec=YouTubeDiscovery)


@pytest.fixture
def album_builder() -> Mock:
    return Mock(spec=AlbumBuilder)


@pytest.fixture
def planner() -> Mock:
    return Mock(spec=Planner)


@pytest.fixture
def updater() -> Mock:
    return Mock(spec=Updater)


@pytest.fixture
def job_repository() -> Mock:
    return Mock(spec=JobRepository)


@pytest.fixture
def failure_action() -> Mock:
    return Mock(return_value="retry")


@pytest.fixture
def console() -> Mock:
    return Mock(spec=YouTubeConsole)


@pytest.fixture
def processor(
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    updater: Mock,
    job_repository: Mock,
    failure_action: Mock,
    console: Mock,
) -> YouTubeVideoManagerProcessor:
    return YouTubeVideoManagerProcessor(
        manifest_reader=manifest_reader,
        youtube_discovery=youtube_discovery,
        album_builder=album_builder,
        planner=planner,
        updater=updater,
        job_repository=job_repository,
        failure_action=failure_action,
        console=console,
    )


def test_pending_job_is_continued_without_creating_new_job(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    pending_job: Mock,
    job_repository: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = pending_job

    processor.process(manifest_path)

    updater.update.assert_called_once_with(pending_job)
    manifest_reader.read.assert_not_called()
    youtube_discovery.discover.assert_not_called()
    album_builder.build.assert_not_called()
    planner.plan.assert_not_called()


def test_failed_job_retry_is_retried_and_updated(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    failed_job: Mock,
    job_repository: Mock,
    failure_action: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = failed_job
    failure_action.return_value = "retry"

    processor.process(manifest_path)

    failure_action.assert_called_once_with()
    failed_job.retry.assert_called_once_with()
    job_repository.save.assert_called_once_with(failed_job)
    updater.update.assert_called_once_with(failed_job)


def test_failed_job_discard_creates_new_job(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    failed_job: Mock,
    job_repository: Mock,
    failure_action: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    manifest: Mock,
    youtube_videos: list,
    album: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = failed_job
    failure_action.return_value = "discard"

    manifest_reader.read.return_value = manifest
    youtube_discovery.discover.return_value = youtube_videos
    album_builder.build.return_value = album
    new_job = Mock(spec=Job)
    planner.plan.return_value = new_job

    processor.process(manifest_path)

    failed_job.retry.assert_not_called()
    manifest_reader.read.assert_called_once_with(manifest_path)
    youtube_discovery.discover.assert_called_once_with(len(manifest.videos))
    album_builder.build.assert_called_once_with(manifest, youtube_videos)
    planner.plan.assert_called_once_with(album)
    updater.update.assert_called_once_with(new_job)


def test_no_existing_job_creates_new_job_from_manifest(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    job_repository: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    manifest: Mock,
    youtube_videos: list,
    album: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = None

    manifest_reader.read.return_value = manifest
    youtube_discovery.discover.return_value = youtube_videos
    album_builder.build.return_value = album
    new_job = Mock(spec=Job)
    planner.plan.return_value = new_job

    processor.process(manifest_path)

    manifest_reader.read.assert_called_once_with(manifest_path)
    youtube_discovery.discover.assert_called_once_with(len(manifest.videos))
    album_builder.build.assert_called_once_with(manifest, youtube_videos)
    planner.plan.assert_called_once_with(album)
    updater.update.assert_called_once_with(new_job)


def test_pending_job_has_priority_over_failed_job(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    pending_job: Mock,
    failed_job: Mock,
    job_repository: Mock,
    failure_action: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = pending_job
    job_repository.find_failed.return_value = failed_job

    processor.process(manifest_path)

    job_repository.find_failed.assert_not_called()
    failure_action.assert_not_called()
    updater.update.assert_called_once_with(pending_job)


def test_completed_job_is_not_retrieved_by_processor(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    job_repository: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    updater: Mock,
    manifest: Mock,
    youtube_videos: list,
    album: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = None

    manifest_reader.read.return_value = manifest
    youtube_discovery.discover.return_value = youtube_videos
    album_builder.build.return_value = album
    new_job = Mock(spec=Job)
    planner.plan.return_value = new_job

    processor.process(manifest_path)

    job_repository.find_pending.assert_called_once_with()
    job_repository.find_failed.assert_called_once_with()
    updater.update.assert_called_once_with(new_job)


def test_running_job_is_not_retrieved_by_processor(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    job_repository: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    updater: Mock,
    manifest: Mock,
    youtube_videos: list,
    album: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = None

    manifest_reader.read.return_value = manifest
    youtube_discovery.discover.return_value = youtube_videos
    album_builder.build.return_value = album
    new_job = Mock(spec=Job)
    planner.plan.return_value = new_job

    processor.process(manifest_path)

    job_repository.find_pending.assert_called_once_with()
    job_repository.find_failed.assert_called_once_with()
    updater.update.assert_called_once_with(new_job)


@pytest.mark.parametrize("action", ["invalid", "", "Retry", "DISCARD", "cancel"])
def test_invalid_failed_job_action_raises_value_error(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    failed_job: Mock,
    job_repository: Mock,
    failure_action: Mock,
    updater: Mock,
    action: str,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = failed_job
    failure_action.return_value = action

    with pytest.raises(
        ValueError,
        match="Invalid action for failed job. Expected 'retry' or 'discard'.",
    ):
        processor.process(manifest_path)

    failed_job.retry.assert_not_called()
    updater.update.assert_not_called()


def test_retry_saves_job_before_updating(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    failed_job: Mock,
    job_repository: Mock,
    failure_action: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = failed_job
    failure_action.return_value = "retry"

    calls = Mock()
    failed_job.retry.side_effect = lambda: calls("retry")
    job_repository.save.side_effect = lambda value: calls("save", value)
    updater.update.side_effect = lambda value: calls("update", value)

    processor.process(manifest_path)

    assert calls.call_args_list == [
        call("retry"),
        call("save", failed_job),
        call("update", failed_job),
    ]


def test_new_job_is_not_explicitly_saved_by_processor(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    job_repository: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    updater: Mock,
    manifest: Mock,
    youtube_videos: list,
    album: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = None

    manifest_reader.read.return_value = manifest
    youtube_discovery.discover.return_value = youtube_videos
    album_builder.build.return_value = album
    new_job = Mock(spec=Job)
    planner.plan.return_value = new_job

    processor.process(manifest_path)

    job_repository.save.assert_not_called()
    updater.update.assert_called_once_with(new_job)


def test_manifest_path_is_passed_unchanged(
    processor: YouTubeVideoManagerProcessor,
    manifest_path: Path,
    job_repository: Mock,
    manifest_reader: Mock,
    youtube_discovery: Mock,
    album_builder: Mock,
    planner: Mock,
    manifest: Mock,
    youtube_videos: list,
    album: Mock,
    updater: Mock,
) -> None:
    job_repository.find_pending.return_value = None
    job_repository.find_failed.return_value = None

    manifest_reader.read.return_value = manifest
    youtube_discovery.discover.return_value = youtube_videos
    album_builder.build.return_value = album
    new_job = Mock(spec=Job)
    planner.plan.return_value = new_job

    processor.process(manifest_path)

    assert manifest_reader.read.call_args.args == (manifest_path,)
    updater.update.assert_called_once_with(new_job)
