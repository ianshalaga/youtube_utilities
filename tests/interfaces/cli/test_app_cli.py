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


def test_run_web_delegates_to_launch_web_server(monkeypatch) -> None:
    launch_mock = Mock()
    monkeypatch.setattr("interfaces.web.launcher.launch_web_server", launch_mock)

    app_cli.run_web(host="127.0.0.1", port=8000, open_browser=True)

    launch_mock.assert_called_once_with(
        host="127.0.0.1",
        port=8000,
        open_browser=True,
    )


def test_build_parser_accepts_web_command_with_custom_flags() -> None:
    parser = app_cli.build_parser()
    args = parser.parse_args(["web", "--host", "0.0.0.0", "--port", "9000", "--no-browser"])

    assert args.command == "web"
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.no_browser is True


def test_main_executes_web_command(monkeypatch) -> None:
    run_web_mock = Mock()
    monkeypatch.setattr(app_cli, "run_web", run_web_mock)
    monkeypatch.setattr(app_cli, "ConfigManager", Mock())
    monkeypatch.setattr(
        "sys.argv",
        ["app.py", "web", "--port", "8000"],
    )

    app_cli.main()

    run_web_mock.assert_called_once_with(
        host="127.0.0.1",
        port=8000,
        open_browser=True,
    )


def test_run_export_context_delegates_to_context_exporter(monkeypatch) -> None:
    exporter_mock = Mock()
    exporter_cls = Mock(return_value=exporter_mock)
    monkeypatch.setattr("tools.export_context.ContextExporter", exporter_cls)

    app_cli.run_export_context("video_music", include_tests=False, output_format="txt")

    exporter_cls.assert_called_once_with()
    exporter_mock.export.assert_called_once_with(
        target="video_music",
        include_tests=False,
        output_format="txt",
    )


def test_build_parser_accepts_export_context_without_target() -> None:
    parser = app_cli.build_parser()
    args = parser.parse_args(["export_context"])

    assert args.command == "export_context"
    assert args.target == "all"
    assert args.no_tests is False
    assert args.format == "md"


def test_build_parser_accepts_export_context_with_target_and_options() -> None:
    parser = app_cli.build_parser()
    args = parser.parse_args(["export_context", "video_music", "--no-tests", "--format", "txt"])

    assert args.command == "export_context"
    assert args.target == "video_music"
    assert args.no_tests is True
    assert args.format == "txt"


def test_main_executes_export_context_command(monkeypatch) -> None:
    run_export_mock = Mock()
    monkeypatch.setattr(app_cli, "run_export_context", run_export_mock)
    monkeypatch.setattr(app_cli, "ConfigManager", Mock())
    monkeypatch.setattr(
        "sys.argv",
        ["app.py", "export_context", "video_joiner"],
    )

    app_cli.main()

    run_export_mock.assert_called_once_with(
        target="video_joiner",
        include_tests=True,
        output_format="md",
    )
