from datetime import datetime, timezone
from pathlib import Path

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata

from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.models.job import JobModel
from services.youtube.storage.models.operation import OperationModel
from services.youtube.storage.models.video import VideoModel
from services.youtube.storage.models.video_metadata import VideoMetadataModel


def create_video() -> Video:
    metadata = VideoMetadata(
        title="01 - Test Song",
        description="Test description",
        tags=["test", "song"],
        playlists=["playlist-1", "playlist-2"],
        game="Test Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(
            2026,
            9,
            17,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        thumbnail=Path("thumbnail.jpg"),
    )

    return Video(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG,
        metadata=metadata,
    )


def create_update_metadata_operation() -> Operation:
    video = create_video()

    return Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=video.metadata,
    )


def create_set_thumbnail_operation() -> Operation:
    video = create_video()

    return Operation(
        video=video,
        operation_type=OperationType.SET_THUMBNAIL,
        data=video.metadata.thumbnail,
    )


def create_add_to_playlist_operation() -> Operation:
    video = create_video()

    return Operation(
        video=video,
        operation_type=OperationType.ADD_TO_PLAYLIST,
        data="playlist-1",
    )


def test_to_model_maps_pending_job():
    mapper = JobMapper()
    operation = create_update_metadata_operation()
    job = Job([operation])

    model = mapper.to_model(job)

    assert isinstance(model, JobModel)
    assert model.status == JobStatus.PENDING.value
    assert len(model.operations) == 1


def test_to_model_maps_operation():
    mapper = JobMapper()
    operation = create_update_metadata_operation()
    job = Job([operation])

    model = mapper.to_model(job)
    operation_model = model.operations[0]

    assert isinstance(operation_model, OperationModel)
    assert operation_model.operation_type == OperationType.UPDATE_METADATA.value
    assert operation_model.status == OperationStatus.PENDING.value


def test_to_model_maps_video():
    mapper = JobMapper()
    operation = create_update_metadata_operation()
    job = Job([operation])

    model = mapper.to_model(job)
    video_model = model.operations[0].video

    assert isinstance(video_model, VideoModel)
    assert video_model.video_id == "video-123"
    assert video_model.position == 1
    assert video_model.video_type == VideoType.SONG.value


def test_to_model_maps_update_metadata():
    mapper = JobMapper()
    operation = create_update_metadata_operation()
    job = Job([operation])

    model = mapper.to_model(job)
    data_model = model.operations[0].data

    assert isinstance(data_model, VideoMetadataModel)
    assert data_model.title == "01 - Test Song"
    assert data_model.description == "Test description"
    assert data_model.tags == '["test", "song"]'
    assert data_model.game == "Test Game"
    assert data_model.made_for_kids is False
    assert data_model.contains_synthetic_media is False
    assert data_model.publish_at == "2026-09-17T18:00:00+00:00"
    assert data_model.thumbnail == "thumbnail.jpg"
    assert data_model.playlist is None


def test_to_model_maps_set_thumbnail():
    mapper = JobMapper()
    operation = create_set_thumbnail_operation()
    job = Job([operation])

    model = mapper.to_model(job)
    data_model = model.operations[0].data

    assert isinstance(data_model, VideoMetadataModel)
    assert data_model.thumbnail == "thumbnail.jpg"
    assert data_model.title is None
    assert data_model.description is None
    assert data_model.tags is None
    assert data_model.game is None
    assert data_model.made_for_kids is None
    assert data_model.contains_synthetic_media is None
    assert data_model.publish_at is None
    assert data_model.playlist is None


def test_to_model_maps_add_to_playlist():
    mapper = JobMapper()
    operation = create_add_to_playlist_operation()
    job = Job([operation])

    model = mapper.to_model(job)
    data_model = model.operations[0].data

    assert isinstance(data_model, VideoMetadataModel)
    assert data_model.playlist == "playlist-1"
    assert data_model.title is None
    assert data_model.description is None
    assert data_model.tags is None
    assert data_model.game is None
    assert data_model.made_for_kids is None
    assert data_model.contains_synthetic_media is None
    assert data_model.publish_at is None
    assert data_model.thumbnail is None


def test_to_domain_maps_pending_job():
    mapper = JobMapper()

    job_model = JobModel(status=JobStatus.PENDING.value)
    operation_model = OperationModel(
        operation_type=OperationType.UPDATE_METADATA.value,
        status=OperationStatus.PENDING.value,
    )
    operation_model.video = VideoModel(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG.value,
    )
    operation_model.data = VideoMetadataModel(
        title="01 - Test Song",
        description="Test description",
        tags='["test", "song"]',
        game="Test Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at="2026-09-17T18:00:00+00:00",
        thumbnail="thumbnail.jpg",
    )
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)

    assert isinstance(job, Job)
    assert job.status is JobStatus.PENDING
    assert len(job.operations) == 1


def test_to_domain_maps_video():
    mapper = JobMapper()

    video_model = VideoModel(
        video_id="video-123",
        position=2,
        video_type=VideoType.COMPILATION.value,
    )

    operation_model = OperationModel(
        operation_type=OperationType.ADD_TO_PLAYLIST.value,
        status=OperationStatus.PENDING.value,
    )
    operation_model.video = video_model
    operation_model.data = VideoMetadataModel(
        playlist="playlist-1",
    )

    job_model = JobModel(status=JobStatus.PENDING.value)
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)
    video = job.operations[0].video

    assert video.video_id == "video-123"
    assert video.position == 2
    assert video.video_type is VideoType.COMPILATION


def test_to_domain_maps_update_metadata():
    mapper = JobMapper()

    operation_model = OperationModel(
        operation_type=OperationType.UPDATE_METADATA.value,
        status=OperationStatus.PENDING.value,
    )
    operation_model.video = VideoModel(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG.value,
    )
    operation_model.data = VideoMetadataModel(
        title="01 - Test Song",
        description="Test description",
        tags='["test", "song"]',
        game="Test Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at="2026-09-17T18:00:00+00:00",
        thumbnail="thumbnail.jpg",
    )

    job_model = JobModel(status=JobStatus.PENDING.value)
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)
    metadata = job.operations[0].data

    assert isinstance(metadata, VideoMetadata)
    assert metadata.title == "01 - Test Song"
    assert metadata.description == "Test description"
    assert metadata.tags == ("test", "song")
    assert metadata.playlists == ()
    assert metadata.game == "Test Game"
    assert metadata.made_for_kids is False
    assert metadata.contains_synthetic_media is False
    assert metadata.publish_at == datetime(
        2026,
        9,
        17,
        18,
        0,
        tzinfo=timezone.utc,
    )
    assert metadata.thumbnail == Path("thumbnail.jpg")


def test_to_domain_maps_set_thumbnail():
    mapper = JobMapper()

    operation_model = OperationModel(
        operation_type=OperationType.SET_THUMBNAIL.value,
        status=OperationStatus.PENDING.value,
    )
    operation_model.video = VideoModel(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG.value,
    )
    operation_model.data = VideoMetadataModel(
        thumbnail="thumbnail.jpg",
    )

    job_model = JobModel(status=JobStatus.PENDING.value)
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)

    assert job.operations[0].data == Path("thumbnail.jpg")


def test_to_domain_maps_add_to_playlist():
    mapper = JobMapper()

    operation_model = OperationModel(
        operation_type=OperationType.ADD_TO_PLAYLIST.value,
        status=OperationStatus.PENDING.value,
    )
    operation_model.video = VideoModel(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG.value,
    )
    operation_model.data = VideoMetadataModel(
        playlist="playlist-1",
    )

    job_model = JobModel(status=JobStatus.PENDING.value)
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)

    assert job.operations[0].data == "playlist-1"


def test_to_domain_maps_completed_job():
    mapper = JobMapper()

    operation_model = OperationModel(
        operation_type=OperationType.ADD_TO_PLAYLIST.value,
        status=OperationStatus.COMPLETED.value,
    )
    operation_model.video = VideoModel(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG.value,
    )
    operation_model.data = VideoMetadataModel(
        playlist="playlist-1",
    )

    job_model = JobModel(status=JobStatus.COMPLETED.value)
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)

    assert job.status is JobStatus.COMPLETED
    assert job.operations[0].status is OperationStatus.COMPLETED


def test_to_domain_maps_failed_job():
    mapper = JobMapper()

    operation_model = OperationModel(
        operation_type=OperationType.ADD_TO_PLAYLIST.value,
        status=OperationStatus.FAILED.value,
    )
    operation_model.video = VideoModel(
        video_id="video-123",
        position=1,
        video_type=VideoType.SONG.value,
    )
    operation_model.data = VideoMetadataModel(
        playlist="playlist-1",
    )

    job_model = JobModel(status=JobStatus.FAILED.value)
    job_model.operations = [operation_model]

    job = mapper.to_domain(job_model)

    assert job.status is JobStatus.FAILED
    assert job.operations[0].status is OperationStatus.FAILED


def test_update_model_updates_existing_job():
    mapper = JobMapper()

    operation = create_update_metadata_operation()
    job = Job([operation])

    job_model = JobModel(
        id=42,
        status=JobStatus.RUNNING.value,
    )

    mapper.update_model(job_model, job)

    assert job_model.id == 42
    assert job_model.status == JobStatus.PENDING.value
    assert len(job_model.operations) == 1

    operation_model = job_model.operations[0]

    assert operation_model.operation_type == OperationType.UPDATE_METADATA.value
    assert operation_model.status == OperationStatus.PENDING.value


def test_update_model_replaces_existing_operations():
    mapper = JobMapper()

    old_operation = OperationModel(
        operation_type=OperationType.ADD_TO_PLAYLIST.value,
        status=OperationStatus.COMPLETED.value,
    )

    job_model = JobModel(
        id=42,
        status=JobStatus.RUNNING.value,
    )
    job_model.operations = [old_operation]

    new_operation = create_update_metadata_operation()
    job = Job([new_operation])

    mapper.update_model(job_model, job)

    assert len(job_model.operations) == 1
    assert job_model.operations[0] is not old_operation
    assert (
        job_model.operations[0].operation_type
        == OperationType.UPDATE_METADATA.value
    )