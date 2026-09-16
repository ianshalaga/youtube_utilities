from datetime import datetime
from pathlib import Path

import pytest

from domain.youtube.job import Job, JobStatus
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from domain.youtube.operation import (
    Operation,
    OperationStatus,
    OperationType,
)


@pytest.fixture
def video_metadata() -> VideoMetadata:
    return VideoMetadata(
        title="Test title",
        description="Test description",
        tags=["tag1"],
        playlists=["playlist-1"],
        game="Test game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 1, 1, 12, 0),
        thumbnail=Path("thumbnail.jpg"),
    )


@pytest.fixture
def video(video_metadata: VideoMetadata) -> Video:
    return Video(
        video_id="video-id",
        position=1,
        video_type=VideoType.SONG,
        metadata=video_metadata,
    )


@pytest.fixture
def operation(video: Video, video_metadata: VideoMetadata) -> Operation:
    return Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=video_metadata,
    )


@pytest.fixture
def completed_operation(
    video: Video,
    video_metadata: VideoMetadata,
) -> Operation:
    operation = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=video_metadata,
    )
    operation.start()
    operation.complete()
    return operation


def test_job_statuses() -> None:
    assert JobStatus.PENDING.value == "pending"
    assert JobStatus.RUNNING.value == "running"
    assert JobStatus.COMPLETED.value == "completed"
    assert JobStatus.FAILED.value == "failed"


def test_job_requires_at_least_one_operation() -> None:
    with pytest.raises(
        ValueError,
        match="A job must contain at least one operation.",
    ):
        Job([])


def test_job_is_created_as_pending(operation: Operation) -> None:
    job = Job([operation])

    assert job.status is JobStatus.PENDING


def test_job_exposes_operations(operation: Operation) -> None:
    job = Job([operation])

    assert job.operations == (operation,)


def test_job_operations_are_immutable_from_outside(
    operation: Operation,
) -> None:
    operations = [operation]
    job = Job(operations)

    operations.clear()

    assert job.operations == (operation,)


def test_job_operations_property_returns_tuple(
    operation: Operation,
) -> None:
    job = Job([operation])

    assert isinstance(job.operations, tuple)


def test_start_changes_status_to_running(
    operation: Operation,
) -> None:
    job = Job([operation])

    job.start()

    assert job.status is JobStatus.RUNNING


def test_complete_changes_status_to_completed_when_all_operations_are_completed(
    completed_operation: Operation,
) -> None:
    job = Job([completed_operation])
    job.start()

    job.complete()

    assert job.status is JobStatus.COMPLETED


def test_complete_rejects_job_with_pending_operations(
    operation: Operation,
) -> None:
    job = Job([operation])
    job.start()

    with pytest.raises(
        ValueError,
        match="A job can only be completed when all operations are completed.",
    ):
        job.complete()

    assert job.status is JobStatus.RUNNING


def test_complete_rejects_job_with_running_operations(
    operation: Operation,
) -> None:
    operation.start()
    job = Job([operation])
    job.start()

    with pytest.raises(
        ValueError,
        match="A job can only be completed when all operations are completed.",
    ):
        job.complete()

    assert job.status is JobStatus.RUNNING


def test_complete_rejects_job_with_failed_operations(
    operation: Operation,
) -> None:
    operation.start()
    operation.fail()

    job = Job([operation])
    job.start()

    with pytest.raises(
        ValueError,
        match="A job can only be completed when all operations are completed.",
    ):
        job.complete()

    assert job.status is JobStatus.RUNNING


def test_fail_changes_status_to_failed(
    operation: Operation,
) -> None:
    job = Job([operation])
    job.start()

    job.fail()

    assert job.status is JobStatus.FAILED


@pytest.mark.parametrize(
    "status",
    [
        JobStatus.RUNNING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    ],
)
def test_start_rejects_non_pending_status(
    operation: Operation,
    status: JobStatus,
) -> None:
    job = Job([operation])

    if status is JobStatus.RUNNING:
        job.start()
    elif status is JobStatus.COMPLETED:
        operation.start()
        operation.complete()
        job.start()
        job.complete()
    else:
        job.start()
        job.fail()

    with pytest.raises(
        ValueError,
        match="Only pending jobs can be started.",
    ):
        job.start()


@pytest.mark.parametrize(
    "status",
    [
        JobStatus.PENDING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    ],
)
def test_complete_rejects_non_running_status(
    completed_operation: Operation,
    status: JobStatus,
) -> None:
    job = Job([completed_operation])

    if status is JobStatus.RUNNING:
        job.start()
    elif status is JobStatus.COMPLETED:
        job.start()
        job.complete()
    elif status is JobStatus.FAILED:
        job.start()
        job.fail()

    with pytest.raises(
        ValueError,
        match="Only running jobs can be completed.",
    ):
        job.complete()


@pytest.mark.parametrize(
    "status",
    [
        JobStatus.PENDING,
        JobStatus.COMPLETED,
        JobStatus.FAILED,
    ],
)
def test_fail_rejects_non_running_status(
    completed_operation: Operation,
    status: JobStatus,
) -> None:
    job = Job([completed_operation])

    if status is JobStatus.RUNNING:
        job.start()
    elif status is JobStatus.COMPLETED:
        job.start()
        job.complete()
    elif status is JobStatus.FAILED:
        job.start()
        job.fail()

    with pytest.raises(
        ValueError,
        match="Only running jobs can be failed.",
    ):
        job.fail()


def test_job_requires_all_operations_to_be_completed(
    video: Video,
    video_metadata: VideoMetadata,
) -> None:
    completed = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=video_metadata,
    )
    pending = Operation(
        video=video,
        operation_type=OperationType.SET_THUMBNAIL,
        data=Path("thumbnail.jpg"),
    )

    completed.start()
    completed.complete()

    job = Job([completed, pending])
    job.start()

    with pytest.raises(
        ValueError,
        match="A job can only be completed when all operations are completed.",
    ):
        job.complete()

    assert job.status is JobStatus.RUNNING
    assert completed.status is OperationStatus.COMPLETED
    assert pending.status is OperationStatus.PENDING