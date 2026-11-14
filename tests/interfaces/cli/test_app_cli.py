from pathlib import Path
from unittest.mock import Mock

from interfaces.cli import app_cli


def test_run_video_music_builds_input_processes_and_displays_result(
    monkeypatch,
) -> None:
    config = object()
    input_data = object()
    result = object()

    build_input = Mock(return_value=input_data)
    processor = Mock()
    processor.process.return_value = result
    create_processor = Mock(return_value=processor)
    presenter = Mock()
    presenter_factory = Mock(return_value=presenter)

    monkeypatch.setattr(app_cli, "build_video_music_input", build_input)
    monkeypatch.setattr(
        app_cli.VideoMusicProcessorFactory,
        "create_processor",
        create_processor,
    )
    monkeypatch.setattr(
        app_cli,
        "VideoMusicResultPresenter",
        presenter_factory,
    )

    app_cli.run_video_music(config)

    build_input.assert_called_once_with(config)
    create_processor.assert_called_once_with(config)
    processor.process.assert_called_once_with(input_data)
    presenter_factory.assert_called_once_with()
    presenter.display.assert_called_once_with(result)


def test_run_youtube_video_manager_delegates_composition_and_closes_session(
    monkeypatch,
) -> None:
    config = Mock()
    config.youtube_video_manager_album_manifest_path = Path(
        "manifests/album.yaml"
    )
    session = Mock()
    processor = Mock()
    processor.list_jobs.return_value = []
    create_processor = Mock(return_value=processor)
    menu = Mock()
    menu.select.return_value = None
    menu_factory = Mock(return_value=menu)
    monkeypatch.setattr(
        app_cli,
        "YouTubeSessionLocal",
        Mock(return_value=session),
    )
    monkeypatch.setattr(app_cli, "YouTubeConsole", Mock())
    monkeypatch.setattr(
        app_cli,
        "YouTubeVideoManagerMenu",
        menu_factory,
    )
    monkeypatch.setattr(
        app_cli.YouTubeVideoManagerProcessorFactory,
        "create_processor",
        create_processor,
    )

    app_cli.run_youtube_video_manager(config)

    create_processor.assert_called_once_with(
        config=config,
        session=session,
        console=app_cli.YouTubeConsole.return_value,
    )
    processor.process.assert_not_called()
    processor.list_jobs.assert_called_once_with()
    menu.select.assert_called_once_with([])
    session.close.assert_called_once_with()
