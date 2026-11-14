from datetime import datetime, timezone
from pathlib import Path

import pytest

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata


def create_metadata(publish_at: datetime) -> VideoMetadata:
    return VideoMetadata(
        title="Video title",
        description="Description",
        tags=["tag"],
        playlists=["playlist"],
        game="Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=publish_at,
        thumbnail=Path("thumbnail.jpg"),
    )


def create_metadata_operation(position: int) -> Operation:
    metadata = create_metadata(datetime(2026, 1, 1, tzinfo=timezone.utc))
    video = Video(
        video_id=f"video-{position}",
        position=position,
        video_type=VideoType.SONG,
        metadata=metadata,
    )
    return Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=metadata,
    )


def test_update_publication_recalculates_dates_by_video_position():
    operations = [create_metadata_operation(1), create_metadata_operation(4)]
    job = Job(
        operations,
        publication=PublicationSettings(
            first_publish_at=datetime(2026, 1, 1, 18, 0),
            timezone="UTC",
            interval_days=1,
        ),
    )
    new_publication = PublicationSettings(
        first_publish_at=datetime(2026, 11, 14, 9, 30),
        timezone="Europe/Paris",
        interval_days=3,
    )

    job.update_publication(new_publication)

    first_metadata = operations[0].data
    fourth_metadata = operations[1].data
    assert isinstance(first_metadata, VideoMetadata)
    assert isinstance(fourth_metadata, VideoMetadata)
    assert first_metadata.publish_at.isoformat() == "2026-11-14T09:30:00+01:00"
    assert fourth_metadata.publish_at.isoformat() == "2026-11-23T09:30:00+01:00"
    assert first_metadata.tags == ("tag",)
    assert first_metadata.playlists == ("playlist",)
    assert job.publication is new_publication


def test_update_publication_rejects_non_created_job():
    operation = create_metadata_operation(1)
    job = Job([operation], status=JobStatus.PENDING)

    with pytest.raises(ValueError, match="Only created jobs can be rescheduled."):
        job.update_publication(
            PublicationSettings(
                first_publish_at=datetime(2026, 11, 14, 9, 30),
                timezone="UTC",
                interval_days=1,
            )
        )


def test_recover_interrupted_resets_running_operation_and_job():
    operation = create_metadata_operation(1)
    operation.start()
    job = Job([operation], status=JobStatus.RUNNING)

    job.recover_interrupted()

    assert job.status is JobStatus.PENDING
    assert operation.status is OperationStatus.PENDING


def test_recover_interrupted_rejects_multiple_running_operations():
    operations = [create_metadata_operation(1), create_metadata_operation(2)]
    for operation in operations:
        operation.start()
    job = Job(operations, status=JobStatus.RUNNING)

    with pytest.raises(
        ValueError,
        match="A running job can have at most one interrupted operation.",
    ):
        job.recover_interrupted()
