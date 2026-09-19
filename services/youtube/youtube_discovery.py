from __future__ import annotations

from typing import Any

from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo
from services.youtube.api.methods import YouTubeMethods


class YouTubeDiscovery:
    """Discover the current album videos uploaded to YouTube."""

    def __init__(self, methods: YouTubeMethods) -> None:
        self._methods = methods

    def discover(self, expected_video_count: int) -> tuple[YouTubeVideo, ...]:
        """Discover the first continuous sequence of private videos."""

        if expected_video_count <= 0:
            raise ValueError("expected_video_count must be greater than zero.")

        uploads_playlist_id = self._get_uploads_playlist_id()

        videos: list[YouTubeVideo] = []
        found_private_block = False
        page_token: str | None = None

        while True:
            response = self._methods.playlist_items_list(
                playlist_id=uploads_playlist_id,
                page_token=page_token,
            )

            for item in response.get("items", []):
                video = self._map_video(item)

                if video.privacy_status is PrivacyStatus.PRIVATE:
                    found_private_block = True
                    videos.append(video)
                    if len(videos) == expected_video_count:
                        return tuple(videos)
                    continue

                if found_private_block:
                    return tuple(videos)

            page_token = response.get("nextPageToken")

            if page_token is None:
                return tuple(videos)

    def _get_uploads_playlist_id(self) -> str:
        """Return the authenticated user's uploads playlist ID."""

        response = self._methods.channels_list()

        items = response.get("items", [])

        if not items:
            raise RuntimeError("Authenticated YouTube channel was not found.")

        playlist_id = (
            items[0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )

        if not playlist_id:
            raise RuntimeError("YouTube uploads playlist was not found.")

        return playlist_id

    @staticmethod
    def _map_video(item: dict[str, Any]) -> YouTubeVideo:
        """Create a YouTubeVideo from a playlist item."""

        content_details = item.get("contentDetails", {})
        snippet = item.get("snippet", {})
        status = item.get("status", {})

        return YouTubeVideo(
            video_id=content_details["videoId"],
            title=snippet["title"],
            description=snippet.get("description"),
            privacy_status=PrivacyStatus(status["privacyStatus"]),
        )