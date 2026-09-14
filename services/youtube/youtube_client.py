from __future__ import annotations

from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from rich.console import Console


class YouTubeApiError(RuntimeError):
    """Raised when the YouTube Data API returns an error."""


class YouTubeQuotaExceededError(YouTubeApiError):
    """Raised when YouTube rejects a request because the quota is exhausted."""


class YouTubeClient:
    """Provide authenticated and encapsulated access to the YouTube Data API."""

    SCOPES = [
        "https://www.googleapis.com/auth/youtube",
    ]

    def __init__(
        self,
        client_secrets_path: Path,
        token_path: Path,
    ) -> None:
        self._client_secrets_path = client_secrets_path
        self._token_path = token_path
        self._console = Console()
        self._service = self._authenticate()

    @property
    def service(self) -> Resource:
        """Return the authenticated YouTube API service."""
        return self._service

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

    def _authenticate(self) -> Resource:
        """Authenticate the user and create the YouTube API service."""
        credentials = self._load_credentials()

        if credentials is None or not credentials.valid:
            credentials = self._refresh_or_authorize(credentials)

        self._save_credentials(credentials)

        return build(
            "youtube",
            "v3",
            credentials=credentials,
        )

    def _load_credentials(self) -> Credentials | None:
        """Load previously stored OAuth credentials."""
        if not self._token_path.exists():
            return None

        return Credentials.from_authorized_user_file(
            str(self._token_path),
            self.SCOPES,
        )

    def _refresh_or_authorize(
        self,
        credentials: Credentials | None,
    ) -> Credentials:
        """Refresh existing credentials or perform OAuth authorization."""
        if credentials is not None and credentials.expired:
            if credentials.refresh_token is None:
                raise RuntimeError(
                    "Stored YouTube credentials have expired and "
                    "contain no refresh token."
                )

            credentials.refresh(Request())
            return credentials

        flow = InstalledAppFlow.from_client_secrets_file(
            str(self._client_secrets_path),
            self.SCOPES,
        )

        return flow.run_local_server(port=0)

    def _save_credentials(self, credentials: Credentials) -> None:
        """Persist OAuth credentials locally."""
        self._token_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._token_path.write_text(
            credentials.to_json(),
            encoding="utf-8",
        )
