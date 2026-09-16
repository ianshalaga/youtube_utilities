# tests\services\youtube\test_album_builder.py

from datetime import datetime

import pytest

from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video import VideoType
from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo
from services.youtube.album_builder import (
    AlbumBuilder,
    AlbumBuildError,
)


# =============================================================================
# Helpers
# =============================================================================


def _create_manifest(
    *,
    videos: list[str] | None = None,
    description: str = "Album description",
    name_prefix: str = "Soul Edge / Blade OST",
    interval_days: int = 1,
) -> AlbumManifest:
    return AlbumManifest(
        name="Soul Edge",
        name_prefix=name_prefix,
        videos=videos
        or [
            "01 Opening Theme",
            "02 Battle Theme",
            "03 Ending Theme",
            "Super Battle Sound Attack",
        ],
        description=description,
        thumbnail=None,
        playlists=["PL_TEST"],
        made_for_kids=False,
        contains_synthetic_media=False,
        tags=["ost"],
        game="Soul Edge",
        publication=PublicationSettings(
            first_publish_at=datetime(2026, 10, 1, 18, 0),
            interval_days=interval_days,
        ),
    )


def _song(
    position: int,
    *,
    title: str | None = None,
    description: str | None = None,
) -> YouTubeVideo:
    title = title or f"{position:02d} Song {position}"

    return YouTubeVideo(
        video_id=f"video-{position}",
        title=title,
        description=description,
        privacy_status=PrivacyStatus.PRIVATE,
    )


def _compilation(
    *,
    title: str = "Super Battle Sound Attack",
    description: str | None = "Existing compilation description",
) -> YouTubeVideo:
    return YouTubeVideo(
        video_id="video-compilation",
        title=title,
        description=description,
        privacy_status=PrivacyStatus.PRIVATE,
    )


# =============================================================================
# Successful build
# =============================================================================


def test_builder_creates_album_from_manifest_and_youtube():
    manifest = _create_manifest(
        videos=[
            "01 Opening Theme",
            "02 Battle Theme",
            "03 Ending Theme",
            "Super Battle Sound Attack",
        ]
    )

    youtube_videos = (
        _compilation(),
        _song(3, title="03 Ending Theme"),
        _song(2, title="02 Battle Theme"),
        _song(1, title="01 Opening Theme"),
    )

    album = AlbumBuilder().build(
        manifest=manifest,
        youtube_videos=youtube_videos,
    )

    assert album.name == "Soul Edge"

    assert len(album.videos) == 4

    assert [video.position for video in album.videos] == [1, 2, 3, 4]

    assert [video.video_type for video in album.videos] == [
        VideoType.SONG,
        VideoType.SONG,
        VideoType.SONG,
        VideoType.COMPILATION,
    ]

    assert [video.video_id for video in album.videos] == [
        "video-1",
        "video-2",
        "video-3",
        "video-compilation",
    ]


# =============================================================================
# Metadata
# =============================================================================


def test_builder_builds_song_metadata_from_manifest():
    manifest = _create_manifest()

    youtube_videos = (
        _compilation(),
        _song(3, title="03 Ending Theme"),
        _song(2, title="02 Battle Theme"),
        _song(1, title="01 Opening Theme"),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    metadata = album.videos[0].metadata

    assert metadata.title == "Soul Edge / Blade OST: Opening Theme"
    assert metadata.description == "Album description"
    assert metadata.tags == ("ost",)
    assert metadata.playlists == ("PL_TEST",)
    assert metadata.game == "Soul Edge"
    assert metadata.made_for_kids is False
    assert metadata.contains_synthetic_media is False
    assert metadata.thumbnail is None


# =============================================================================
# Desired song titles
# =============================================================================


def test_builder_creates_prefixed_song_titles():
    manifest = _create_manifest()

    youtube_videos = (
        _compilation(),
        _song(3, title="03 Ending Theme"),
        _song(2, title="02 Battle Theme"),
        _song(1, title="01 Opening Theme"),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    titles = [video.metadata.title for video in album.videos]

    assert titles == [
        "Soul Edge / Blade OST: Opening Theme",
        "Soul Edge / Blade OST: Battle Theme",
        "Soul Edge / Blade OST: Ending Theme",
        "Super Battle Sound Attack",
    ]


def test_builder_matches_song_by_numeric_prefix():
    manifest = _create_manifest(
        videos=[
            "001 Opening Theme",
            "002 Battle Theme",
            "003 Ending Theme",
            "Super Battle Sound Attack",
        ]
    )

    youtube_videos = (
        _compilation(),
        _song(3, title="003 Ending Theme"),
        _song(2, title="002 Battle Theme"),
        _song(1, title="001 Opening Theme"),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    assert [video.position for video in album.videos] == [1, 2, 3, 4]

    assert [video.metadata.title for video in album.videos] == [
        "Soul Edge / Blade OST: Opening Theme",
        "Soul Edge / Blade OST: Battle Theme",
        "Soul Edge / Blade OST: Ending Theme",
        "Super Battle Sound Attack",
    ]


# =============================================================================
# Publication dates
# =============================================================================


def test_builder_calculates_publication_dates():
    manifest = _create_manifest(interval_days=2)

    youtube_videos = (
        _compilation(),
        _song(3),
        _song(2),
        _song(1),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    publish_dates = [
        video.metadata.publish_at
        for video in album.videos
    ]

    assert publish_dates == [
        datetime(2026, 10, 1, 18, 0),
        datetime(2026, 10, 3, 18, 0),
        datetime(2026, 10, 5, 18, 0),
        datetime(2026, 10, 7, 18, 0),
    ]


# =============================================================================
# Compilation metadata
# =============================================================================


def test_builder_preserves_compilation_title_from_youtube():
    manifest = _create_manifest()

    youtube_videos = (
        _compilation(),
        _song(3),
        _song(2),
        _song(1),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    compilation = album.videos[-1]

    assert compilation.video_type is VideoType.COMPILATION
    assert compilation.metadata.title == "Super Battle Sound Attack"


def test_builder_concatenates_compilation_description():
    manifest = _create_manifest(
        description="Desired album description."
    )

    youtube_videos = (
        _compilation(
            description="Existing compilation description."
        ),
        _song(3),
        _song(2),
        _song(1),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    compilation = album.videos[-1]

    assert compilation.metadata.description == (
        "Existing compilation description.\n\n"
        "Desired album description."
    )


def test_builder_keeps_compilation_description_when_limit_is_exceeded():
    existing = "A" * 4990
    desired = "B" * 100

    manifest = _create_manifest(description=desired)

    youtube_videos = (
        _compilation(description=existing),
        _song(3),
        _song(2),
        _song(1),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    compilation = album.videos[-1]

    assert compilation.metadata.description == existing


def test_builder_uses_empty_description_when_compilation_has_no_description():
    manifest = _create_manifest(
        description="Desired album description."
    )

    youtube_videos = (
        _compilation(description=None),
        _song(3),
        _song(2),
        _song(1),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    compilation = album.videos[-1]

    assert compilation.metadata.description == (
        "\n\nDesired album description."
    )


# =============================================================================
# Title length
# =============================================================================


def test_builder_shortens_song_title_by_removing_words():
    manifest = _create_manifest(
        name_prefix="Very Long Game Soundtrack Collection",
        videos=[
            "01 This Song Contains Many Many Many Words That Will Exceed "
            "The Maximum Title Length Allowed By YouTube",
            "Compilation",
        ],
    )

    youtube_videos = (
        _compilation(title="Compilation"),
        _song(
            1,
            title=(
                "01 This Song Contains Many Many Many Words That Will Exceed "
                "The Maximum Title Length Allowed By YouTube"
            ),
        ),
    )

    album = AlbumBuilder().build(manifest, youtube_videos)

    title = album.videos[0].metadata.title

    assert len(title) <= 100
    assert not title.endswith(" ")


# =============================================================================
# Validation errors
# =============================================================================


def test_builder_rejects_empty_youtube_discovery():
    manifest = _create_manifest()

    with pytest.raises(
        AlbumBuildError,
        match="No private YouTube videos were discovered",
    ):
        AlbumBuilder().build(
            manifest=manifest,
            youtube_videos=(),
        )


def test_builder_reports_missing_youtube_videos():
    manifest = _create_manifest()

    youtube_videos = (
        _compilation(),
        _song(2),
        _song(1),
    )

    with pytest.raises(AlbumBuildError) as exc:
        AlbumBuilder().build(manifest, youtube_videos)

    message = str(exc.value)

    assert "Missing from YouTube:" in message
    assert "03 Ending Theme" in message


def test_builder_reports_extra_youtube_videos():
    manifest = _create_manifest()

    youtube_videos = (
        _compilation(),
        _song(4, title="04 Extra Theme"),
        _song(3),
        _song(2),
        _song(1),
    )

    with pytest.raises(AlbumBuildError) as exc:
        AlbumBuilder().build(manifest, youtube_videos)

    message = str(exc.value)

    assert "Extra on YouTube:" in message
    assert "04 Extra Theme" in message


def test_builder_reports_missing_compilation():
    manifest = _create_manifest()

    youtube_videos = (
        _song(3),
        _song(2),
        _song(1),
    )

    with pytest.raises(AlbumBuildError) as exc:
        AlbumBuilder().build(manifest, youtube_videos)

    message = str(exc.value)

    assert "Missing from YouTube:" in message
    assert "Super Battle Sound Attack" in message


def test_builder_reports_unexpected_compilation():
    manifest = _create_manifest(
        videos=[
            "01 Opening Theme",
            "02 Battle Theme",
            "03 Ending Theme",
            "Expected Compilation",
        ]
    )

    youtube_videos = (
        _compilation(title="Super Battle Sound Attack"),
        _song(3),
        _song(2),
        _song(1),
    )

    with pytest.raises(AlbumBuildError) as exc:
        AlbumBuilder().build(manifest, youtube_videos)

    message = str(exc.value)

    assert "Extra on YouTube:" in message
    assert "Super Battle Sound Attack" in message