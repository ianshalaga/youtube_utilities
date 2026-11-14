from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from core.config_manager import ConfigManager
from applications.youtube_video_manager.processor import (
    YouTubeVideoManagerProcessor,
)
from services.youtube.album_builder import AlbumBuilder
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.api.client import YouTubeClient
from services.youtube.api.methods import YouTubeMethods
from services.youtube.console import YouTubeConsole
from services.youtube.operations_builder import OperationsBuilder
from services.youtube.planner import Planner
from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.repository import YouTubeJobRepository
from services.youtube.updater import Updater
from services.youtube.youtube_discovery import YouTubeDiscovery
from services.youtube.video_id_overrides_reader import VideoIdOverridesReader


class YouTubeVideoManagerProcessorFactory:
    """Builds the dependencies required by YouTube Video Manager."""

    @staticmethod
    def create_processor(
        config: ConfigManager,
        session: Session,
        failure_action: Callable[[], str],
        console: YouTubeConsole | None = None,
    ) -> YouTubeVideoManagerProcessor:
        youtube_client = YouTubeClient(
            client_secrets_path=Path(
                config.youtube_video_manager_client_secrets_path,
            ),
            token_path=Path(
                config.youtube_video_manager_token_path,
            ),
        )
        youtube_methods = YouTubeMethods(youtube_client)
        youtube_discovery = YouTubeDiscovery(methods=youtube_methods)

        job_repository = YouTubeJobRepository(
            session=session,
            mapper=JobMapper(),
        )
        planner = Planner(OperationsBuilder())
        console = console or YouTubeConsole()
        updater = Updater(
            youtube_methods=youtube_methods,
            job_repository=job_repository,
            console=console,
            max_attempts=config.youtube_video_manager_max_attempts,
        )

        return YouTubeVideoManagerProcessor(
            manifest_reader=YamlReader(),
            youtube_discovery=youtube_discovery,
            album_builder=AlbumBuilder(),
            planner=planner,
            updater=updater,
            job_repository=job_repository,
            failure_action=failure_action,
            console=console,
            video_id_overrides_reader=VideoIdOverridesReader(),
            video_id_overrides_path=(
                config.youtube_video_manager_video_id_overrides_path
            ),
        )
