import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from interfaces.web import launcher


def test_wait_for_server_returns_true_when_connected(monkeypatch):
    mock_socket = MagicMock()
    monkeypatch.setattr(launcher.socket, "create_connection", Mock(return_value=mock_socket))

    assert launcher.wait_for_server("127.0.0.1", 8000, timeout=0.5) is True


def test_wait_for_server_returns_false_when_timeout(monkeypatch):
    monkeypatch.setattr(
        launcher.socket,
        "create_connection",
        Mock(side_effect=ConnectionRefusedError("Connection refused")),
    )

    assert launcher.wait_for_server("127.0.0.1", 8000, timeout=0.1) is False


def test_open_browser_when_ready_waits_and_opens_url(monkeypatch):
    wait_mock = Mock(return_value=True)
    open_mock = Mock()
    monkeypatch.setattr(launcher, "wait_for_server", wait_mock)
    monkeypatch.setattr(launcher.webbrowser, "open", open_mock)

    launcher.open_browser_when_ready("http://localhost:8000", "127.0.0.1", 8000, timeout=1.0)

    wait_mock.assert_called_once_with("127.0.0.1", 8000, timeout=1.0)
    open_mock.assert_called_once_with("http://localhost:8000")


def test_setup_django_environment_configures_sys_path_and_django(monkeypatch):
    django_mock = Mock()
    monkeypatch.setattr(launcher, "django", django_mock)

    launcher.setup_django_environment()

    django_mock.setup.assert_called_once()
    assert any("interfaces" in path for path in sys.path)


@patch("threading.Thread")
def test_launch_web_server_starts_runserver_and_browser_thread(thread_mock, monkeypatch):
    setup_mock = Mock()
    call_command_mock = Mock()

    monkeypatch.setattr(launcher, "setup_django_environment", setup_mock)
    monkeypatch.setattr(
        "django.core.management.call_command",
        call_command_mock,
        raising=False,
    )

    launcher.launch_web_server("127.0.0.1", 8000, open_browser=True, browser_timeout=2.0)

    setup_mock.assert_called_once()
    thread_mock.assert_called_once_with(
        target=launcher.open_browser_when_ready,
        args=("http://localhost:8000", "127.0.0.1", 8000, 2.0),
        daemon=True,
    )
    thread_mock.return_value.start.assert_called_once()
    call_command_mock.assert_called_once_with("runserver", "127.0.0.1:8000", use_reloader=False)


@patch("threading.Thread")
def test_launch_web_server_without_browser(thread_mock, monkeypatch):
    setup_mock = Mock()
    call_command_mock = Mock()

    monkeypatch.setattr(launcher, "setup_django_environment", setup_mock)
    monkeypatch.setattr(
        "django.core.management.call_command",
        call_command_mock,
        raising=False,
    )

    launcher.launch_web_server("0.0.0.0", 9000, open_browser=False)

    setup_mock.assert_called_once()
    thread_mock.assert_not_called()
    call_command_mock.assert_called_once_with("runserver", "0.0.0.0:9000", use_reloader=False)
