from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.video_metadata import VideoMetadata
from services.youtube.operations_builder import OperationsBuilder
from services.youtube.planner import Planner

def _operation(video_id: str, operation_type: OperationType) -> Operation:
    video = Mock()
    video.video_id = video_id

    if operation_type is OperationType.UPDATE_METADATA:
        data = VideoMetadata(
            title="Test title",
            description="Test description",
            tags=None,
            playlists=[],
            game="Test game",
            made_for_kids=False,
            contains_synthetic_media=False,
            publish_at=datetime(2026, 10, 1, 18, 0),
            thumbnail=None,
        )
    elif operation_type is OperationType.SET_THUMBNAIL:
        data = Path("thumbnail.jpg")
    else:
        data = "playlist-id"

    return Operation(
        video=video,
        operation_type=operation_type,
        data=data,
    )


def test_planner_builds_job_from_album_operations():
    album = Mock()
    operations = [
        _operation("video-1", OperationType.UPDATE_METADATA),
        _operation("video-1", OperationType.ADD_TO_PLAYLIST),
    ]

    operations_builder = Mock(spec=OperationsBuilder)
    operations_builder.build.return_value = operations

    planner = Planner(operations_builder)

    job = planner.plan(album)

    assert isinstance(job, Job)
    assert job.operations == tuple(operations)
    assert job.status is JobStatus.PENDING


def test_planner_delegates_operation_creation_to_operations_builder():
    album = Mock()
    operations = [
        _operation("video-1", OperationType.UPDATE_METADATA),
    ]

    operations_builder = Mock(spec=OperationsBuilder)
    operations_builder.build.return_value = operations

    planner = Planner(operations_builder)

    planner.plan(album)

    operations_builder.build.assert_called_once_with(album)
    

def test_planner_preserves_operation_order():
    album = Mock()
    operations = [
        _operation("video-1", OperationType.UPDATE_METADATA),
        _operation("video-1", OperationType.SET_THUMBNAIL),
        _operation("video-1", OperationType.ADD_TO_PLAYLIST),
        _operation("video-2", OperationType.UPDATE_METADATA),
    ]

    operations_builder = Mock(spec=OperationsBuilder)
    operations_builder.build.return_value = operations

    planner = Planner(operations_builder)

    job = planner.plan(album)

    assert list(job.operations) == operations


def test_planner_does_not_modify_operations():
    album = Mock()
    operations = [
        _operation("video-1", OperationType.UPDATE_METADATA),
        _operation("video-1", OperationType.SET_THUMBNAIL),
    ]

    operations_builder = Mock(spec=OperationsBuilder)
    operations_builder.build.return_value = operations

    planner = Planner(operations_builder)

    planner.plan(album)

    assert all(
        operation.status is OperationStatus.PENDING
        for operation in operations
    )


def test_planner_propagates_operations_builder_errors():
    album = Mock()
    error = RuntimeError("Unable to build operations.")

    operations_builder = Mock(spec=OperationsBuilder)
    operations_builder.build.side_effect = error

    planner = Planner(operations_builder)

    with pytest.raises(RuntimeError, match="Unable to build operations."):
        planner.plan(album)
