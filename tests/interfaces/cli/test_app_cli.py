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
    create_processor.assert_called_once_with()
    processor.process.assert_called_once_with(input_data)
    presenter_factory.assert_called_once_with()
    presenter.display.assert_called_once_with(result)
