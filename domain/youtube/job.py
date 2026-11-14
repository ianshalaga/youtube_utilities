# domain\youtube\job.py

from datetime import timedelta
from enum import Enum

from domain.youtube.operation import (
    Operation,
    OperationStatus,
    OperationType,
)
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video_metadata import VideoMetadata


class JobStatus(Enum):
    CREATED = "created"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job:
    def __init__(
        self,
        operations: list[Operation],
        publication: PublicationSettings | None = None,
        job_id: int | None = None,
        status: JobStatus = JobStatus.CREATED,
        name: str | None = None,
    ) -> None:
        if not operations:
            raise ValueError("A job must contain at least one operation.")

        self._operations = list(operations)
        self._publication = publication
        self._id = job_id
        self._name = name
        self._status = status

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def publication(self) -> PublicationSettings | None:
        return self._publication

    @property
    def name(self) -> str | None:
        return self._name

    def assign_id(self, job_id: int) -> None:
        if self._id is not None and self._id != job_id:
            raise ValueError("A persisted job ID cannot be changed.")
        self._id = job_id

    @property
    def operations(self) -> tuple[Operation, ...]:
        return tuple(self._operations)

    @property
    def status(self) -> JobStatus:
        return self._status

    def start(self) -> None:
        if self._status not in {JobStatus.CREATED, JobStatus.PENDING}:
            raise ValueError("Only created or pending jobs can be started.")

        self._status = JobStatus.RUNNING

    def complete(self) -> None:
        if self._status is not JobStatus.RUNNING:
            raise ValueError("Only running jobs can be completed.")

        if not all(
            operation.status is OperationStatus.COMPLETED
            for operation in self._operations
        ):
            raise ValueError(
                "A job can only be completed when all operations are completed."
            )

        self._status = JobStatus.COMPLETED

    def fail(self) -> None:
        if self._status is not JobStatus.RUNNING:
            raise ValueError("Only running jobs can be failed.")

        self._status = JobStatus.FAILED

    def reset(self) -> None:
        """Return a running job to pending after a quota interruption."""
        if self._status is not JobStatus.RUNNING:
            raise ValueError("Only running jobs can be reset.")

        self._status = JobStatus.PENDING

    def update_publication(self, publication: PublicationSettings) -> None:
        if self._status is not JobStatus.CREATED:
            raise ValueError("Only created jobs can be rescheduled.")
        if any(
            operation.status is not OperationStatus.PENDING
            for operation in self._operations
        ):
            raise ValueError("A created job cannot contain started operations.")

        for operation in self._operations:
            if operation.operation_type is not OperationType.UPDATE_METADATA:
                continue

            metadata = operation.data
            if not isinstance(metadata, VideoMetadata):
                raise TypeError(
                    "Metadata update operations must contain VideoMetadata."
                )

            publish_at = publication.first_publish_at + timedelta(
                days=(operation.video.position - 1)
                * publication.interval_days
            )
            operation.replace_data(
                VideoMetadata(
                    title=metadata.title,
                    description=metadata.description,
                    tags=(
                        list(metadata.tags)
                        if metadata.tags is not None
                        else None
                    ),
                    playlists=list(metadata.playlists),
                    game=metadata.game,
                    made_for_kids=metadata.made_for_kids,
                    contains_synthetic_media=metadata.contains_synthetic_media,
                    publish_at=publish_at,
                    thumbnail=metadata.thumbnail,
                )
            )

        self._publication = publication

    def recover_interrupted(self) -> None:
        if self._status is not JobStatus.RUNNING:
            raise ValueError("Only running jobs can be recovered.")

        if any(
            operation.status is OperationStatus.FAILED
            for operation in self._operations
        ):
            raise ValueError(
                "A running job cannot contain failed operations during recovery."
            )

        running_operations = [
            operation
            for operation in self._operations
            if operation.status is OperationStatus.RUNNING
        ]
        if len(running_operations) > 1:
            raise ValueError(
                "A running job can have at most one interrupted operation."
            )

        for operation in running_operations:
            operation.reset()

        self.reset()

    def retry(self) -> None:
        if self._status is not JobStatus.FAILED:
            raise ValueError("Only failed jobs can be retried.")

        failed_operations = [
            operation
            for operation in self._operations
            if operation.status is OperationStatus.FAILED
        ]

        if len(failed_operations) != 1:
            raise ValueError(
                "A failed job must contain exactly one failed operation to be retried."
            )

        failed_operations[0].retry()
        self._status = JobStatus.PENDING
