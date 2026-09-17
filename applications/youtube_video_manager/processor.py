from pathlib import Path
from typing import Callable, Protocol

from domain.youtube.album import Album
from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.job import Job
from services.youtube.album_builder import AlbumBuilder
from services.youtube.planner import Planner
from services.youtube.youtube_discovery import YouTubeDiscovery


class ManifestReader(Protocol):
    def read(self, path: Path) -> AlbumManifest:
        ...


class Updater(Protocol):
    def update(self, job: Job) -> None:
        ...


class JobRepository(Protocol):
    def find_pending(self) -> Job | None:
        ...

    def find_failed(self) -> Job | None:
        ...

    def save(self, job: Job) -> None:
        ...


class YouTubeVideoManagerProcessor:
    def __init__(
        self,
        manifest_reader: ManifestReader,
        youtube_discovery: YouTubeDiscovery,
        album_builder: AlbumBuilder,
        planner: Planner,
        updater: Updater,
        job_repository: JobRepository,
        failure_action: Callable[[], str],
    ) -> None:
        self._manifest_reader = manifest_reader
        self._youtube_discovery = youtube_discovery
        self._album_builder = album_builder
        self._planner = planner
        self._updater = updater
        self._job_repository = job_repository
        self._failure_action = failure_action

    def process(self, manifest_path: Path) -> None:
        job = self._job_repository.find_pending()

        if job is not None:
            self._updater.update(job)
            return

        job = self._job_repository.find_failed()

        if job is not None:
            action = self._failure_action()

            if action == "retry":
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

        self._updater.update(job)

    def _create_job(self, manifest_path: Path) -> Job:
        manifest = self._manifest_reader.read(manifest_path)
        youtube_videos = self._youtube_discovery.discover()

        album = self._album_builder.build(
            manifest,
            youtube_videos,
        )

        return self._planner.plan(album)
