from datetime import datetime

from domain.youtube.album import Album
from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata


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
        first_publish_at=datetime(2026, 10, 1, 18, 0),
        videos=videos,
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
        first_publish_at=datetime(2026, 10, 1, 18, 0),
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
    print(f"First publish at: {manifest.first_publish_at}")
    print(f"Thumbnail: {manifest.thumbnail}")


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
