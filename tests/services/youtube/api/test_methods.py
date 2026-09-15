from unittest.mock import MagicMock, patch

import pytest

from googleapiclient.errors import HttpError

from services.youtube.api.methods import (
    YouTubeApiError,
    YouTubeMethods,
    YouTubeQuotaExceededError,
)


@pytest.fixture
def client():
    client = MagicMock()
    client.service = MagicMock()
    return client


@pytest.fixture
def methods(client):
    return YouTubeMethods(client)


def test_channels_list(methods, client):
    request = MagicMock()
    request.execute.return_value = {
        "items": [
            {
                "id": "channel-id",
            }
        ]
    }

    client.service.channels.return_value.list.return_value = request

    result = methods.channels_list()

    client.service.channels.return_value.list.assert_called_once_with(
        part="contentDetails",
        mine=True,
    )
    request.execute.assert_called_once()

    assert result == {
        "items": [
            {
                "id": "channel-id",
            }
        ]
    }


def test_channels_list_accepts_custom_parameters(methods, client):
    request = MagicMock()
    request.execute.return_value = {"items": []}

    client.service.channels.return_value.list.return_value = request

    result = methods.channels_list(
        part="snippet,contentDetails",
        mine=False,
    )

    client.service.channels.return_value.list.assert_called_once_with(
        part="snippet,contentDetails",
        mine=False,
    )
    request.execute.assert_called_once()

    assert result == {"items": []}


def test_playlist_items_list_without_page_token(methods, client):
    request = MagicMock()
    request.execute.return_value = {
        "items": [],
        "nextPageToken": "next-page",
    }

    client.service.playlistItems.return_value.list.return_value = request

    result = methods.playlist_items_list(
        playlist_id="PL_TEST",
    )

    client.service.playlistItems.return_value.list.assert_called_once_with(
        part="snippet,contentDetails,status",
        playlistId="PL_TEST",
        maxResults=50,
    )
    request.execute.assert_called_once()

    assert result["nextPageToken"] == "next-page"


def test_playlist_items_list_with_page_token(methods, client):
    request = MagicMock()
    request.execute.return_value = {"items": []}

    client.service.playlistItems.return_value.list.return_value = request

    methods.playlist_items_list(
        playlist_id="PL_TEST",
        part="snippet",
        max_results=25,
        page_token="page-token",
    )

    client.service.playlistItems.return_value.list.assert_called_once_with(
        part="snippet",
        playlistId="PL_TEST",
        maxResults=25,
        pageToken="page-token",
    )
    request.execute.assert_called_once()


def test_videos_list(methods, client):
    request = MagicMock()
    request.execute.return_value = {
        "items": [
            {
                "id": "video-01",
            },
            {
                "id": "video-02",
            },
        ]
    }

    client.service.videos.return_value.list.return_value = request

    result = methods.videos_list(
        video_ids=["video-01", "video-02"],
    )

    client.service.videos.return_value.list.assert_called_once_with(
        part="snippet,status",
        id="video-01,video-02",
    )
    request.execute.assert_called_once()

    assert len(result["items"]) == 2


def test_videos_list_rejects_empty_video_ids(methods):
    with pytest.raises(
        ValueError,
        match="video_ids must not be empty",
    ):
        methods.videos_list(video_ids=[])


def test_videos_list_accepts_custom_part(methods, client):
    request = MagicMock()
    request.execute.return_value = {"items": []}

    client.service.videos.return_value.list.return_value = request

    methods.videos_list(
        video_ids=["video-01"],
        part="snippet,status,contentDetails",
    )

    client.service.videos.return_value.list.assert_called_once_with(
        part="snippet,status,contentDetails",
        id="video-01",
    )


def test_videos_update(methods, client):
    request = MagicMock()
    request.execute.return_value = {
        "id": "video-01",
    }

    client.service.videos.return_value.update.return_value = request

    video_resource = {
        "id": "video-01",
        "snippet": {
            "title": "Updated title",
        },
    }

    result = methods.videos_update(
        video_resource=video_resource,
    )

    client.service.videos.return_value.update.assert_called_once_with(
        part="snippet,status",
        body=video_resource,
    )
    request.execute.assert_called_once()

    assert result["id"] == "video-01"


def test_videos_update_accepts_custom_part(methods, client):
    request = MagicMock()
    request.execute.return_value = {"id": "video-01"}

    client.service.videos.return_value.update.return_value = request

    methods.videos_update(
        video_resource={"id": "video-01"},
        part="snippet",
    )

    client.service.videos.return_value.update.assert_called_once_with(
        part="snippet",
        body={"id": "video-01"},
    )


def test_thumbnails_set(methods, client, tmp_path):
    thumbnail_path = tmp_path / "thumbnail.jpg"
    thumbnail_path.write_bytes(b"fake image data")

    request = MagicMock()
    request.execute.return_value = {
        "items": [
            {
                "default": {
                    "url": "https://example.com/thumbnail.jpg",
                }
            }
        ]
    }

    client.service.thumbnails.return_value.set.return_value = request

    with patch(
        "services.youtube.api.methods.MediaFileUpload"
    ) as media_upload:
        media = MagicMock()
        media_upload.return_value = media

        result = methods.thumbnails_set(
            video_id="video-01",
            thumbnail_path=thumbnail_path,
        )

    media_upload.assert_called_once_with(
        str(thumbnail_path),
        mimetype="image/jpeg",
    )

    client.service.thumbnails.return_value.set.assert_called_once_with(
        videoId="video-01",
        media_body=media,
    )

    request.execute.assert_called_once()

    assert result["items"]


def test_thumbnails_set_rejects_missing_file(methods, tmp_path):
    thumbnail_path = tmp_path / "missing.jpg"

    with pytest.raises(
        FileNotFoundError,
        match="Thumbnail file does not exist",
    ):
        methods.thumbnails_set(
            video_id="video-01",
            thumbnail_path=thumbnail_path,
        )


def test_playlists_list_without_page_token(methods, client):
    request = MagicMock()
    request.execute.return_value = {
        "items": [
            {
                "id": "playlist-01",
            }
        ]
    }

    client.service.playlists.return_value.list.return_value = request

    result = methods.playlists_list()

    client.service.playlists.return_value.list.assert_called_once_with(
        part="snippet,contentDetails",
        mine=True,
        maxResults=50,
    )
    request.execute.assert_called_once()

    assert result["items"][0]["id"] == "playlist-01"


def test_playlists_list_with_page_token(methods, client):
    request = MagicMock()
    request.execute.return_value = {"items": []}

    client.service.playlists.return_value.list.return_value = request

    methods.playlists_list(
        part="snippet",
        mine=False,
        max_results=20,
        page_token="page-token",
    )

    client.service.playlists.return_value.list.assert_called_once_with(
        part="snippet",
        mine=False,
        maxResults=20,
        pageToken="page-token",
    )


def test_playlist_items_insert(methods, client):
    request = MagicMock()
    request.execute.return_value = {
        "id": "playlist-item-id",
    }

    client.service.playlistItems.return_value.insert.return_value = request

    playlist_item_resource = {
        "snippet": {
            "playlistId": "PL_TEST",
            "resourceId": {
                "kind": "youtube#video",
                "videoId": "video-01",
            },
        }
    }

    result = methods.playlist_items_insert(
        playlist_item_resource=playlist_item_resource,
    )

    client.service.playlistItems.return_value.insert.assert_called_once_with(
        part="snippet",
        body=playlist_item_resource,
    )
    request.execute.assert_called_once()

    assert result["id"] == "playlist-item-id"


def test_playlist_items_insert_accepts_custom_part(methods, client):
    request = MagicMock()
    request.execute.return_value = {}

    client.service.playlistItems.return_value.insert.return_value = request

    methods.playlist_items_insert(
        playlist_item_resource={"snippet": {}},
        part="snippet,contentDetails",
    )

    client.service.playlistItems.return_value.insert.assert_called_once_with(
        part="snippet,contentDetails",
        body={"snippet": {}},
    )


def test_execute_returns_response(methods):
    request = MagicMock()
    request.execute.return_value = {"success": True}

    result = methods._execute(
        "test.operation",
        request,
    )

    request.execute.assert_called_once()
    assert result == {"success": True}


def test_execute_translates_quota_exceeded_error(methods):
    error = HttpError(
        resp=MagicMock(status=403),
        content=b'{"error": {"errors": [{"reason": "quotaExceeded"}]}}',
    )

    request = MagicMock()
    request.execute.side_effect = error

    with pytest.raises(YouTubeQuotaExceededError) as exception:
        methods._execute(
            "videos.update",
            request,
        )

    assert str(exception.value) == (
        "YouTube API quota has been exceeded."
    )


def test_execute_translates_other_http_error(methods):
    error = HttpError(
        resp=MagicMock(status=403),
        content=b'{"error": {"errors": [{"reason": "forbidden"}]}}',
    )

    request = MagicMock()
    request.execute.side_effect = error

    with pytest.raises(YouTubeApiError) as exception:
        methods._execute(
            "videos.update",
            request,
        )

    assert "YouTube API request failed for videos.update" in str(
        exception.value
    )


@pytest.mark.parametrize(
    "content",
    [
        b'{"reason": "quotaExceeded"}',
    ],
)
def test_is_quota_exceeded_detects_quota_error(methods, content):
    error = HttpError(
        resp=MagicMock(status=403),
        content=content,
    )

    assert methods._is_quota_exceeded(error)


def test_is_quota_exceeded_rejects_other_errors(methods):
    error = HttpError(
        resp=MagicMock(status=403),
        content=b'{"reason": "forbidden"}',
    )

    assert not methods._is_quota_exceeded(error)
