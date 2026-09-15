from unittest.mock import MagicMock, patch

import pytest

from services.youtube.api.client import YouTubeClient


def test_loads_valid_existing_credentials(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(
        '{"token": "test-token"}',
        encoding="utf-8",
    )

    client_secrets_path = tmp_path / "client_secrets.json"

    credentials = MagicMock()
    credentials.valid = True
    credentials.to_json.return_value = '{"token": "test-token"}'

    with (
        patch(
            "services.youtube.api.client.Credentials.from_authorized_user_file",
            return_value=credentials,
        ) as load_credentials,
        patch(
            "services.youtube.api.client.build",
            return_value=MagicMock(),
        ) as build,
    ):
        client = YouTubeClient(
            client_secrets_path=client_secrets_path,
            token_path=token_path,
        )

    load_credentials.assert_called_once_with(
        str(token_path),
        YouTubeClient.SCOPES,
    )
    build.assert_called_once()
    assert client.service is build.return_value


def test_authenticates_when_credentials_do_not_exist(tmp_path):
    token_path = tmp_path / "token.json"
    client_secrets_path = tmp_path / "client_secrets.json"

    credentials = MagicMock()
    credentials.to_json.return_value = '{"token": "new-token"}'

    flow = MagicMock()
    flow.run_local_server.return_value = credentials

    with (
        patch(
            "services.youtube.api.client.InstalledAppFlow.from_client_secrets_file",
            return_value=flow,
        ) as create_flow,
        patch(
            "services.youtube.api.client.build",
            return_value=MagicMock(),
        ),
    ):
        YouTubeClient(
            client_secrets_path=client_secrets_path,
            token_path=token_path,
        )

    create_flow.assert_called_once_with(
        str(client_secrets_path),
        YouTubeClient.SCOPES,
    )

    flow.run_local_server.assert_called_once_with(port=0)

    assert token_path.exists()
    assert token_path.read_text(encoding="utf-8") == '{"token": "new-token"}'


def test_refreshes_expired_credentials(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(
        '{"token": "old-token"}',
        encoding="utf-8",
    )

    client_secrets_path = tmp_path / "client_secrets.json"

    credentials = MagicMock()
    credentials.valid = False
    credentials.expired = True
    credentials.refresh_token = "refresh-token"
    credentials.to_json.return_value = '{"token": "refreshed-token"}'

    with (
        patch(
            "services.youtube.api.client.Credentials.from_authorized_user_file",
            return_value=credentials,
        ),
        patch(
            "services.youtube.api.client.build",
            return_value=MagicMock(),
        ),
    ):
        YouTubeClient(
            client_secrets_path=client_secrets_path,
            token_path=token_path,
        )

    credentials.refresh.assert_called_once()

    assert token_path.read_text(encoding="utf-8") == (
        '{"token": "refreshed-token"}'
    )


def test_rejects_expired_credentials_without_refresh_token(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(
        '{"token": "old-token"}',
        encoding="utf-8",
    )

    client_secrets_path = tmp_path / "client_secrets.json"

    credentials = MagicMock()
    credentials.valid = False
    credentials.expired = True
    credentials.refresh_token = None

    with patch(
        "services.youtube.api.client.Credentials.from_authorized_user_file",
        return_value=credentials,
    ):
        with pytest.raises(
            RuntimeError,
            match="contain no refresh token",
        ):
            YouTubeClient(
                client_secrets_path=client_secrets_path,
                token_path=token_path,
            )


def test_authorizes_when_credentials_are_invalid_but_not_expired(tmp_path):
    token_path = tmp_path / "token.json"
    token_path.write_text(
        '{"token": "invalid-token"}',
        encoding="utf-8",
    )

    client_secrets_path = tmp_path / "client_secrets.json"

    stored_credentials = MagicMock()
    stored_credentials.valid = False
    stored_credentials.expired = False

    authorized_credentials = MagicMock()
    authorized_credentials.to_json.return_value = (
        '{"token": "authorized-token"}'
    )

    flow = MagicMock()
    flow.run_local_server.return_value = authorized_credentials

    with (
        patch(
            "services.youtube.api.client.Credentials.from_authorized_user_file",
            return_value=stored_credentials,
        ),
        patch(
            "services.youtube.api.client.InstalledAppFlow.from_client_secrets_file",
            return_value=flow,
        ),
        patch(
            "services.youtube.api.client.build",
            return_value=MagicMock(),
        ),
    ):
        YouTubeClient(
            client_secrets_path=client_secrets_path,
            token_path=token_path,
        )

    flow.run_local_server.assert_called_once_with(port=0)

    assert token_path.read_text(encoding="utf-8") == (
        '{"token": "authorized-token"}'
    )


def test_creates_parent_directory_when_saving_credentials(tmp_path):
    token_path = tmp_path / "nested" / "directory" / "token.json"

    credentials = MagicMock()
    credentials.to_json.return_value = '{"token": "test-token"}'

    client_secrets_path = tmp_path / "client_secrets.json"

    with (
        patch(
            "services.youtube.api.client.InstalledAppFlow.from_client_secrets_file",
        ) as create_flow,
        patch(
            "services.youtube.api.client.build",
            return_value=MagicMock(),
        ),
    ):
        flow = create_flow.return_value
        flow.run_local_server.return_value = credentials

        YouTubeClient(
            client_secrets_path=client_secrets_path,
            token_path=token_path,
        )

    assert token_path.exists()
    assert token_path.read_text(encoding="utf-8") == (
        '{"token": "test-token"}'
    )