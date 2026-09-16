from datetime import datetime
from pathlib import Path

import pytest

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
        tags=["tag1", "tag2"],
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


def test_operation_types() -> None:
    assert OperationType.UPDATE_METADATA.value == "update_metadata"
    assert OperationType.SET_THUMBNAIL.value == "set_thumbnail"
    assert OperationType.ADD_TO_PLAYLIST.value == "add_to_playlist"


def test_operation_statuses() -> None:
    assert OperationStatus.PENDING.value == "pending"
    assert OperationStatus.RUNNING.value == "running"
    assert OperationStatus.COMPLETED.value == "completed"
    assert OperationStatus.FAILED.value == "failed"


def test_operation_is_created_as_pending(video: Video, video_metadata: VideoMetadata) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    assert operation.status is OperationStatus.PENDING


def test_operation_exposes_video_type_and_data(video: Video, video_metadata: VideoMetadata) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    assert operation.video is video
    assert operation.operation_type is OperationType.UPDATE_METADATA
    assert operation.data is video_metadata


def test_start_changes_status_to_running(video: Video, video_metadata: VideoMetadata) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    operation.start()
    assert operation.status is OperationStatus.RUNNING


def test_complete_changes_status_to_completed(video: Video, video_metadata: VideoMetadata) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    operation.start()
    operation.complete()
    assert operation.status is OperationStatus.COMPLETED


def test_fail_changes_status_to_failed(video: Video, video_metadata: VideoMetadata) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    operation.start()
    operation.fail()
    assert operation.status is OperationStatus.FAILED


@pytest.mark.parametrize("status", [OperationStatus.RUNNING, OperationStatus.COMPLETED, OperationStatus.FAILED])
def test_start_rejects_non_pending_status(video: Video, video_metadata: VideoMetadata, status: OperationStatus) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    if status is OperationStatus.RUNNING:
        operation.start()
    elif status is OperationStatus.COMPLETED:
        operation.start(); operation.complete()
    else:
        operation.start(); operation.fail()
    with pytest.raises(ValueError, match="Only pending operations can be started."):
        operation.start()


@pytest.mark.parametrize("status", [OperationStatus.PENDING, OperationStatus.COMPLETED, OperationStatus.FAILED])
def test_complete_rejects_non_running_status(video: Video, video_metadata: VideoMetadata, status: OperationStatus) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    if status is OperationStatus.RUNNING:
        operation.start()
    elif status is OperationStatus.COMPLETED:
        operation.start(); operation.complete()
    else:
        operation.start(); operation.fail()
    with pytest.raises(ValueError, match="Only running operations can be completed."):
        operation.complete()


@pytest.mark.parametrize("status", [OperationStatus.PENDING, OperationStatus.COMPLETED, OperationStatus.FAILED])
def test_fail_rejects_non_running_status(video: Video, video_metadata: VideoMetadata, status: OperationStatus) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    if status is OperationStatus.RUNNING:
        operation.start()
    elif status is OperationStatus.COMPLETED:
        operation.start(); operation.complete()
    else:
        operation.start(); operation.fail()
    with pytest.raises(ValueError, match="Only running operations can be failed."):
        operation.fail()


def test_update_metadata_accepts_video_metadata(video: Video, video_metadata: VideoMetadata) -> None:
    operation = Operation(video, OperationType.UPDATE_METADATA, video_metadata)
    assert operation.data is video_metadata


def test_set_thumbnail_accepts_path(video: Video) -> None:
    thumbnail = Path("thumbnail.jpg")
    operation = Operation(video, OperationType.SET_THUMBNAIL, thumbnail)
    assert operation.data is thumbnail


def test_add_to_playlist_accepts_string(video: Video) -> None:
    playlist = "playlist-id"
    operation = Operation(video, OperationType.ADD_TO_PLAYLIST, playlist)
    assert operation.data == playlist


@pytest.mark.parametrize(
    ("operation_type", "data"),
    [
        (OperationType.UPDATE_METADATA, Path("thumbnail.jpg")),
        (OperationType.UPDATE_METADATA, "playlist-id"),
        (OperationType.SET_THUMBNAIL, "playlist-id"),
        (OperationType.SET_THUMBNAIL, object()),
        (OperationType.ADD_TO_PLAYLIST, Path("thumbnail.jpg")),
        (OperationType.ADD_TO_PLAYLIST, object()),
    ],
)
def test_operation_rejects_invalid_data_type(video: Video, operation_type: OperationType, data: object) -> None:
    with pytest.raises(TypeError):
        Operation(video, operation_type, data)