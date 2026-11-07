from pathlib import Path
from typing import Callable

from domain.youtube.job import Job
from domain.youtube.job_repository import JobRepository
from services.youtube.album_builder import AlbumBuilder
from services.youtube.planner import Planner
from services.youtube.youtube_discovery import (
    MissingYouTubeVideosError,
    YouTubeDiscovery,
)
from services.youtube.updater import Updater
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.console import YouTubeConsole
from services.youtube.video_id_overrides_reader import (
    VideoIdOverridesError,
    VideoIdOverridesReader,
)


class YouTubeVideoManagerProcessor:
    def __init__(
        self,
        manifest_reader: YamlReader,
        youtube_discovery: YouTubeDiscovery,
        album_builder: AlbumBuilder,
        planner: Planner,
        updater: Updater,
        job_repository: JobRepository,
        failure_action: Callable[[], str],
        console: YouTubeConsole,
        video_id_overrides_reader: VideoIdOverridesReader,
        video_id_overrides_path: Path,
    ) -> None:
        self._manifest_reader = manifest_reader
        self._youtube_discovery = youtube_discovery
        self._album_builder = album_builder
        self._planner = planner
        self._updater = updater
        self._job_repository = job_repository
        self._failure_action = failure_action
        self._console = console
        self._video_id_overrides_reader = video_id_overrides_reader
        self._video_id_overrides_path = video_id_overrides_path

    def process(self, manifest_path: Path) -> None:
        job = self._job_repository.find_pending()

        if job is not None:
            self._console.existing_job()
            self._updater.update(job)
            return

        job = self._job_repository.find_failed()

        if job is not None:
            action = self._failure_action()

            if action == "retry":
                self._console.retrying_job()
                job.retry()
                self._job_repository.save(job)
                self._updater.update(job)
                return

            if action == "discard":
                job = None
            else:
                raise ValueError(
                    "Invalid action for failed job. Expected 'retry' or 'discard'."
                )

        if job is None:
            job = self._create_job(manifest_path)
            self._console.new_job()

        self._updater.update(job)

    def _create_job(self, manifest_path: Path) -> Job:
        manifest = self._manifest_reader.read(manifest_path)

        try:
            youtube_videos = self._youtube_discovery.discover(
                expected_video_titles=manifest.videos,
            )
        except MissingYouTubeVideosError as error:
            self._console.videos_missing_from_uploads(error.missing_titles)
            self._console.video_id_fallback_started(
                self._video_id_overrides_path
            )

            try:
                video_ids = self._video_id_overrides_reader.read(
                    self._video_id_overrides_path
                )
            except VideoIdOverridesError as read_error:
                self._console.video_id_fallback_error(str(read_error))
                raise

            fallback_videos, unresolved_titles = (
                self._youtube_discovery.discover_by_video_ids(
                    expected_titles=error.missing_titles,
                    video_ids_by_title=video_ids,
                )
            )
            resolved_titles = tuple(
                title
                for title in error.missing_titles
                if title not in unresolved_titles
            )
            self._console.video_id_fallback_resolved(
                resolved_titles
            )

            if unresolved_titles:
                self._console.video_id_fallback_failed(
                    unresolved_titles,
                    self._video_id_overrides_path,
                )
                raise RuntimeError(
                    "Unable to resolve all missing videos by ID: "
                    + ", ".join(unresolved_titles)
                ) from error

            youtube_videos = error.discovered_videos + fallback_videos
        
        # DEPURATION
        # print("\n=== YOUTUBE DISCOVERY ===")

        # for video in youtube_videos:
        #     print(
        #         f"{video.video_id} | "
        #         f"{video.privacy_status.value} | "
        #         f"{video.title!r}"
        #     )

        # print("=========================\n")

        album = self._album_builder.build(
            manifest,
            youtube_videos,
        )

        return self._planner.plan(album)
