from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

from rich.console import Console

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import Operation, OperationStatus, OperationType
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from interfaces.cli.menus import youtube_video_manager_menu as menu_module
from interfaces.cli.menus.youtube_video_manager_menu import (
    MenuAction,
    MenuSelection,
    YouTubeVideoManagerMenu,
)


def create_job() -> Job:
    metadata = VideoMetadata(
        title="Test video",
        description="Description",
        tags=None,
        playlists=[],
        game="Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 11, 14, 18, 0, tzinfo=timezone.utc),
        thumbnail=Path("thumbnail.jpg"),
    )
    video = Video(
        video_id="video-1",
        position=1,
        video_type=VideoType.SONG,
        metadata=metadata,
    )
    metadata_operation = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=metadata,
    )
    completed_thumbnail = Operation(
        video=video,
        operation_type=OperationType.SET_THUMBNAIL,
        data=metadata.thumbnail,
    )
    completed_thumbnail.start()
    completed_thumbnail.complete()
    failed_playlist = Operation(
        video=video,
        operation_type=OperationType.ADD_TO_PLAYLIST,
        data="playlist-1",
    )
    failed_playlist.start()
    failed_playlist.fail()
    completed_playlist = Operation(
        video=video,
        operation_type=OperationType.ADD_TO_PLAYLIST,
        data="playlist-2",
    )
    completed_playlist.start()
    completed_playlist.complete()
    return Job(
        [
            metadata_operation,
            completed_thumbnail,
            failed_playlist,
            completed_playlist,
        ],
        job_id=24,
        status=JobStatus.FAILED,
        name="Example Album",
    )


def create_running_job() -> Job:
    metadata = VideoMetadata(
        title="Running video",
        description="Description",
        tags=None,
        playlists=[],
        game="Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 11, 14, 18, 0, tzinfo=timezone.utc),
        thumbnail=Path("thumbnail.jpg"),
    )
    video = Video(
        video_id="video-2",
        position=2,
        video_type=VideoType.SONG,
        metadata=metadata,
    )
    operation = Operation(
        video=video,
        operation_type=OperationType.SET_THUMBNAIL,
        data=metadata.thumbnail,
    )
    operation.start()
    return Job(
        [operation],
        job_id=25,
        status=JobStatus.RUNNING,
        name="Running Album",
    )


def test_select_lists_jobs_by_status_and_returns_selected_job(monkeypatch):
    output = StringIO()
    console = Console(file=output, width=160, color_system=None)
    menu = YouTubeVideoManagerMenu(console=console)
    job = create_job()
    selection = MenuSelection(MenuAction.SELECT_JOB, 24)
    prompt = Mock()
    prompt.ask.return_value = selection
    select = Mock(return_value=prompt)
    monkeypatch.setattr(menu_module.questionary, "select", select)

    running_job = create_running_job()
    result = menu.select([job, running_job])

    assert result == selection
    rendered = output.getvalue()
    assert "[FAILED] Jobs" in rendered
    assert "[RUNNING] Jobs" in rendered
    assert "Example Album" in rendered
    assert "Running Album" in rendered
    assert "Metadatos" in rendered
    assert "Miniaturas" in rendered
    assert "Playlists" in rendered
    assert "P=pendientes" in rendered
    assert "P:1" in rendered
    assert "R:1" in rendered
    assert "F:1" in rendered
    assert "C:1" in rendered
    select.assert_called_once()
    assert select.call_args.kwargs["use_arrow_keys"] is True
    choices = select.call_args.kwargs["choices"]
    assert choices[0].value == MenuSelection(MenuAction.CREATE_JOB)
    assert choices[1].value == selection
    assert "FAILED · Example Album · #24" == choices[1].title
    assert choices[2].value == MenuSelection(MenuAction.SELECT_JOB, 25)


def test_select_without_jobs_offers_only_create(monkeypatch):
    menu = YouTubeVideoManagerMenu(
        console=Console(file=StringIO(), color_system=None),
    )
    prompt = Mock()
    prompt.ask.return_value = MenuSelection(MenuAction.CREATE_JOB)
    select = Mock(return_value=prompt)
    monkeypatch.setattr(menu_module.questionary, "select", select)

    result = menu.select([])

    assert result == MenuSelection(MenuAction.CREATE_JOB)
    choices = select.call_args.kwargs["choices"]
    assert len(choices) == 1
    assert choices[0].value.action is MenuAction.CREATE_JOB
