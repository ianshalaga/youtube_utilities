# tests\\services\\youtube\\test_youtube_discovery.py

from unittest.mock import MagicMock

import pytest

from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo
from services.youtube.api.methods import YouTubeMethods
from services.youtube.youtube_discovery import YouTubeDiscovery


UPLOADS_PLAYLIST_ID = "UU_TEST_UPLOADS"


def _create_playlist_item(
    video_id: str,
    title: str,
    description: str | None,
    privacy_status: str,
) -> dict:
    return {
        "contentDetails": {
            "videoId": video_id,
        },
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }


def _create_methods() -> MagicMock:
    methods = MagicMock(spec=YouTubeMethods)

    methods.channels_list.return_value = {
        "items": [
            {
                "contentDetails": {
                    "relatedPlaylists": {
                        "uploads": UPLOADS_PLAYLIST_ID,
                    },
                },
            },
        ],
    }

    return methods


def test_discover_returns_expected_videos():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-unrelated",
                "Unrelated Private Video",
                "Unrelated description",
                "private",
            ),
            _create_playlist_item(
                "video-03",
                "03 Battle Theme Orchestral Mix",
                "Battle description",
                "private",
            ),
            _create_playlist_item(
                "video-02",
                "02 Exploration Theme",
                "Exploration description",
                "private",
            ),
            _create_playlist_item(
                "video-unrelated-public",
                "Unrelated Public Video",
                None,
                "public",
            ),
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
                "Opening description",
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=(
            "03 Battle Theme",
            "02 Exploration Theme",
            "01 Opening Theme",
        )
    )

    assert result == (
        YouTubeVideo(
            video_id="video-03",
            title="03 Battle Theme Orchestral Mix",
            description="Battle description",
            privacy_status=PrivacyStatus.PRIVATE,
        ),
        YouTubeVideo(
            video_id="video-02",
            title="02 Exploration Theme",
            description="Exploration description",
            privacy_status=PrivacyStatus.PRIVATE,
        ),
        YouTubeVideo(
            video_id="video-01",
            title="01 Opening Theme",
            description="Opening description",
            privacy_status=PrivacyStatus.PRIVATE,
        ),
    )


def test_discover_skips_unrelated_private_videos_between_expected_videos():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-03",
                "03 Battle Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-unrelated-01",
                "Other Album - 05 Track",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-02",
                "02 Exploration Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-unrelated-02",
                "Silent Hill 2 OST",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=(
            "03 Battle Theme",
            "02 Exploration Theme",
            "01 Opening Theme",
        )
    )

    assert [video.video_id for video in result] == [
        "video-03",
        "video-02",
        "video-01",
    ]


def test_discover_ignores_public_and_unlisted_videos():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-public",
                "Public Video",
                None,
                "public",
            ),
            _create_playlist_item(
                "video-02",
                "02 Battle Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-unlisted",
                "Unlisted Video",
                None,
                "unlisted",
            ),
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=(
            "02 Battle Theme",
            "01 Opening Theme",
        )
    )

    assert [video.video_id for video in result] == [
        "video-02",
        "video-01",
    ]


def test_discover_raises_when_expected_video_is_missing():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-unrelated",
                "Unrelated Private Video",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        RuntimeError,
        match="Not all expected YouTube videos were discovered",
    ):
        discovery.discover(
            expected_video_titles=(
                "01 Opening Theme",
                "02 Missing Theme",
            )
        )


def test_discover_raises_when_playlist_is_empty():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [],
    }

    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        RuntimeError,
        match="Not all expected YouTube videos were discovered",
    ):
        discovery.discover(
            expected_video_titles=("01 Opening Theme",)
        )


def test_discover_handles_private_videos_without_description():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=("01 Opening Theme",)
    )

    assert len(result) == 1
    assert result[0].video_id == "video-01"
    assert result[0].title == "01 Opening Theme"
    assert result[0].description is None
    assert result[0].privacy_status is PrivacyStatus.PRIVATE


def test_discover_matches_numbered_videos_by_numeric_prefix():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-02",
                "02 Exploration Theme Orchestral Mix",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-01",
                "01 Opening Theme - Remastered",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=(
            "02 Exploration Theme",
            "01 Opening Theme",
        )
    )

    assert [video.video_id for video in result] == [
        "video-02",
        "video-01",
    ]


def test_discover_matches_compilation_by_exact_title():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-compilation",
                "Crysis | Re-Engineered Soundtrack",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=("Crysis | Re-Engineered Soundtrack",)
    )

    assert [video.video_id for video in result] == ["video-compilation"]


def test_discover_does_not_match_compilation_by_partial_title():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-compilation",
                "Crysis | Re-Engineered Soundtrack Extended",
                None,
                "private",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        RuntimeError,
        match="Not all expected YouTube videos were discovered",
    ):
        discovery.discover(
            expected_video_titles=("Crysis | Re-Engineered Soundtrack",)
        )


def test_discover_rejects_empty_expected_video_titles():
    methods = _create_methods()
    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        ValueError,
        match="expected_video_titles must not be empty",
    ):
        discovery.discover(expected_video_titles=())


def test_discover_raises_when_authenticated_channel_is_not_found():
    methods = MagicMock(spec=YouTubeMethods)
    methods.channels_list.return_value = {"items": []}

    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        RuntimeError,
        match="Authenticated YouTube channel was not found",
    ):
        discovery.discover(
            expected_video_titles=("01 Opening Theme",)
        )


def test_discover_raises_when_uploads_playlist_is_not_found():
    methods = MagicMock(spec=YouTubeMethods)
    methods.channels_list.return_value = {
        "items": [
            {
                "contentDetails": {
                    "relatedPlaylists": {},
                },
            },
        ],
    }

    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        RuntimeError,
        match="YouTube uploads playlist was not found",
    ):
        discovery.discover(
            expected_video_titles=("01 Opening Theme",)
        )

def test_discover_uses_multiple_pagination_strategies_until_all_expected_videos_are_found():
    methods = _create_methods()

    methods.playlist_items_list.side_effect = [
        {
            "items": [
                _create_playlist_item(
                    "video-unrelated-01",
                    "Unrelated Private Video",
                    None,
                    "private",
                ),
                _create_playlist_item(
                    "video-03",
                    "03 Battle Theme",
                    None,
                    "private",
                ),
            ],
        },
        {
            "items": [
                _create_playlist_item(
                    "video-unrelated-02",
                    "Silent Hill 2 OST",
                    None,
                    "private",
                ),
                _create_playlist_item(
                    "video-02",
                    "02 Exploration Theme",
                    None,
                    "private",
                ),
            ],
        },
        {
            "items": [
                _create_playlist_item(
                    "video-public",
                    "Public Video",
                    None,
                    "public",
                ),
                _create_playlist_item(
                    "video-01",
                    "01 Opening Theme",
                    None,
                    "private",
                ),
            ],
        },
    ]

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover(
        expected_video_titles=(
            "03 Battle Theme",
            "02 Exploration Theme",
            "01 Opening Theme",
        )
    )

    assert [video.video_id for video in result] == [
        "video-03",
        "video-02",
        "video-01",
    ]

    assert methods.playlist_items_list.call_count == 3

    first_call = methods.playlist_items_list.call_args_list[0]
    second_call = methods.playlist_items_list.call_args_list[1]
    third_call = methods.playlist_items_list.call_args_list[2]

    assert first_call.kwargs == {
        "playlist_id": UPLOADS_PLAYLIST_ID,
        "max_results": 50,
        "page_token": None,
    }

    assert second_call.kwargs == {
        "playlist_id": UPLOADS_PLAYLIST_ID,
        "max_results": 34,
        "page_token": None,
    }

    assert third_call.kwargs == {
        "playlist_id": UPLOADS_PLAYLIST_ID,
        "max_results": 23,
        "page_token": None,
    }


def test_build_max_results_strategy():
    assert YouTubeDiscovery._build_max_results_strategy() == (50, 34, 23)