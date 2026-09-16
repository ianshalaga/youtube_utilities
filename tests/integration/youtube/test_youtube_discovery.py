from __future__ import annotations

import os
from pathlib import Path

import pytest

from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo
from services.youtube.api.client import YouTubeClient
from services.youtube.api.methods import YouTubeMethods
from services.youtube.youtube_discovery import YouTubeDiscovery


CLIENT_SECRETS_ENV = "YOUTUBE_CLIENT_SECRETS"
TOKEN_ENV = "YOUTUBE_TOKEN"


@pytest.fixture
def youtube_discovery() -> YouTubeDiscovery:
    client_secrets_path = os.getenv(CLIENT_SECRETS_ENV)
    token_path = os.getenv(TOKEN_ENV)

    if not client_secrets_path:
        pytest.skip(
            f"Environment variable {CLIENT_SECRETS_ENV} is not configured."
        )

    if not token_path:
        pytest.skip(
            f"Environment variable {TOKEN_ENV} is not configured."
        )

    client_secrets = Path(client_secrets_path)
    token = Path(token_path)

    if not client_secrets.is_file():
        pytest.fail(
            f"YouTube client secrets file does not exist: {client_secrets}"
        )

    client = YouTubeClient(
        client_secrets_path=client_secrets,
        token_path=token,
    )

    methods = YouTubeMethods(client)

    return YouTubeDiscovery(methods)


@pytest.mark.integration
def test_youtube_discovery_returns_real_videos(
    youtube_discovery: YouTubeDiscovery,
) -> None:
    videos = youtube_discovery.discover()

    assert isinstance(videos, tuple)
    assert videos
    assert all(isinstance(video, YouTubeVideo) for video in videos)

    for video in videos:
        assert video.video_id
        assert video.title
        assert video.privacy_status is PrivacyStatus.PRIVATE

        print(
            f"{video.video_id} | "
            f"{video.privacy_status.value} | "
            f"{video.title}"
        )

# $env:YOUTUBE_CLIENT_SECRETS="config\youtube\client_secret.json"
# $env:YOUTUBE_TOKEN="config\youtube\token.json"


