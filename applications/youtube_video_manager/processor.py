from pathlib import Path
from typing import Callable

from domain.youtube.job import Job
from domain.youtube.job_repository import JobRepository
from services.youtube.album_builder import AlbumBuilder
from services.youtube.planner import Planner
from services.youtube.youtube_discovery import YouTubeDiscovery
from services.youtube.updater import Updater
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.console import YouTubeConsole



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
    ) -> None:
        self._manifest_reader = manifest_reader
        self._youtube_discovery = youtube_discovery
        self._album_builder = album_builder
        self._planner = planner
        self._updater = updater
        self._job_repository = job_repository
        self._failure_action = failure_action
        self._console = console

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
        youtube_videos = self._youtube_discovery.discover(len(manifest.videos))

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
