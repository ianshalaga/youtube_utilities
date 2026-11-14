from pathlib import Path
from unittest.mock import Mock

import pytest

from applications.youtube_video_manager.processor import (
    YouTubeVideoManagerProcessor,
)
from domain.youtube.job import Job
from domain.youtube.job_repository import JobRepository
from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo
from services.youtube.album_builder import AlbumBuilder
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.console import YouTubeConsole
from services.youtube.planner import Planner
from services.youtube.updater import Updater
from services.youtube.video_id_overrides_reader import VideoIdOverridesReader
from services.youtube.youtube_discovery import (
    MissingYouTubeVideosError,
    YouTubeDiscovery,
)


@pytest.fixture
def manifest_path() -> Path:
    return Path("manifests/test.yaml")


@pytest.fixture
def manifest() -> Mock:
    value = Mock(name="manifest")
    value.videos = ("066 Existing title", "067 Manifest title")
    return value


@pytest.fixture
def dependencies():
    return {
        "manifest_reader": Mock(spec=YamlReader),
        "youtube_discovery": Mock(spec=YouTubeDiscovery),
        "album_builder": Mock(spec=AlbumBuilder),
        "planner": Mock(spec=Planner),
        "updater": Mock(spec=Updater),
        "job_repository": Mock(spec=JobRepository),
        "console": Mock(spec=YouTubeConsole),
        "video_id_overrides_reader": Mock(spec=VideoIdOverridesReader),
    }


@pytest.fixture
def processor(dependencies) -> YouTubeVideoManagerProcessor:
    return YouTubeVideoManagerProcessor(
        **dependencies,
        video_id_overrides_path=Path(
            "config/youtube/video_id_overrides.yaml"
        ),
    )


def test_create_and_save_job_builds_and_persists_job(
    processor,
    dependencies,
    manifest,
    manifest_path,
):
    youtube_videos = [Mock(name="youtube video")]
    album = Mock(name="album")
    job = Mock(spec=Job)
    dependencies["manifest_reader"].read.return_value = manifest
    dependencies["youtube_discovery"].discover.return_value = youtube_videos
    dependencies["album_builder"].build.return_value = album
    dependencies["planner"].plan.return_value = job

    result = processor.create_and_save_job(manifest_path)

    assert result is job
    dependencies["manifest_reader"].read.assert_called_once_with(manifest_path)
    dependencies["youtube_discovery"].discover.assert_called_once_with(
        expected_video_titles=manifest.videos,
    )
    dependencies["album_builder"].build.assert_called_once_with(
        manifest,
        youtube_videos,
    )
    dependencies["planner"].plan.assert_called_once_with(album)
    dependencies["job_repository"].save.assert_called_once_with(job)
    dependencies["console"].job_created.assert_called_once_with(job)


def test_missing_playlist_videos_are_resolved_from_id_overrides(
    processor,
    dependencies,
    manifest,
    manifest_path,
):
    playlist_video = YouTubeVideo(
        video_id="youtube-id-066",
        title="066 Existing title",
        description=None,
        privacy_status=PrivacyStatus.PRIVATE,
    )
    recovered_video = YouTubeVideo(
        video_id="youtube-id-067",
        title="067 Different YouTube title",
        description=None,
        privacy_status=PrivacyStatus.PRIVATE,
    )
    dependencies["manifest_reader"].read.return_value = manifest
    dependencies["youtube_discovery"].discover.side_effect = (
        MissingYouTubeVideosError(
            discovered_videos=(playlist_video,),
            missing_titles=("067 Manifest title",),
            message="Missing from uploads playlist",
        )
    )
    dependencies["video_id_overrides_reader"].read.return_value = {
        "067 Manifest title": "youtube-id-067"
    }
    dependencies["youtube_discovery"].discover_by_video_ids.return_value = (
        (recovered_video,),
        (),
    )
    album = Mock(name="album")
    job = Mock(spec=Job)
    dependencies["album_builder"].build.return_value = album
    dependencies["planner"].plan.return_value = job

    result = processor.create_and_save_job(manifest_path)

    assert result is job
    dependencies["console"].videos_missing_from_uploads.assert_called_once_with(
        ("067 Manifest title",)
    )
    dependencies["youtube_discovery"].discover_by_video_ids.assert_called_once_with(
        expected_titles=("067 Manifest title",),
        video_ids_by_title={"067 Manifest title": "youtube-id-067"},
    )
    dependencies["album_builder"].build.assert_called_once_with(
        manifest,
        (playlist_video, recovered_video),
    )
    dependencies["job_repository"].save.assert_called_once_with(job)


def test_creation_failure_is_reported_and_does_not_save_job(
    processor,
    dependencies,
    manifest_path,
):
    error = ValueError("Manifest unavailable")
    dependencies["manifest_reader"].read.side_effect = error

    result = processor.create_and_save_job(manifest_path)

    assert result is None
    dependencies["job_repository"].save.assert_not_called()
    dependencies["console"].job_creation_failed.assert_called_once_with(error)
