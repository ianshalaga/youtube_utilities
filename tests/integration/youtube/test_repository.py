from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata

from services.youtube.storage.base import Base
from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.models import JobModel, OperationModel
from services.youtube.storage.repository import YouTubeJobRepository

pytestmark = pytest.mark.integration

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture
def mapper():
    return JobMapper()


@pytest.fixture
def repository(session, mapper):
    return YouTubeJobRepository(session, mapper)


def create_metadata(
    title: str = "01 - Test Song",
    thumbnail: Path | None = Path("thumbnail.jpg"),
) -> VideoMetadata:
    return VideoMetadata(
        title=title,
        description="Test description",
        tags=["test", "song"],
        playlists=["playlist-1", "playlist-2"],
        game="Test Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 9, 17, 18, 0, tzinfo=timezone.utc),
        thumbnail=thumbnail,
    )


def create_video(
    video_id: str = "video-123",
    position: int = 1,
    metadata: VideoMetadata | None = None,
) -> Video:
    return Video(
        video_id=video_id,
        position=position,
        video_type=VideoType.SONG,
        metadata=metadata or create_metadata(),
    )


def create_job(title: str = "01 - Test Song") -> Job:
    video = create_video(metadata=create_metadata(title=title))

    operations = [
        Operation(
            video=video,
            operation_type=OperationType.UPDATE_METADATA,
            data=video.metadata,
        ),
        Operation(
            video=video,
            operation_type=OperationType.SET_THUMBNAIL,
            data=video.metadata.thumbnail,
        ),
        Operation(
            video=video,
            operation_type=OperationType.ADD_TO_PLAYLIST,
            data="playlist-1",
        ),
    ]

    return Job(operations)


def test_find_pending_returns_pending_job(repository, session):
    job = create_job()
    repository.save(job)

    loaded_job = repository.find_pending()

    assert loaded_job is not None
    assert loaded_job.status is JobStatus.PENDING
    assert len(loaded_job.operations) == 3
    assert session.query(JobModel).count() == 1


def test_find_failed_returns_failed_job(repository, session):
    job = create_job()
    job.start()
    job.fail()
    repository.save(job)

    loaded_job = repository.find_failed()

    assert loaded_job is not None
    assert loaded_job.status is JobStatus.FAILED
    assert len(loaded_job.operations) == 3
    assert session.query(JobModel).count() == 1


def test_find_pending_returns_none_when_no_pending_job(repository):
    assert repository.find_pending() is None


def test_find_failed_returns_none_when_no_failed_job(repository):
    assert repository.find_failed() is None


def test_save_inserts_new_job(repository, session):
    job = create_job()

    repository.save(job)

    job_models = session.query(JobModel).all()

    assert len(job_models) == 1
    assert job_models[0].status == JobStatus.PENDING.value
    assert len(job_models[0].operations) == 3


def test_save_updates_loaded_job_instead_of_inserting(repository, session):
    job = create_job()
    repository.save(job)

    loaded_job = repository.find_pending()
    assert loaded_job is not None

    loaded_job.start()
    loaded_job.operations[0].start()
    loaded_job.operations[0].complete()

    repository.save(loaded_job)

    job_models = session.query(JobModel).all()

    assert len(job_models) == 1
    assert job_models[0].status == JobStatus.RUNNING.value
    assert job_models[0].operations[0].status == OperationStatus.COMPLETED.value


def test_save_replaces_existing_operations(repository, session):
    job = create_job()
    repository.save(job)

    loaded_job = repository.find_pending()
    assert loaded_job is not None

    loaded_job.start()
    loaded_job.operations[0].start()
    loaded_job.operations[0].complete()

    repository.save(loaded_job)

    job_model = session.query(JobModel).one()

    assert len(job_model.operations) == 3
    assert (
        session.query(OperationModel)
        .filter(OperationModel.job_id == job_model.id)
        .count()
        == 3
    )


def test_saved_job_can_be_loaded_again_as_domain(repository, session):
    job = create_job()
    repository.save(job)

    loaded_job = repository.find_pending()
    assert loaded_job is not None

    loaded_job.start()
    loaded_job.fail()
    repository.save(loaded_job)

    reloaded_job = repository.find_failed()

    assert reloaded_job is not None
    assert reloaded_job.status is JobStatus.FAILED
    assert len(reloaded_job.operations) == 3
    assert all(
        operation.status is OperationStatus.PENDING
        for operation in reloaded_job.operations
    )
