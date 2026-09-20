from __future__ import annotations

from pathlib import Path

from domain.youtube.job import Job, JobStatus
from domain.youtube.job_repository import JobRepository
from domain.youtube.video_metadata import VideoMetadata
from domain.youtube.operation import (
    Operation,
    OperationStatus,
    OperationType,
)

from services.youtube.console import YouTubeConsole
from services.youtube.api.methods import (
    YouTubeMethods,
    YouTubeQuotaExceededError,
)


class Updater:
    """
    Executes the pending operations of a Job against YouTube.

    The Job already contains the desired data and the execution order.
    Updater only executes operations, manages execution state, handles
    retries and persists the resulting Job state.
    """

    def __init__(
        self,
        youtube_methods: YouTubeMethods,
        job_repository: JobRepository,
        console: YouTubeConsole,
        max_attempts: int = 3,
    ) -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least 1.")

        self._youtube_methods = youtube_methods
        self._job_repository = job_repository
        self._console = console
        self._max_attempts = max_attempts

    def update(self, job: Job) -> None:
        """
        Execute a Job from its current state.

        Completed operations are skipped. Pending operations are executed in
        their existing order until the Job completes, quota is exhausted, or
        an operation fails definitively.
        """
        if job.status is JobStatus.PENDING:
            job.start()
        elif job.status is not JobStatus.RUNNING:
            raise ValueError(
                "Only pending or running jobs can be updated."
            )

        video_order: dict[str, int] = {}

        for operation in job.operations:
            video_id = operation.video.video_id
            if video_id not in video_order:
                video_order[video_id] = len(video_order) + 1

        total_videos = len(video_order)
        current_video_id: str | None = None

        for operation in job.operations:
            if operation.status is OperationStatus.COMPLETED:
                continue

            if operation.video.video_id != current_video_id:
                current_video_id = operation.video.video_id
                self._console.video_started(
                    operation.video,
                    video_order[current_video_id],
                    total_videos,
                )

            if operation.status is not OperationStatus.PENDING:
                raise ValueError(
                    "A job can only contain pending or completed operations "
                    "during an update."
                )

            if self._execute_operation(job, operation):
                continue

            return

        job.complete()
        self._job_repository.save(job)
        self._console.job_completed()

    def _execute_operation(self, job: Job, operation: Operation) -> bool:
        """Execute one pending operation and return whether it completed."""
        operation.start()

        for attempt in range(1, self._max_attempts + 1):
            try:
                self._dispatch(operation)
            except YouTubeQuotaExceededError:
                operation.reset()
                job.reset()
                self._job_repository.save(job)
                self._console.job_quota_exceeded()
                return False
            except Exception as error:
                self._report_operation_failure(operation, attempt, error)

                if attempt == self._max_attempts:
                    operation.fail()
                    job.fail()
                    self._job_repository.save(job)
                    self._report_job_failure(operation, error)
                    self._console.job_failed()
                    return False

                # The operation remains RUNNING between normal retry attempts.
                # The next API call is another attempt of the same operation.
                continue
            else:
                operation.complete()
                return True

        raise RuntimeError("Unreachable execution state.")

    def _dispatch(self, operation: Operation) -> None:
        """Dispatch an operation to the corresponding YouTube API method."""
        if operation.operation_type is OperationType.UPDATE_METADATA:
            metadata = self._require_data(operation, VideoMetadata)
            self._youtube_methods.videos_update(
                video_resource=self._build_video_resource(
                    operation.video.video_id,
                    metadata,
                )
            )
            return

        if operation.operation_type is OperationType.SET_THUMBNAIL:
            thumbnail_path = self._require_data(operation, Path)
            self._youtube_methods.thumbnails_set(
                video_id=operation.video.video_id,
                thumbnail_path=thumbnail_path,
            )
            return

        if operation.operation_type is OperationType.ADD_TO_PLAYLIST:
            playlist_id = self._require_data(operation, str)
            self._youtube_methods.playlist_items_insert(
                playlist_item_resource={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": operation.video.video_id,
                        },
                    }
                }
            )
            return

        raise ValueError(
            f"Unsupported operation type: {operation.operation_type}."
        )

    @staticmethod
    def _require_data(
        operation: Operation,
        expected_type: type,
    ):
        data = operation.data
        if not isinstance(data, expected_type):
            raise TypeError(
                f"{operation.operation_type.value} requires "
                f"{expected_type.__name__} data."
            )
        return data

    @staticmethod
    def _build_video_resource(
        video_id: str,
        metadata: VideoMetadata,
    ) -> dict:
        """Adapt domain metadata to the YouTube videos.update resource."""
        # YouTube's "Video games" category is fixed for this application.
        # The game name remains part of the domain metadata for future use.
        VIDEO_GAMES_CATEGORY_ID = "20"

        snippet = {
            "title": metadata.title,
            "description": metadata.description,
            "tags": list(metadata.tags) if metadata.tags is not None else [],
            "categoryId": VIDEO_GAMES_CATEGORY_ID,
        }

        status = {
            "privacyStatus": "private",
            "publishAt": metadata.publish_at.isoformat(),
            "selfDeclaredMadeForKids": metadata.made_for_kids,
            "containsSyntheticMedia": metadata.contains_synthetic_media,
        }

        return {
            "id": video_id,
            "snippet": snippet,
            "status": status,
        }

    @staticmethod
    def _report_operation_failure(
        operation: Operation,
        attempt: int,
        error: Exception,
    ) -> None:
        print(
            f"Operation failed "
            f"(video={operation.video.video_id}, "
            f"type={operation.operation_type.value}, "
            f"attempt={attempt}): {error}"
        )

    @staticmethod
    def _report_job_failure(
        operation: Operation,
        error: Exception,
    ) -> None:
        print(
            f"Job failed on operation "
            f"(video={operation.video.video_id}, "
            f"type={operation.operation_type.value}): {error}"
        )
