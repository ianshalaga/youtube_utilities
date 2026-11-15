from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest

from domain.youtube.job import JobStatus
from domain.youtube.publication_settings import PublicationSettings
from interfaces.cli import app_cli
from interfaces.cli.menus.youtube_video_manager_menu import (
    MenuAction,
    MenuSelection,
)


@pytest.mark.parametrize(
    ("status", "prompt_method", "prompt_result", "processor_method"),
    [
        (
            JobStatus.CREATED,
            "ask_created_job_publication",
            "publication",
            "start_created_job",
        ),
        (JobStatus.PENDING, None, None, "continue_pending_job"),
        (
            JobStatus.FAILED,
            "ask_failed_job_action",
            "retry",
            "retry_failed_job",
        ),
        (
            JobStatus.RUNNING,
            "ask_running_job_action",
            "resume",
            "recover_running_job",
        ),
    ],
)
def test_cli_dispatches_selected_job_by_its_state(
    monkeypatch,
    status,
    prompt_method,
    prompt_result,
    processor_method,
):
    config = Mock()
    config.youtube_video_manager_album_manifest_path = Path("manifest.yaml")
    session = Mock()
    processor = Mock()
    job = Mock()
    job.status = status
    job.id = 9
    publication = PublicationSettings(
        first_publish_at=datetime(2026, 11, 14, 18, 0),
        timezone="UTC",
        interval_days=3,
    )
    if prompt_result == "publication":
        prompt_result = publication
    processor.list_jobs.return_value = [job]
    processor.get_job.return_value = job

    menu = Mock()
    menu.select.side_effect = [
        MenuSelection(MenuAction.SELECT_JOB, 9),
        None,
    ]
    prompts = Mock()
    if prompt_method is not None:
        getattr(prompts, prompt_method).return_value = prompt_result

    session_factory = Mock(return_value=session)
    console_factory = Mock()
    processor_factory = Mock(return_value=processor)
    menu_factory = Mock(return_value=menu)
    prompts_factory = Mock(return_value=prompts)
    monkeypatch.setattr(app_cli, "YouTubeSessionLocal", session_factory)
    monkeypatch.setattr(app_cli, "YouTubeConsole", console_factory)
    monkeypatch.setattr(
        app_cli.YouTubeVideoManagerProcessorFactory,
        "create_processor",
        processor_factory,
    )
    monkeypatch.setattr(app_cli, "YouTubeVideoManagerMenu", menu_factory)
    monkeypatch.setattr(
        app_cli,
        "YouTubeVideoManagerPrompts",
        prompts_factory,
    )

    app_cli.run_youtube_video_manager(config)

    if status is JobStatus.CREATED:
        processor.start_created_job.assert_called_once_with(job, publication)
    else:
        getattr(processor, processor_method).assert_called_once_with(job)
    session.close.assert_called_once_with()


def test_cli_creates_job_and_returns_to_menu(monkeypatch):
    config = Mock()
    config.youtube_video_manager_album_manifest_path = Path("manifest.yaml")
    session = Mock()
    processor = Mock()
    processor.list_jobs.return_value = []
    menu = Mock()
    menu.select.side_effect = [
        MenuSelection(MenuAction.CREATE_JOB),
        None,
    ]
    monkeypatch.setattr(
        app_cli,
        "YouTubeSessionLocal",
        Mock(return_value=session),
    )
    monkeypatch.setattr(app_cli, "YouTubeConsole", Mock())
    monkeypatch.setattr(
        app_cli.YouTubeVideoManagerProcessorFactory,
        "create_processor",
        Mock(return_value=processor),
    )
    monkeypatch.setattr(
        app_cli,
        "YouTubeVideoManagerMenu",
        Mock(return_value=menu),
    )

    app_cli.run_youtube_video_manager(config)

    processor.create_and_save_job.assert_called_once_with(Path("manifest.yaml"))
    assert menu.select.call_count == 2
    session.close.assert_called_once_with()


def test_cli_exits_when_exit_option_is_selected(monkeypatch):
    config = Mock()
    config.youtube_video_manager_album_manifest_path = Path("manifest.yaml")
    session = Mock()
    processor = Mock()
    menu = Mock()
    menu.select.return_value = MenuSelection(MenuAction.EXIT)
    monkeypatch.setattr(
        app_cli,
        "YouTubeSessionLocal",
        Mock(return_value=session),
    )
    monkeypatch.setattr(app_cli, "YouTubeConsole", Mock())
    monkeypatch.setattr(
        app_cli.YouTubeVideoManagerProcessorFactory,
        "create_processor",
        Mock(return_value=processor),
    )
    monkeypatch.setattr(
        app_cli,
        "YouTubeVideoManagerMenu",
        Mock(return_value=menu),
    )

    app_cli.run_youtube_video_manager(config)

    menu.select.assert_called_once_with(processor.list_jobs.return_value)
    processor.create_and_save_job.assert_not_called()
    session.close.assert_called_once_with()
