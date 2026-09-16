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


def test_discover_returns_continuous_private_videos():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-04",
                "Compilation",
                "Compilation description",
                "private",
            ),
            _create_playlist_item(
                "video-03",
                "03 Battle Theme",
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
                "video-01",
                "01 Opening Theme",
                "Opening description",
                "private",
            ),
            _create_playlist_item(
                "video-old",
                "Older Video",
                "Older description",
                "public",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert result == (
        YouTubeVideo(
            video_id="video-04",
            title="Compilation",
            description="Compilation description",
            privacy_status=PrivacyStatus.PRIVATE,
        ),
        YouTubeVideo(
            video_id="video-03",
            title="03 Battle Theme",
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


def test_discover_stops_at_public_video():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-02",
                "02 Battle Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-old",
                "Older Video",
                None,
                "public",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert len(result) == 2
    assert all(
        video.privacy_status is PrivacyStatus.PRIVATE
        for video in result
    )


def test_discover_stops_at_unlisted_video():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-02",
                "02 Battle Theme",
                None,
                "private",
            ),
            _create_playlist_item(
                "video-01",
                "01 Opening Theme",
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
                "video-old",
                "Older Video",
                None,
                "public",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert len(result) == 2
    assert [video.video_id for video in result] == [
        "video-02",
        "video-01",
    ]


def test_discover_returns_empty_tuple_when_first_video_is_public():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-old",
                "Older Video",
                None,
                "public",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert result == ()


def test_discover_returns_empty_tuple_when_first_video_is_unlisted():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [
            _create_playlist_item(
                "video-unlisted",
                "Unlisted Video",
                None,
                "unlisted",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert result == ()


def test_discover_follows_pagination():
    methods = _create_methods()

    methods.playlist_items_list.side_effect = [
        {
            "items": [
                _create_playlist_item(
                    "video-02",
                    "02 Battle Theme",
                    None,
                    "private",
                ),
                _create_playlist_item(
                    "video-01",
                    "01 Opening Theme",
                    None,
                    "private",
                ),
            ],
            "nextPageToken": "PAGE_2",
        },
        {
            "items": [
                _create_playlist_item(
                    "video-older",
                    "Older Video",
                    None,
                    "public",
                ),
            ],
        },
    ]

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert [video.video_id for video in result] == [
        "video-02",
        "video-01",
    ]

    assert methods.playlist_items_list.call_count == 2

    first_call = methods.playlist_items_list.call_args_list[0]
    second_call = methods.playlist_items_list.call_args_list[1]

    assert first_call.kwargs == {
        "playlist_id": UPLOADS_PLAYLIST_ID,
        "page_token": None,
    }

    assert second_call.kwargs == {
        "playlist_id": UPLOADS_PLAYLIST_ID,
        "page_token": "PAGE_2",
    }


def test_discover_does_not_request_next_page_after_cutoff():
    methods = _create_methods()

    methods.playlist_items_list.side_effect = [
        {
            "items": [
                _create_playlist_item(
                    "video-02",
                    "02 Battle Theme",
                    None,
                    "private",
                ),
                _create_playlist_item(
                    "video-old",
                    "Older Video",
                    None,
                    "public",
                ),
            ],
            "nextPageToken": "PAGE_2",
        },
        {
            "items": [
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

    result = discovery.discover()

    assert [video.video_id for video in result] == ["video-02"]
    assert methods.playlist_items_list.call_count == 1


def test_discover_returns_empty_tuple_when_playlist_is_empty():
    methods = _create_methods()

    methods.playlist_items_list.return_value = {
        "items": [],
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert result == ()


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
            _create_playlist_item(
                "video-old",
                "Older Video",
                None,
                "public",
            ),
        ]
    }

    discovery = YouTubeDiscovery(methods)

    result = discovery.discover()

    assert len(result) == 1
    assert result[0].video_id == "video-01"
    assert result[0].title == "01 Opening Theme"
    assert result[0].description is None
    assert result[0].privacy_status is PrivacyStatus.PRIVATE


def test_discover_raises_when_authenticated_channel_is_not_found():
    methods = MagicMock(spec=YouTubeMethods)
    methods.channels_list.return_value = {"items": []}

    discovery = YouTubeDiscovery(methods)

    with pytest.raises(
        RuntimeError,
        match="Authenticated YouTube channel was not found",
    ):
        discovery.discover()


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
        discovery.discover()
