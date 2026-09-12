from datetime import datetime

from domain.youtube.album import Album
from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from domain.youtube.publication_settings import PublicationSettings


def create_video(video_id: str, position: int) -> Video:
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


def create_album(videos: list[Video]) -> Album:
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
        )
    )


def create_manifest() -> AlbumManifest:
    """Create a minimal AlbumManifest for tests."""
    return AlbumManifest(
        name="Test Album",
        name_prefix="Test OST",
        videos=[
            "01 Opening Theme",
            "02 Battle Theme",
            "Test Compilation",
        ],
        description="Test album description",
        thumbnail=None,
        playlists=["PL_TEST"],
        made_for_kids=False,
        contains_synthetic_media=False,
        tags=None,
        game="Test Game",
        publication=PublicationSettings(
            first_publish_at=datetime(2026, 10, 1, 18, 0),
            interval_days=1,
        )
    )


def run_test(name: str, videos: list[Video]) -> None:
    """Run one album validation test and display its result."""
    album = create_album(videos)
    result = album.validate()

    print(f"\n=== {name} ===")
    print(f"Valid: {result.is_valid}")

    if result.is_valid:
        print("No validation errors.")
        return

    print(f"Errors: {len(result.errors)}")

    for error in result.errors:
        print(f"- [{error.field}] {error.message}")


def run_manifest_test() -> None:
    """Run the AlbumManifest test."""
    manifest = create_manifest()

    print("\n=== AlbumManifest ===")
    print(f"Name: {manifest.name}")
    print(f"Name prefix: {manifest.name_prefix}")
    print(f"Videos: {manifest.videos}")
    print(f"Description: {manifest.description}")
    print(f"Playlists: {manifest.playlists}")
    print(f"Made for kids: {manifest.made_for_kids}")
    print(f"Contains synthetic media: {manifest.contains_synthetic_media}")
    print(f"Tags: {manifest.tags}")
    print(f"Game: {manifest.game}")
    print(f"First publish at: {manifest.publication.first_publish_at}")
    print(f"Thumbnail: {manifest.thumbnail}")


def run_yaml_reader_test() -> None:
    """Test the complete YAML manifest reading pipeline."""

    from pathlib import Path
    from tempfile import TemporaryDirectory
    from textwrap import dedent

    from services.youtube.album_manifest.exceptions import (
        ManifestConfigurationError,
        ManifestParseError,
    )
    from services.youtube.album_manifest.yaml_reader import YamlReader

    reader = YamlReader()

    valid_manifest = dedent(
        """
        album: "Test Album"
        name_prefix: "Test Album"
        videos:
          - "Song One"
          - "Song Two"
        description: "Test album description."
        thumbnail: "C:/test/thumbnail.jpg"
        playlists:
          - "PL_TEST_001"
          - "PL_TEST_002"
        made_for_kids: false
        contains_synthetic_media: false
        tags:
          - "test"
          - "album"
        game: "Test Game"
        publication:
          first_publish_at: "2026-11-11T02:00:00+02:00"
          interval_days: 1
        """
    )

    with TemporaryDirectory() as temporary_directory:
        manifest_path = Path(temporary_directory) / "test_manifest.yaml"
        manifest_path.write_text(valid_manifest, encoding="utf-8")

        manifest = reader.read(manifest_path)

    print("\n=== YAML READER TEST ===")

    print(f"Name: {manifest.name}")
    print(f"Name prefix: {manifest.name_prefix}")
    print(f"Videos: {manifest.videos}")
    print(f"Description: {manifest.description}")
    print(f"Thumbnail: {manifest.thumbnail}")
    print(f"Playlists: {manifest.playlists}")
    print(f"Made for kids: {manifest.made_for_kids}")
    print(
        "Contains synthetic media: "
        f"{manifest.contains_synthetic_media}"
    )
    print(f"Tags: {manifest.tags}")
    print(f"Game: {manifest.game}")

    print("\nPublication:")
    print(
        f"  First publish at: "
        f"{manifest.publication.first_publish_at}"
    )
    print(
        f"  Interval days: "
        f"{manifest.publication.interval_days}"
    )

    print("\nTypes:")
    print(f"  Manifest: {type(manifest).__name__}")
    print(f"  Thumbnail: {type(manifest.thumbnail).__name__}")
    print(
        "  First publish at: "
        f"{type(manifest.publication.first_publish_at).__name__}"
    )
    print(f"  Publication: {type(manifest.publication).__name__}")

    print("\n=== EXPECTED CONVERSIONS ===")

    print(
        "Thumbnail is Path: "
        f"{isinstance(manifest.thumbnail, Path)}"
    )
    print(
        "First publish at is datetime: "
        f"{isinstance(manifest.publication.first_publish_at, datetime)}"
    )
    print(
        "Publication is PublicationSettings: "
        f"{isinstance(manifest.publication, PublicationSettings)}"
    )

    print("\n=== ERROR TEST: INVALID YAML ===")

    invalid_yaml = dedent(
        """
        album: "Test Album"
          invalid indentation
        """
    )

    try:
        with TemporaryDirectory() as temporary_directory:
            manifest_path = Path(temporary_directory) / "invalid.yaml"
            manifest_path.write_text(invalid_yaml, encoding="utf-8")

            reader.read(manifest_path)

    except ManifestParseError as exc:
        print(f"ManifestParseError correctly raised: {exc}")
    else:
        print("ERROR: ManifestParseError was not raised.")

    print("\n=== ERROR TEST: INVALID CONFIGURATION ===")

    invalid_configuration = dedent(
        """
        album: "Test Album"
        """
    )

    try:
        with TemporaryDirectory() as temporary_directory:
            manifest_path = (
                Path(temporary_directory)
                / "invalid_configuration.yaml"
            )
            manifest_path.write_text(
                invalid_configuration,
                encoding="utf-8",
            )

            reader.read(manifest_path)

    except ManifestConfigurationError as exc:
        print("ManifestConfigurationError correctly raised:")
        print(exc)
    else:
        print("ERROR: ManifestConfigurationError was not raised.")

    print("\n=== YAML READER TEST COMPLETE ===")


def main() -> None:
    run_manifest_test()

    run_test(
        "No duplicated positions",
        [
            create_video("video_01", 1),
            create_video("video_02", 2),
            create_video("video_03", 3),
            create_video("video_04", 4),
        ],
    )

    run_test(
        "One duplicated position",
        [
            create_video("video_01", 1),
            create_video("video_02", 2),
            create_video("video_03", 2),
            create_video("video_04", 3),
        ],
    )

    run_test(
        "Multiple duplicated positions",
        [
            create_video("video_01", 1),
            create_video("video_02", 2),
            create_video("video_03", 2),
            create_video("video_04", 3),
            create_video("video_05", 4),
            create_video("video_06", 4),
            create_video("video_07", 5),
            create_video("video_08", 5),
        ],
    )

    run_yaml_reader_test()
