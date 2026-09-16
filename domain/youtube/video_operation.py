from enum import Enum
from pathlib import Path
from typing import TypeAlias

from .video import Video
from .video_metadata import VideoMetadata


class OperationType(Enum):
    UPDATE_METADATA = "update_metadata"
    SET_THUMBNAIL = "set_thumbnail"
    ADD_TO_PLAYLIST = "add_to_playlist"


class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


OperationData: TypeAlias = VideoMetadata | Path | str


class Operation:
    def __init__(
        self,
        video: Video,
        operation_type: OperationType,
        data: OperationData,
    ) -> None:
        self._validate_data(operation_type, data)

        self._video = video
        self._operation_type = operation_type
        self._status = OperationStatus.PENDING
        self._data = data

    @property
    def video(self) -> Video:
        return self._video

    @property
    def operation_type(self) -> OperationType:
        return self._operation_type

    @property
    def status(self) -> OperationStatus:
        return self._status

    @property
    def data(self) -> OperationData:
        return self._data

    def start(self) -> None:
        if self._status is not OperationStatus.PENDING:
            raise ValueError(
                "Only pending operations can be started."
            )

        self._status = OperationStatus.RUNNING

    def complete(self) -> None:
        if self._status is not OperationStatus.RUNNING:
            raise ValueError(
                "Only running operations can be completed."
            )

        self._status = OperationStatus.COMPLETED

    def fail(self) -> None:
        if self._status is not OperationStatus.RUNNING:
            raise ValueError(
                "Only running operations can be failed."
            )

        self._status = OperationStatus.FAILED

    @staticmethod
    def _validate_data(
        operation_type: OperationType,
        data: OperationData,
    ) -> None:
        expected_types = {
            OperationType.UPDATE_METADATA: VideoMetadata,
            OperationType.SET_THUMBNAIL: Path,
            OperationType.ADD_TO_PLAYLIST: str,
        }

        expected_type = expected_types[operation_type]

        if not isinstance(data, expected_type):
            raise TypeError(
                f"{operation_type.value} requires "
                f"{expected_type.__name__} data."
            )