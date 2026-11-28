import json
from datetime import datetime, timezone
from pathlib import Path

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import (
    Operation,
    OperationData,
    OperationStatus,
    OperationType,
)
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata

from services.youtube.storage.models.job import JobModel
from services.youtube.storage.models.operation import OperationModel
from services.youtube.storage.models.video import VideoModel
from services.youtube.storage.models.video_metadata import VideoMetadataModel


class JobMapper:
    def to_model(self, job: Job) -> JobModel:
        job_model = JobModel(
            status=job.status.value,
            name=job.name,
        )
        self._publication_to_model(job_model, job)

        videos_by_id: dict[str, VideoModel] = {}

        job_model.operations = [
            self._operation_to_model(operation, videos_by_id, job_model)
            for operation in job.operations
        ]

        return job_model

    def update_model(self, job_model: JobModel, job: Job) -> None:
        job_model.status = job.status.value
        job_model.name = job.name
        self._publication_to_model(job_model, job)

        videos_by_id: dict[str, VideoModel] = {
            operation.video.video_id: operation.video
            for operation in job_model.operations
            if operation.video is not None
        }

        job_model.operations = [
            self._operation_to_model(operation, videos_by_id, job_model)
            for operation in job.operations
        ]

    def to_domain(self, job_model: JobModel) -> Job:
        operations = [
            self._operation_to_domain(operation_model)
            for operation_model in job_model.operations
        ]

        publication = None
        if (
            job_model.first_publish_at is not None
            and job_model.interval_days is not None
            and job_model.timezone is not None
        ):
            publication = PublicationSettings(
                first_publish_at=datetime.fromisoformat(
                    job_model.first_publish_at
                ).replace(tzinfo=None),
                timezone=job_model.timezone,
                interval_days=job_model.interval_days,
            )

        return Job(
            operations,
            publication=publication,
            job_id=job_model.id,
            status=JobStatus(job_model.status),
            name=job_model.name,
        )

    @staticmethod
    def _publication_to_model(job_model: JobModel, job: Job) -> None:
        publication = job.publication
        if publication is None:
            job_model.first_publish_at = None
            job_model.interval_days = None
            job_model.timezone = None
            return

        job_model.first_publish_at = publication.first_publish_at.replace(
            tzinfo=None
        ).isoformat()
        job_model.interval_days = publication.interval_days
        job_model.timezone = publication.timezone.key

    def _operation_to_model(
        self,
        operation: Operation,
        videos_by_id: dict[str, VideoModel],
        job_model: JobModel,
    ) -> OperationModel:
        operation_model = OperationModel(
            operation_type=operation.operation_type.value,
            status=operation.status.value,
        )

        video = videos_by_id.get(operation.video.video_id)
        
        if video is None:
            video = self._video_to_model(operation.video, job_model)
            videos_by_id[operation.video.video_id] = video

        operation_model.video = video
        operation_model.data = self._data_to_model(
            operation.operation_type,
            operation.data,
        )

        return operation_model

    def _operation_to_domain(
        self,
        operation_model: OperationModel,
    ) -> Operation:
        video = self._video_to_domain(operation_model.video)

        data = self._data_to_domain(
            operation_model.operation_type,
            operation_model.data,
        )

        operation = Operation(
            video=video,
            operation_type=OperationType(operation_model.operation_type),
            data=data,
        )

        if operation_model.status == OperationStatus.RUNNING.value:
            operation.start()
        elif operation_model.status == OperationStatus.COMPLETED.value:
            operation.start()
            operation.complete()
        elif operation_model.status == OperationStatus.FAILED.value:
            operation.start()
            operation.fail()

        return operation

    def _video_to_model(
        self,
        video: Video,
        job_model: JobModel,
    ) -> VideoModel:
        return VideoModel(
            job=job_model,
            video_id=video.video_id,
            position=video.position,
            video_type=video.video_type.value,
        )

    def _video_to_domain(self, video_model: VideoModel) -> Video:
        return Video(
            video_id=video_model.video_id,
            position=video_model.position,
            video_type=VideoType(video_model.video_type),
            metadata=VideoMetadata(
                title="",
                description="",
                tags=None,
                playlists=[],
                game="",
                made_for_kids=False,
                contains_synthetic_media=False,
                publish_at=datetime.min.replace(tzinfo=timezone.utc),
                thumbnail=None,
            ),
        )

    def _data_to_model(
        self,
        operation_type: OperationType,
        data: OperationData,
    ) -> VideoMetadataModel:
        if operation_type is OperationType.UPDATE_METADATA:
            metadata = data

            return VideoMetadataModel(
                title=metadata.title,
                description=metadata.description,
                tags=(
                    json.dumps(metadata.tags)
                    if metadata.tags is not None
                    else None
                ),
                game=metadata.game,
                made_for_kids=metadata.made_for_kids,
                contains_synthetic_media=metadata.contains_synthetic_media,
                publish_at=metadata.publish_at.isoformat(),
                thumbnail=(
                    str(metadata.thumbnail)
                    if metadata.thumbnail is not None
                    else None
                ),
            )

        if operation_type is OperationType.SET_THUMBNAIL:
            return VideoMetadataModel(
                thumbnail=str(data),
            )

        if operation_type is OperationType.ADD_TO_PLAYLIST:
            return VideoMetadataModel(
                playlist=data,
            )

        raise ValueError(
            f"Unsupported operation type: {operation_type}"
        )

    def _data_to_domain(
        self,
        operation_type: str,
        data_model: VideoMetadataModel,
    ) -> OperationData:
        operation_type = OperationType(operation_type)

        if operation_type is OperationType.UPDATE_METADATA:
            tags = (
                json.loads(data_model.tags)
                if data_model.tags is not None
                else None
            )

            return VideoMetadata(
                title=data_model.title,
                description=data_model.description,
                tags=tags,
                playlists=[],
                game=data_model.game,
                made_for_kids=data_model.made_for_kids,
                contains_synthetic_media=data_model.contains_synthetic_media,
                publish_at=datetime.fromisoformat(data_model.publish_at),
                thumbnail=(
                    Path(data_model.thumbnail)
                    if data_model.thumbnail is not None
                    else None
                ),
            )

        if operation_type is OperationType.SET_THUMBNAIL:
            return Path(data_model.thumbnail)

        if operation_type is OperationType.ADD_TO_PLAYLIST:
            return data_model.playlist

        raise ValueError(
            f"Unsupported operation type: {operation_type}"
        )
