from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import Mock

from rich.console import Console

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import (
    Operation,
    OperationType,
)
from domain.youtube.publication_settings import PublicationSettings
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from interfaces.cli.menus import youtube_video_manager_prompts as prompts_module
from interfaces.cli.menus.youtube_video_manager_prompts import (
    YouTubeVideoManagerPrompts,
)


def create_job() -> Job:
    metadata = VideoMetadata(
        title="Video",
        description="Description",
        tags=None,
        playlists=[],
        game="Game",
        made_for_kids=False,
        contains_synthetic_media=False,
        publish_at=datetime(2026, 1, 1, 18, 0),
        thumbnail=None,
    )
    video = Video(
        video_id="video-1",
        position=1,
        video_type=VideoType.SONG,
        metadata=metadata,
    )
    operation = Operation(
        video=video,
        operation_type=OperationType.UPDATE_METADATA,
        data=metadata,
    )
    publication = PublicationSettings(
        first_publish_at=datetime(2026, 1, 1, 18, 0),
        timezone="Europe/Paris",
        interval_days=2,
    )
    return Job([operation], publication=publication, name="Test Album")


def test_created_job_prompt_can_keep_publication(monkeypatch):
    prompts = YouTubeVideoManagerPrompts(
        console=Console(file=StringIO(), color_system=None),
    )
    prompt = Mock()
    prompt.ask.return_value = "keep"
    select = Mock(return_value=prompt)
    monkeypatch.setattr(prompts_module.questionary, "select", select)
    job = create_job()

    result = prompts.ask_created_job_publication(job)

    assert result is job.publication
    assert select.call_args.kwargs["use_arrow_keys"] is True


def test_created_job_prompt_updates_date_interval_and_timezone(monkeypatch):
    prompts = YouTubeVideoManagerPrompts(
        console=Console(file=StringIO(), color_system=None),
    )
    select_prompt = Mock()
    select_prompt.ask.return_value = "update"
    select = Mock(return_value=select_prompt)
    text = Mock()
    text_values = iter(["2026-11-14 09:30", "4", "America/Toronto"])

    def text_prompt(*args, **kwargs):
        prompt = Mock()
        prompt.ask.return_value = next(text_values)
        return prompt

    text.side_effect = text_prompt
    confirm_prompt = Mock()
    confirm_prompt.ask.return_value = True
    confirm = Mock(return_value=confirm_prompt)
    monkeypatch.setattr(prompts_module.questionary, "select", select)
    monkeypatch.setattr(prompts_module.questionary, "text", text)
    monkeypatch.setattr(prompts_module.questionary, "confirm", confirm)

    result = prompts.ask_created_job_publication(create_job())

    assert result is not None
    assert result.first_publish_at == datetime(
        2026,
        11,
        14,
        9,
        30,
        tzinfo=result.timezone,
    )
    assert result.interval_days == 4
    assert result.timezone.key == "America/Toronto"
    assert text.call_count == 3


def test_failed_thumbnail_job_offers_thumbnail_path_update(monkeypatch):
    job = create_job()
    thumbnail_operation = Operation(
        video=job.operations[0].video,
        operation_type=OperationType.SET_THUMBNAIL,
        data=Path("old-thumbnail.jpg"),
    )
    thumbnail_operation.start()
    thumbnail_operation.fail()
    job = Job([thumbnail_operation], status=JobStatus.FAILED)
    prompt = Mock()
    prompt.ask.return_value = "update_thumbnail"
    select = Mock(return_value=prompt)
    monkeypatch.setattr(prompts_module.questionary, "select", select)
    prompts = YouTubeVideoManagerPrompts(
        console=Console(file=StringIO(), color_system=None),
    )

    result = prompts.ask_failed_job_action(job)

    assert result == "update_thumbnail"
    choices = select.call_args.kwargs["choices"]
    assert [choice.value for choice in choices] == [
        "retry",
        "update_thumbnail",
        "delete",
    ]


def test_thumbnail_path_prompt_returns_existing_file(monkeypatch, tmp_path):
    thumbnail = tmp_path / "thumbnail.jpg"
    thumbnail.write_bytes(b"thumbnail")
    prompt = Mock()
    prompt.ask.return_value = f'"{thumbnail}"'
    path_prompt = Mock(return_value=prompt)
    monkeypatch.setattr(
        prompts_module.questionary,
        "path",
        path_prompt,
    )
    prompts = YouTubeVideoManagerPrompts(
        console=Console(file=StringIO(), color_system=None),
    )

    result = prompts.ask_thumbnail_path()

    assert result == thumbnail
