
import pytest
from unittest.mock import patch
import json

from django.http import Http404
from django.test import RequestFactory

from interfaces.web.apps.video_music_web.progress.runtime import (
    job_registry,
)
from interfaces.web.apps.video_music_web.progress.job_runner import (
    run_video_music_job,
)
from interfaces.web.apps.video_music_web.views import (
    IndexView,
    JobProgressView,
    JobStatusView,
)


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_job_status_returns_json(request_factory, tmp_path):
    job_id = job_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=10,
    )

    request = request_factory.get(
        f"/video-music/jobs/{job_id}/status/"
    )
    response = JobStatusView.as_view()(
        request,
        job_id=job_id,
    )

    assert response.status_code == 200

    payload = json.loads(response.content)
    assert payload["job"]["job_id"] == job_id
    assert payload["job"]["status"] == "queued"
    assert payload["job"]["total_tracks"] == 0
    assert payload["job"]["tracks"] == []


def test_job_status_returns_404_for_unknown_job(request_factory):
    request = request_factory.get(
        "/video-music/jobs/unknown/status/"
    )

    with pytest.raises(Http404):
        JobStatusView.as_view()(
            request,
            job_id="unknown",
        )


@patch("interfaces.web.apps.video_music_web.views.messages.success")
@patch("interfaces.web.apps.video_music_web.views.Thread")
@patch("interfaces.web.apps.video_music_web.views.job_registry")
@patch("interfaces.web.apps.video_music_web.views.ConfigManager")
def test_index_post_starts_background_job(
    config_manager_class,
    registry,
    thread_class,
    messages_success,
    request_factory,
    tmp_path,
):
    audios_dir = tmp_path / "audio"
    audios_dir.mkdir()

    video_path = tmp_path / "base.mkv"
    video_path.touch()

    job_id = "job-123"
    registry.create_job.return_value = job_id

    request = request_factory.post(
        "/video-music/",
        {
            "max_items_per_dir": "10",
            "audios_dir": str(audios_dir),
            "video_path": str(video_path),
            "output_dir": "output",
        },
    )

    response = IndexView.as_view()(request)

    assert response.status_code == 302
    assert response.url == f"/video-music/jobs/{job_id}/"

    registry.create_job.assert_called_once()
    thread_class.assert_called_once()

    thread_class.assert_called_once()
    thread_class.assert_called_once_with(
        target=run_video_music_job,
        args=(job_id, thread_class.call_args.kwargs["args"][1]),
        daemon=True,
    )

    thread = thread_class.return_value
    thread.start.assert_called_once()

    args = thread_class.call_args.kwargs["args"]
    assert args[0] == job_id
    assert args[1].audios_dir == audios_dir
    assert args[1].video_path == video_path
    assert args[1].output_dir == audios_dir / "output"
    assert args[1].max_items_per_dir == 10


def test_job_progress_returns_page_for_existing_job(
    request_factory,
    tmp_path,
):
    job_id = job_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=10,
    )

    request = request_factory.get(
        f"/video-music/jobs/{job_id}/"
    )
    response = JobProgressView.as_view()(
        request,
        job_id=job_id,
    )

    assert response.status_code == 200
    assert b"Progreso de Video Music" in response.content
    assert job_id.encode() in response.content
    assert b"Informaci\xc3\xb3n del trabajo" in response.content
    assert b"queued" in response.content


def test_job_progress_returns_404_for_unknown_job(request_factory):
    request = request_factory.get("/video-music/jobs/unknown/")

    with pytest.raises(Http404):
        JobProgressView.as_view()(request, job_id="unknown")