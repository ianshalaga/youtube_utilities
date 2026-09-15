# tests\domain\youtube\test_album.py

from datetime import datetime

import pytest

from domain.youtube.album import Album
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata


def _create_video(video_id: str, position: int) -> Video:
    """Create a minimal Video for validation tests."""
    metadata = VideoMetadata(
        title=f"Video {position}",
        description="Test description",
        tags=None,
        playlists=["PL_TEST"],
        game="Test Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 10, 1, 18, 0),
        thumbnail=None,
    )

    return Video(
        video_id=video_id,
        position=position,
        video_type=VideoType.SONG,
        current_metadata=metadata,
        desired_metadata=metadata,
    )


def _create_album(videos: list[Video]) -> Album:
    """Create a minimal Album for validation tests."""
    return Album(
        name="Test Album",
        description="Test album description",
        playlists=["PL_TEST"],
        game="Test Game",
        videos=videos,
        publication=PublicationSettings(
            first_publish_at=datetime(2026, 10, 1, 18, 0),
            interval_days=1,
        ),
    )


@pytest.mark.parametrize(
    "positions, expected_valid",
    [
        ([1, 2, 3, 4], True),
        ([1, 2, 2, 3], False),
        ([1, 2, 2, 3, 4, 4, 5, 5], False),
    ],
)
def test_album_validates_video_positions(positions, expected_valid):
    videos = [
        _create_video(f"video_{index:02d}", position)
        for index, position in enumerate(positions, start=1)
    ]

    album = _create_album(videos)

    result = album.validate()

    assert result.is_valid is expected_valid


def test_album_rejects_duplicated_position():
    album = _create_album(
        [
            _create_video("video_01", 1),
            _create_video("video_02", 2),
            _create_video("video_03", 2),
            _create_video("video_04", 3),
        ]
    )

    result = album.validate()

    assert not result.is_valid
    assert any(
        error.field == "videos.position[2]"
        for error in result.errors
    )


def test_album_reports_multiple_duplicated_positions():
    album = _create_album(
        [
            _create_video("video_01", 1),
            _create_video("video_02", 2),
            _create_video("video_03", 2),
            _create_video("video_04", 3),
            _create_video("video_05", 4),
            _create_video("video_06", 4),
            _create_video("video_07", 5),
            _create_video("video_08", 5),
        ]
    )

    result = album.validate()

    assert not result.is_valid
    assert len(result.errors) == 3
    assert {error.field for error in result.errors} == {
        "videos.position[2]",
        "videos.position[4]",
        "videos.position[5]",
    }