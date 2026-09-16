# services\youtube\operations_builder.py

from domain.youtube.album import Album
from domain.youtube.operation import Operation, OperationType
from domain.youtube.video import Video


class OperationsBuilder:
    """
    Builds the operations required to apply an Album configuration.

    The Album represents the desired state. This builder decomposes that
    desired state into concrete operations without consulting YouTube or
    executing any operation.
    """

    def build(self, album: Album) -> list[Operation]:
        """
        Build all operations required for the videos in an Album.

        For each video:
            - one UPDATE_METADATA operation is created;
            - one SET_THUMBNAIL operation is created when a thumbnail exists;
            - one ADD_TO_PLAYLIST operation is created for each playlist.

        Returns:
            The operations in deterministic album/video order.

        Raises:
            ValueError: If the album contains no videos.
        """
        if not album.videos:
            raise ValueError("Cannot build operations for an empty album.")

        operations: list[Operation] = []

        for video in album.videos:
            operations.extend(self._build_video_operations(video))

        return operations

    def _build_video_operations(self, video: Video) -> list[Operation]:
        operations = [
            Operation(
                video=video,
                operation_type=OperationType.UPDATE_METADATA,
                data=video.metadata,
            )
        ]

        if video.metadata.thumbnail is not None:
            operations.append(
                Operation(
                    video=video,
                    operation_type=OperationType.SET_THUMBNAIL,
                    data=video.metadata.thumbnail,
                )
            )

        operations.extend(
            Operation(
                video=video,
                operation_type=OperationType.ADD_TO_PLAYLIST,
                data=playlist,
            )
            for playlist in video.metadata.playlists
        )

        return operations