from pathlib import Path

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import OperationStatus, OperationType
from domain.youtube.job_repository import JobRepository
from domain.youtube.publication_settings import PublicationSettings
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
        self._console = console
        self._video_id_overrides_reader = video_id_overrides_reader
        self._video_id_overrides_path = video_id_overrides_path

    def list_jobs(self) -> list[Job]:
        self._job_repository.delete_completed()
        return self._job_repository.find_selectable()

    def get_job(self, job_id: int) -> Job | None:
        return self._job_repository.find_by_id(job_id)

    def create_and_save_job(self, manifest_path: Path) -> Job | None:
        try:
            job = self._create_job(manifest_path)
            self._job_repository.save(job)
        except Exception as error:
            self._console.job_creation_failed(error)
            return None

        self._console.job_created(job)
        return job

    def start_created_job(
        self,
        job: Job,
        publication: PublicationSettings,
    ) -> None:
        if job.status is not JobStatus.CREATED:
            raise ValueError("Only created jobs can be started here.")
        job.update_publication(publication)
        self._job_repository.save(job)
        self._console.publication_updated(job)
        self._console.created_job_starting(job)
        self._updater.update(job)

    def continue_pending_job(self, job: Job) -> None:
        if job.status is not JobStatus.PENDING:
            raise ValueError("Only pending jobs can be continued.")
        self._console.existing_job()
        self._updater.update(job)

    def retry_failed_job(self, job: Job) -> None:
        if job.status is not JobStatus.FAILED:
            raise ValueError("Only failed jobs can be retried.")
        self._console.retrying_job()
        job.retry()
        self._updater.update(job)

    def update_failed_thumbnail_and_retry(
        self,
        job: Job,
        thumbnail_path: Path,
    ) -> None:
        if job.status is not JobStatus.FAILED:
            raise ValueError("Only failed jobs can update a thumbnail path.")

        failed_operations = [
            operation
            for operation in job.operations
            if operation.status is OperationStatus.FAILED
        ]
        if (
            len(failed_operations) != 1
            or failed_operations[0].operation_type
            is not OperationType.SET_THUMBNAIL
        ):
            raise ValueError(
                "The failed job must have exactly one failed thumbnail operation."
            )

        job.retry_with_data(thumbnail_path)
        self._console.retrying_job()
        self._updater.update(job)

    def recover_running_job(self, job: Job) -> None:
        if job.status is not JobStatus.RUNNING:
            raise ValueError("Only running jobs can be recovered.")
        job.recover_interrupted()
        self._job_repository.save(job)
        self._console.running_job_recovery_started(job)
        self._updater.update(job)

    def delete_job(self, job: Job) -> None:
        self._job_repository.delete(job)
        self._console.job_deleted(job)

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
