from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


class YouTubeClient:
    """Provide an authenticated YouTube Data API client."""

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
        self._service = self._authenticate()

    @property
    def service(self) -> Resource:
        """Return the authenticated YouTube API service."""
        return self._service

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