from __future__ import annotations

from pathlib import Path
from typing import Any

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from rich.console import Console

from services.youtube.api.client import YouTubeClient


class YouTubeApiError(RuntimeError):
    """Raised when the YouTube Data API returns an error."""


class YouTubeQuotaExceededError(YouTubeApiError):
    """Raised when YouTube rejects a request because the quota is exhausted."""


class YouTubeMethods:
    """Provide concrete operations against the YouTube Data API."""

    def __init__(self, client: YouTubeClient) -> None:
        self._service = client.service
        self._console = Console()

    def channels_list(
        self,
        *,
        part: str = "contentDetails",
        mine: bool = True,
    ) -> dict[str, Any]:
        """Retrieve channel information for the authenticated user."""
        return self._execute(
            "channels.list",
            self._service.channels().list(
                part=part,
                mine=mine,
            ),
        )

    def playlist_items_list(
        self,
        *,
        playlist_id: str,
        part: str = "snippet,contentDetails,status",
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve a page of items from a YouTube playlist."""
        request_kwargs: dict[str, Any] = {
            "part": part,
            "playlistId": playlist_id,
            "maxResults": max_results,
        }

        if page_token is not None:
            request_kwargs["pageToken"] = page_token

        return self._execute(
            "playlistItems.list",
            self._service.playlistItems().list(**request_kwargs),
        )

    def videos_list(
        self,
        *,
        video_ids: list[str],
        part: str = "snippet,status",
    ) -> dict[str, Any]:
        """Retrieve information for one or more YouTube videos."""
        if not video_ids:
            raise ValueError("video_ids must not be empty.")

        return self._execute(
            "videos.list",
            self._service.videos().list(
                part=part,
                id=",".join(video_ids),
            ),
        )

    def videos_update(
        self,
        *,
        video_resource: dict[str, Any],
        part: str = "snippet,status",
    ) -> dict[str, Any]:
        """Update a YouTube video."""
        return self._execute(
            "videos.update",
            self._service.videos().update(
                part=part,
                body=video_resource,
            ),
        )

    def thumbnails_set(
        self,
        *,
        video_id: str,
        thumbnail_path: Path,
    ) -> dict[str, Any]:
        """Set a video's custom thumbnail."""
        if not thumbnail_path.is_file():
            raise FileNotFoundError(
                f"Thumbnail file does not exist: {thumbnail_path}"
            )

        media = MediaFileUpload(
            str(thumbnail_path),
            mimetype="image/jpeg",
        )

        return self._execute(
            "thumbnails.set",
            self._service.thumbnails().set(
                videoId=video_id,
                media_body=media,
            ),
        )

    def playlists_list(
        self,
        *,
        part: str = "snippet,contentDetails",
        mine: bool = True,
        max_results: int = 50,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve a page of playlists for the authenticated user."""
        request_kwargs: dict[str, Any] = {
            "part": part,
            "mine": mine,
            "maxResults": max_results,
        }

        if page_token is not None:
            request_kwargs["pageToken"] = page_token

        return self._execute(
            "playlists.list",
            self._service.playlists().list(**request_kwargs),
        )

    def playlist_items_insert(
        self,
        *,
        playlist_item_resource: dict[str, Any],
        part: str = "snippet",
    ) -> dict[str, Any]:
        """Add a video to a YouTube playlist."""
        return self._execute(
            "playlistItems.insert",
            self._service.playlistItems().insert(
                part=part,
                body=playlist_item_resource,
            ),
        )

    def _execute(
        self,
        operation: str,
        request: Any,
    ) -> dict[str, Any]:
        """Execute an API request and translate Google API errors."""
        try:
            response = request.execute()
        except HttpError as error:
            if self._is_quota_exceeded(error):
                self._console.print(
                    f"[red][YouTube API][/red] "
                    f"[bold]{operation}[/bold] → quotaExceeded"
                )
                raise YouTubeQuotaExceededError(
                    "YouTube API quota has been exceeded."
                ) from error

            self._console.print(
                f"[red][YouTube API][/red] "
                f"[bold]{operation}[/bold] → HTTP {error.resp.status}"
            )
            raise YouTubeApiError(
                f"YouTube API request failed for {operation}: {error}"
            ) from error

        self._console.print(
            f"[green][YouTube API][/green] "
            f"[bold]{operation}[/bold] → OK"
        )
        return response

    @staticmethod
    def _is_quota_exceeded(error: HttpError) -> bool:
        """Return whether an API error represents exhausted quota."""
        content = error.content

        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")

        return "quotaExceeded" in str(content)