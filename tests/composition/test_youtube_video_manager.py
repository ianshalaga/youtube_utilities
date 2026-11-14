from pathlib import Path
from unittest.mock import MagicMock, patch

from composition.youtube_video_manager import (
    YouTubeVideoManagerProcessorFactory,
)


def test_create_processor_composes_youtube_video_manager_dependencies():
    config = MagicMock()
    config.youtube_video_manager_client_secrets_path = Path("client.json")
    config.youtube_video_manager_token_path = Path("token.json")
    config.youtube_video_manager_max_attempts = 4
    config.youtube_video_manager_video_id_overrides_path = Path("ids.yaml")
    session = MagicMock()
    failure_action = MagicMock()
    console = MagicMock()

    with (
        patch("composition.youtube_video_manager.YouTubeClient") as client,
        patch("composition.youtube_video_manager.YouTubeMethods") as methods,
        patch("composition.youtube_video_manager.YouTubeDiscovery") as discovery,
        patch("composition.youtube_video_manager.JobMapper") as mapper,
        patch("composition.youtube_video_manager.YouTubeJobRepository") as repository,
        patch("composition.youtube_video_manager.OperationsBuilder") as operations_builder,
        patch("composition.youtube_video_manager.Planner") as planner,
        patch("composition.youtube_video_manager.Updater") as updater,
        patch("composition.youtube_video_manager.YamlReader") as manifest_reader,
        patch("composition.youtube_video_manager.AlbumBuilder") as album_builder,
        patch("composition.youtube_video_manager.VideoIdOverridesReader") as overrides_reader,
        patch("composition.youtube_video_manager.YouTubeVideoManagerProcessor") as processor,
    ):
        result = YouTubeVideoManagerProcessorFactory.create_processor(
            config=config,
            session=session,
            failure_action=failure_action,
            console=console,
        )

    assert result is processor.return_value
    client.assert_called_once_with(
        client_secrets_path=Path("client.json"),
        token_path=Path("token.json"),
    )
    methods.assert_called_once_with(client.return_value)
    discovery.assert_called_once_with(methods=methods.return_value)
    repository.assert_called_once_with(
        session=session,
        mapper=mapper.return_value,
    )
    planner.assert_called_once_with(operations_builder.return_value)
    updater.assert_called_once_with(
        youtube_methods=methods.return_value,
        job_repository=repository.return_value,
        console=console,
        max_attempts=4,
    )
    processor.assert_called_once_with(
        manifest_reader=manifest_reader.return_value,
        youtube_discovery=discovery.return_value,
        album_builder=album_builder.return_value,
        planner=planner.return_value,
        updater=updater.return_value,
        job_repository=repository.return_value,
        failure_action=failure_action,
        console=console,
        video_id_overrides_reader=overrides_reader.return_value,
        video_id_overrides_path=Path("ids.yaml"),
    )
