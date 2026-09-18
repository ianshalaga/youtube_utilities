from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call
from zoneinfo import ZoneInfo

import pytest

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from services.youtube.api.methods import YouTubeQuotaExceededError
from services.youtube.updater import JobRepository, Updater


@pytest.fixture
def video_metadata() -> VideoMetadata:
    return VideoMetadata(
        title="Test title",
        description="Test description",
        tags=["tag1", "tag2"],
        playlists=["playlist-1", "playlist-2"],
        game="Test game",
        made_for_kids=True,
        contains_synthetic_media=True,
        publish_at=datetime(
            2026,
            10,
            15,
            18,
            30,
            tzinfo=ZoneInfo("Europe/Paris"),
        ),
        thumbnail=Path("thumbnail.jpg"),
    )


@pytest.fixture
def video(video_metadata: VideoMetadata) -> Video:
    return Video(
        video_id="video-id",
        position=1,
        video_type=VideoType.SONG,
        metadata=video_metadata,
    )


@pytest.fixture
def update_metadata_operation(
    video: Video,
    video_metadata: VideoMetadata,
) -> Operation:
    return Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=video_metadata,
    )


@pytest.fixture
def thumbnail_operation(video: Video) -> Operation:
    return Operation(
        video=video,
        operation_type=OperationType.SET_THUMBNAIL,
        data=Path("thumbnail.jpg"),
    )


@pytest.fixture
def playlist_operation(video: Video) -> Operation:
    return Operation(
        video=video,
        operation_type=OperationType.ADD_TO_PLAYLIST,
        data="playlist-123",
    )


@pytest.fixture
def youtube_methods() -> MagicMock:
    return MagicMock()


@pytest.fixture
def job_repository() -> MagicMock:
    return MagicMock(spec=JobRepository)


@pytest.fixture
def updater(
    youtube_methods: MagicMock,
    job_repository: MagicMock,
) -> Updater:
    return Updater(
        youtube_methods=youtube_methods,
        job_repository=job_repository,
    )


def test_job_repository_exposes_save() -> None:
    repository = MagicMock(spec=JobRepository)

    repository.save(Job([])) if False else None

    assert hasattr(repository, "save")


@pytest.mark.parametrize("max_attempts", [0, -1, -10])
def test_init_rejects_invalid_max_attempts(
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    max_attempts: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="max_attempts must be at least 1.",
    ):
        Updater(
            youtube_methods=youtube_methods,
            job_repository=job_repository,
            max_attempts=max_attempts,
        )


def test_init_accepts_max_attempts_of_one(
    youtube_methods: MagicMock,
    job_repository: MagicMock,
) -> None:
    updater = Updater(
        youtube_methods=youtube_methods,
        job_repository=job_repository,
        max_attempts=1,
    )

    assert updater is not None


def test_update_executes_update_metadata_and_completes_job(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    job = Job([update_metadata_operation])

    updater.update(job)

    assert job.status is JobStatus.COMPLETED
    assert update_metadata_operation.status is OperationStatus.COMPLETED
    youtube_methods.videos_update.assert_called_once()
    job_repository.save.assert_called_once_with(job)


def test_update_starts_pending_job(
    updater: Updater,
    update_metadata_operation: Operation,
) -> None:
    job = Job([update_metadata_operation])

    assert job.status is JobStatus.PENDING

    updater.update(job)

    assert job.status is JobStatus.COMPLETED


def test_update_accepts_running_job(
    updater: Updater,
    update_metadata_operation: Operation,
) -> None:
    job = Job([update_metadata_operation])
    job.start()

    updater.update(job)

    assert job.status is JobStatus.COMPLETED
    assert update_metadata_operation.status is OperationStatus.COMPLETED


@pytest.mark.parametrize(
    "status",
    [JobStatus.COMPLETED, JobStatus.FAILED],
)
def test_update_rejects_completed_or_failed_job(
    updater: Updater,
    update_metadata_operation: Operation,
    status: JobStatus,
) -> None:
    job = Job([update_metadata_operation])

    if status is JobStatus.COMPLETED:
        update_metadata_operation.start()
        update_metadata_operation.complete()
        job.start()
        job.complete()
    else:
        job.start()
        job.fail()

    with pytest.raises(
        ValueError,
        match="Only pending or running jobs can be updated.",
    ):
        updater.update(job)


def test_update_metadata_sends_complete_supported_metadata(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
    video_metadata: VideoMetadata,
) -> None:
    job = Job([update_metadata_operation])

    updater.update(job)

    youtube_methods.videos_update.assert_called_once_with(
        video_resource={
            "id": "video-id",
            "snippet": {
                "title": "Test title",
                "description": "Test description",
                "tags": ["tag1", "tag2"],
                "categoryId": "20",
            },
            "status": {
                "privacyStatus": "private",
                "publishAt": video_metadata.publish_at.isoformat(),
                "selfDeclaredMadeForKids": True,
                "containsSyntheticMedia": True,
            },
        }
    )


def test_update_metadata_does_not_send_game(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    job = Job([update_metadata_operation])

    updater.update(job)

    resource = youtube_methods.videos_update.call_args.kwargs["video_resource"]

    assert "game" not in resource
    assert "game" not in resource["snippet"]
    assert "game" not in resource["status"]


def test_update_metadata_preserves_none_tags_as_empty_list(
    updater: Updater,
    youtube_methods: MagicMock,
    video: Video,
) -> None:
    metadata = VideoMetadata(
        title="Title",
        description="Description",
        tags=None,
        playlists=[],
        game="Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(
            2026,
            10,
            15,
            18,
            30,
            tzinfo=ZoneInfo("Europe/Paris"),
        ),
        thumbnail=None,
    )
    operation = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=metadata,
    )
    job = Job([operation])

    updater.update(job)

    resource = youtube_methods.videos_update.call_args.kwargs["video_resource"]

    assert resource["snippet"]["tags"] == []


def test_set_thumbnail_dispatches_thumbnail_path(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    thumbnail_operation: Operation,
) -> None:
    job = Job([thumbnail_operation])

    updater.update(job)

    youtube_methods.thumbnails_set.assert_called_once_with(
        video_id="video-id",
        thumbnail_path=Path("thumbnail.jpg"),
    )
    youtube_methods.videos_update.assert_not_called()
    youtube_methods.playlist_items_insert.assert_not_called()
    assert thumbnail_operation.status is OperationStatus.COMPLETED
    assert job.status is JobStatus.COMPLETED
    job_repository.save.assert_called_once_with(job)


def test_add_to_playlist_dispatches_playlist_id(
    updater: Updater,
    youtube_methods: MagicMock,
    playlist_operation: Operation,
) -> None:
    job = Job([playlist_operation])

    updater.update(job)

    youtube_methods.playlist_items_insert.assert_called_once_with(
        playlist_item_resource={
            "snippet": {
                "playlistId": "playlist-123",
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": "video-id",
                },
            }
        }
    )
    youtube_methods.videos_update.assert_not_called()
    youtube_methods.thumbnails_set.assert_not_called()


def test_operations_execute_in_job_order(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
    thumbnail_operation: Operation,
    playlist_operation: Operation,
) -> None:
    job = Job(
        [
            update_metadata_operation,
            thumbnail_operation,
            playlist_operation,
        ]
    )

    updater.update(job)

    assert youtube_methods.method_calls == [
        call.videos_update(
            video_resource={
                "id": "video-id",
                "snippet": {
                    "title": "Test title",
                    "description": "Test description",
                    "tags": ["tag1", "tag2"],
                    "categoryId": "20",
                },
                "status": {
                    "privacyStatus": "private",
                    "publishAt": datetime(
                        2026,
                        10,
                        15,
                        18,
                        30,
                        tzinfo=ZoneInfo("Europe/Paris")
                    ).isoformat(),
                    "selfDeclaredMadeForKids": True,
                    "containsSyntheticMedia": True,
                },
            }
        ),
        call.thumbnails_set(
            video_id="video-id",
            thumbnail_path=Path("thumbnail.jpg"),
        ),
        call.playlist_items_insert(
            playlist_item_resource={
                "snippet": {
                    "playlistId": "playlist-123",
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": "video-id",
                    },
                }
            }
        ),
    ]


def test_completed_operations_are_skipped(
    updater: Updater,
    youtube_methods: MagicMock,
    completed_operation: Operation,
) -> None:
    job = Job([completed_operation])

    updater.update(job)

    assert completed_operation.status is OperationStatus.COMPLETED
    assert job.status is JobStatus.COMPLETED
    youtube_methods.videos_update.assert_not_called()
    youtube_methods.thumbnails_set.assert_not_called()
    youtube_methods.playlist_items_insert.assert_not_called()


@pytest.fixture
def completed_operation(
    video: Video,
    video_metadata: VideoMetadata,
) -> Operation:
    operation = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=video_metadata,
    )
    operation.start()
    operation.complete()
    return operation


def test_completed_operation_is_skipped_and_pending_operation_executes(
    updater: Updater,
    youtube_methods: MagicMock,
    completed_operation: Operation,
    thumbnail_operation: Operation,
) -> None:
    job = Job([completed_operation, thumbnail_operation])

    updater.update(job)

    assert completed_operation.status is OperationStatus.COMPLETED
    assert thumbnail_operation.status is OperationStatus.COMPLETED
    assert job.status is JobStatus.COMPLETED
    youtube_methods.videos_update.assert_not_called()
    youtube_methods.thumbnails_set.assert_called_once()


@pytest.mark.parametrize(
    "operation_status",
    [OperationStatus.RUNNING, OperationStatus.FAILED],
)
def test_update_rejects_non_pending_non_completed_operation(
    updater: Updater,
    update_metadata_operation: Operation,
    operation_status: OperationStatus,
) -> None:
    job = Job([update_metadata_operation])

    if operation_status is OperationStatus.RUNNING:
        update_metadata_operation.start()
    else:
        update_metadata_operation.start()
        update_metadata_operation.fail()

    with pytest.raises(
        ValueError,
        match="A job can only contain pending or completed operations during an update.",
    ):
        updater.update(job)

    assert job.status is JobStatus.RUNNING


def test_normal_error_is_retried_until_success(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = [
        RuntimeError("temporary error"),
        RuntimeError("temporary error"),
        None,
    ]
    job = Job([update_metadata_operation])

    updater.update(job)

    assert update_metadata_operation.status is OperationStatus.COMPLETED
    assert job.status is JobStatus.COMPLETED
    assert youtube_methods.videos_update.call_count == 3


def test_normal_error_retry_does_not_reset_operation_between_attempts(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    statuses: list[OperationStatus] = []

    def fail_then_succeed(**_: object) -> None:
        statuses.append(update_metadata_operation.status)
        if len(statuses) == 1:
            raise RuntimeError("temporary error")

    youtube_methods.videos_update.side_effect = fail_then_succeed

    job = Job([update_metadata_operation])

    updater.update(job)

    assert statuses == [
        OperationStatus.RUNNING,
        OperationStatus.RUNNING,
    ]
    assert update_metadata_operation.status is OperationStatus.COMPLETED


def test_final_normal_error_marks_operation_and_job_failed(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
    capsys: pytest.CaptureFixture[str],
) -> None:
    youtube_methods.videos_update.side_effect = RuntimeError("permanent error")
    job = Job([update_metadata_operation])

    updater.update(job)

    assert youtube_methods.videos_update.call_count == 3
    assert update_metadata_operation.status is OperationStatus.FAILED
    assert job.status is JobStatus.FAILED
    job_repository.save.assert_called_once_with(job)

    output = capsys.readouterr().out
    assert "Operation failed" in output
    assert "permanent error" in output
    assert "Job failed on operation" in output


def test_final_normal_error_stops_before_subsequent_operations(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
    thumbnail_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = RuntimeError("permanent error")
    job = Job([update_metadata_operation, thumbnail_operation])

    updater.update(job)

    assert update_metadata_operation.status is OperationStatus.FAILED
    assert thumbnail_operation.status is OperationStatus.PENDING
    assert job.status is JobStatus.FAILED
    youtube_methods.thumbnails_set.assert_not_called()


def test_max_attempts_is_respected(
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = RuntimeError("error")
    updater = Updater(
        youtube_methods=youtube_methods,
        job_repository=job_repository,
        max_attempts=1,
    )
    job = Job([update_metadata_operation])

    updater.update(job)

    assert youtube_methods.videos_update.call_count == 1
    assert update_metadata_operation.status is OperationStatus.FAILED
    assert job.status is JobStatus.FAILED


def test_quota_exhaustion_resets_current_operation_and_job(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = YouTubeQuotaExceededError(
        "quota exceeded"
    )
    job = Job([update_metadata_operation])

    updater.update(job)

    assert update_metadata_operation.status is OperationStatus.PENDING
    assert job.status is JobStatus.PENDING
    job_repository.save.assert_called_once_with(job)
    assert youtube_methods.videos_update.call_count == 1


def test_quota_exhaustion_preserves_completed_operations_and_pending_operations(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    completed_operation: Operation,
    update_metadata_operation: Operation,
    thumbnail_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = YouTubeQuotaExceededError(
        "quota exceeded"
    )
    job = Job(
        [
            completed_operation,
            update_metadata_operation,
            thumbnail_operation,
        ]
    )

    updater.update(job)

    assert completed_operation.status is OperationStatus.COMPLETED
    assert update_metadata_operation.status is OperationStatus.PENDING
    assert thumbnail_operation.status is OperationStatus.PENDING
    assert job.status is JobStatus.PENDING
    job_repository.save.assert_called_once_with(job)
    youtube_methods.thumbnails_set.assert_not_called()


def test_quota_exhaustion_does_not_consume_normal_retries(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = YouTubeQuotaExceededError(
        "quota exceeded"
    )
    job = Job([update_metadata_operation])

    updater.update(job)

    assert youtube_methods.videos_update.call_count == 1
    assert update_metadata_operation.status is OperationStatus.PENDING


def test_quota_is_not_reported_as_normal_operation_failure(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
    capsys: pytest.CaptureFixture[str],
) -> None:
    youtube_methods.videos_update.side_effect = YouTubeQuotaExceededError(
        "quota exceeded"
    )
    job = Job([update_metadata_operation])

    updater.update(job)

    output = capsys.readouterr().out

    assert "Operation failed" not in output
    assert "Job failed" not in output


def test_resume_running_job_skips_completed_and_continues_pending(
    updater: Updater,
    youtube_methods: MagicMock,
    completed_operation: Operation,
    thumbnail_operation: Operation,
) -> None:
    job = Job([completed_operation, thumbnail_operation])
    job.start()

    updater.update(job)

    assert completed_operation.status is OperationStatus.COMPLETED
    assert thumbnail_operation.status is OperationStatus.COMPLETED
    assert job.status is JobStatus.COMPLETED
    youtube_methods.videos_update.assert_not_called()
    youtube_methods.thumbnails_set.assert_called_once()


def test_successful_update_persists_only_after_job_completion(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
    thumbnail_operation: Operation,
) -> None:
    job = Job([update_metadata_operation, thumbnail_operation])

    updater.update(job)

    assert job_repository.save.call_count == 1
    assert job_repository.save.call_args == call(job)
    assert job.status is JobStatus.COMPLETED


def test_operation_failure_persists_failed_job(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = RuntimeError("error")
    job = Job([update_metadata_operation])

    updater.update(job)

    assert job_repository.save.call_count == 1
    assert job_repository.save.call_args == call(job)
    assert job.status is JobStatus.FAILED


def test_quota_interruption_persists_pending_job(
    updater: Updater,
    youtube_methods: MagicMock,
    job_repository: MagicMock,
    update_metadata_operation: Operation,
) -> None:
    youtube_methods.videos_update.side_effect = YouTubeQuotaExceededError(
        "quota exceeded"
    )
    job = Job([update_metadata_operation])

    updater.update(job)

    assert job_repository.save.call_count == 1
    assert job_repository.save.call_args == call(job)
    assert job.status is JobStatus.PENDING


def test_multiple_operations_complete_successfully(
    updater: Updater,
    youtube_methods: MagicMock,
    update_metadata_operation: Operation,
    thumbnail_operation: Operation,
    playlist_operation: Operation,
) -> None:
    job = Job(
        [
            update_metadata_operation,
            thumbnail_operation,
            playlist_operation,
        ]
    )

    updater.update(job)

    assert job.status is JobStatus.COMPLETED
    assert all(
        operation.status is OperationStatus.COMPLETED
        for operation in job.operations
    )
    assert youtube_methods.videos_update.call_count == 1
    assert youtube_methods.thumbnails_set.call_count == 1
    assert youtube_methods.playlist_items_insert.call_count == 1