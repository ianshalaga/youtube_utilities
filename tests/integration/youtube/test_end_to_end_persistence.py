from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from domain.youtube.job import JobStatus
from domain.youtube.operation import OperationStatus, OperationType
from services.youtube.album_builder import AlbumBuilder
from services.youtube.album_manifest.yaml_reader import YamlReader
from services.youtube.api.client import YouTubeClient
from services.youtube.api.methods import YouTubeMethods
from services.youtube.operations_builder import OperationsBuilder
from services.youtube.planner import Planner
from services.youtube.storage.base import Base
from services.youtube.storage.mappers.job_mapper import JobMapper
from services.youtube.storage.repository import YouTubeJobRepository
from services.youtube.youtube_discovery import YouTubeDiscovery
from core.config_manager import ConfigManager


@pytest.mark.integration
@pytest.mark.real_youtube
def test_real_youtube_album_is_planned_persisted_and_reloaded() -> None:
    """
    Run the complete read/build/plan/persist/reload workflow against real YouTube.

    This test deliberately does NOT instantiate or call Updater. Therefore it
    performs real YouTube authentication and discovery, but never modifies
    YouTube videos.

    The database is an isolated in-memory SQLite database so the test cannot
    modify the application's normal yvm.db.
    """
    config = ConfigManager()

    manifest_path = Path(
        config.youtube_video_manager_album_manifest_path,
    )

    client = YouTubeClient(
        client_secrets_path=Path(
            config.youtube_video_manager_client_secrets_path,
        ),
        token_path=Path(
            config.youtube_video_manager_token_path,
        ),
    )
    youtube_methods = YouTubeMethods(client)
    discovery = YouTubeDiscovery(methods=youtube_methods)

    manifest_reader = YamlReader()
    album_builder = AlbumBuilder()
    planner = Planner(
        operations_builder=OperationsBuilder(),
    )

    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        future=True,
    )
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    session = SessionLocal()

    try:
        repository = YouTubeJobRepository(
            session=session,
            mapper=JobMapper(),
        )

        manifest = manifest_reader.read(manifest_path)
        youtube_videos = discovery.discover()

        album = album_builder.build(
            manifest=manifest,
            youtube_videos=youtube_videos,
        )

        validation = album.validate()
        assert validation.is_valid, validation.errors

        job = planner.plan(album)

        assert job.status is JobStatus.PENDING
        assert job.operations

        assert all(
            operation.status is OperationStatus.PENDING
            for operation in job.operations
        )

        repository.save(job)

        session.close()

        session = SessionLocal()
        repository = YouTubeJobRepository(
            session=session,
            mapper=JobMapper(),
        )

        loaded_job = repository.find_pending()

        assert loaded_job is not None
        assert loaded_job.status is JobStatus.PENDING
        assert len(loaded_job.operations) == len(job.operations)

        for original, loaded in zip(
            job.operations,
            loaded_job.operations,
        ):
            assert loaded.status is original.status
            assert loaded.operation_type is original.operation_type

            assert loaded.video.video_id == original.video.video_id
            assert loaded.video.position == original.video.position
            assert loaded.video.video_type is original.video.video_type

            if original.operation_type is OperationType.UPDATE_METADATA:
                original_metadata = original.data
                loaded_metadata = loaded.data

                assert loaded_metadata.title == original_metadata.title
                assert loaded_metadata.description == original_metadata.description
                assert loaded_metadata.tags == original_metadata.tags
                assert loaded_metadata.game == original_metadata.game
                assert (
                    loaded_metadata.made_for_kids
                    == original_metadata.made_for_kids
                )
                assert (
                    loaded_metadata.contains_synthetic_media
                    == original_metadata.contains_synthetic_media
                )
                assert loaded_metadata.publish_at == original_metadata.publish_at
                assert loaded_metadata.thumbnail == original_metadata.thumbnail

            elif original.operation_type is OperationType.SET_THUMBNAIL:
                assert loaded.data == original.data

            elif original.operation_type is OperationType.ADD_TO_PLAYLIST:
                assert loaded.data == original.data

    finally:
        session.close()
        engine.dispose()
