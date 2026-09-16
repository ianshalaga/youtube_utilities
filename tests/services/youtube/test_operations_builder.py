# tests\services\youtube\test_operations_builder.py

from datetime import datetime
from pathlib import Path

import pytest

from domain.youtube.album import Album
from domain.youtube.operation import OperationStatus, OperationType
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from services.youtube.operations_builder import OperationsBuilder


def _metadata(
    *,
    title: str = "Test video",
    thumbnail: Path | None = None,
    playlists: list[str] | None = None,
) -> VideoMetadata:
    return VideoMetadata(
        title=title,
        description="Test description",
        tags=["test"],
        playlists=playlists if playlists is not None else ["PL_TEST"],
        game="Test Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 10, 1, 18, 0),
        thumbnail=thumbnail,
    )


def _video(
    video_id: str = "video-1",
    position: int = 1,
    *,
    metadata: VideoMetadata | None = None,
) -> Video:
    metadata = metadata or _metadata()

    return Video(
        video_id=video_id,
        position=position,
        video_type=VideoType.SONG,
        metadata=metadata,
    )


def _album(videos: list[Video]) -> Album:
    return Album(
        name="Test Album",
        description="Test album description",
        playlists=["PL_TEST"],
        game="Test Game",
        publication=_publication(),
        tags=["test"],
        thumbnail=None,
        videos=videos,
    )


def _publication():
    from domain.youtube.publication_settings import PublicationSettings

    return PublicationSettings(
        first_publish_at=datetime(2026, 10, 1, 18, 0),
        interval_days=1,
    )


def test_builder_rejects_empty_album():
    album = _album([])

    with pytest.raises(
        ValueError,
        match="Cannot build operations for an empty album.",
    ):
        OperationsBuilder().build(album)


def test_builder_creates_update_metadata_operation_for_each_video():
    metadata_1 = _metadata(title="Video 1", playlists=[])
    metadata_2 = _metadata(title="Video 2", playlists=[])

    video_1 = _video("video-1", 1, metadata=metadata_1)
    video_2 = _video("video-2", 2, metadata=metadata_2)

    operations = OperationsBuilder().build(_album([video_1, video_2]))

    update_operations = [
        operation
        for operation in operations
        if operation.operation_type is OperationType.UPDATE_METADATA
    ]

    assert len(update_operations) == 2
    assert update_operations[0].video is video_1
    assert update_operations[0].data is metadata_1
    assert update_operations[1].video is video_2
    assert update_operations[1].data is metadata_2


def test_builder_creates_thumbnail_operation_when_thumbnail_exists():
    thumbnail = Path("thumbnail.jpg")
    metadata = _metadata(thumbnail=thumbnail, playlists=[])

    video = _video(metadata=metadata)

    operations = OperationsBuilder().build(_album([video]))

    assert len(operations) == 2

    thumbnail_operation = operations[1]

    assert thumbnail_operation.operation_type is OperationType.SET_THUMBNAIL
    assert thumbnail_operation.video is video
    assert thumbnail_operation.data == thumbnail


def test_builder_does_not_create_thumbnail_operation_when_thumbnail_is_none():
    metadata = _metadata(thumbnail=None, playlists=[])

    video = _video(metadata=metadata)

    operations = OperationsBuilder().build(_album([video]))

    assert len(operations) == 1
    assert operations[0].operation_type is OperationType.UPDATE_METADATA


def test_builder_creates_one_playlist_operation_per_playlist():
    metadata = _metadata(
        playlists=["PL_ONE", "PL_TWO", "PL_THREE"],
    )
    video = _video(metadata=metadata)

    operations = OperationsBuilder().build(_album([video]))

    playlist_operations = [
        operation
        for operation in operations
        if operation.operation_type is OperationType.ADD_TO_PLAYLIST
    ]

    assert [operation.data for operation in playlist_operations] == [
        "PL_ONE",
        "PL_TWO",
        "PL_THREE",
    ]

    assert all(operation.video is video for operation in playlist_operations)


def test_builder_preserves_video_and_operation_order():
    metadata_1 = _metadata(
        title="Video 1",
        thumbnail=Path("video-1.jpg"),
        playlists=["PL_ONE", "PL_TWO"],
    )
    metadata_2 = _metadata(
        title="Video 2",
        thumbnail=None,
        playlists=["PL_THREE"],
    )

    video_1 = _video("video-1", 1, metadata=metadata_1)
    video_2 = _video("video-2", 2, metadata=metadata_2)

    operations = OperationsBuilder().build(_album([video_1, video_2]))

    assert [
        (operation.video.video_id, operation.operation_type, operation.data)
        for operation in operations
    ] == [
        ("video-1", OperationType.UPDATE_METADATA, metadata_1),
        ("video-1", OperationType.SET_THUMBNAIL, Path("video-1.jpg")),
        ("video-1", OperationType.ADD_TO_PLAYLIST, "PL_ONE"),
        ("video-1", OperationType.ADD_TO_PLAYLIST, "PL_TWO"),
        ("video-2", OperationType.UPDATE_METADATA, metadata_2),
        ("video-2", OperationType.ADD_TO_PLAYLIST, "PL_THREE"),
    ]


def test_builder_creates_all_operations_as_pending():
    metadata = _metadata(
        thumbnail=Path("thumbnail.jpg"),
        playlists=["PL_ONE", "PL_TWO"],
    )
    video = _video(metadata=metadata)

    operations = OperationsBuilder().build(_album([video]))

    assert operations
    assert all(
        operation.status is OperationStatus.PENDING
        for operation in operations
    )