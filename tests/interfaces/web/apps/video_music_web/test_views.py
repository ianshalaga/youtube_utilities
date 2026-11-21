
import pytest
from unittest.mock import patch
import json

from django.http import Http404
from django.test import RequestFactory

from interfaces.web.apps.video_music_web.progress.job_progress import (
    ActiveVideoMusicJobError,
    VideoMusicJobRegistry,
)
from interfaces.web.apps.video_music_web.progress.job_runner import (
    run_video_music_job,
)
from interfaces.web.apps.video_music_web.views import (
    IndexView,
    JobProgressView,
    JobResultView,
    JobStatusView,
)


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def isolated_registry(monkeypatch):
    registry = VideoMusicJobRegistry()
    monkeypatch.setattr(
        "interfaces.web.apps.video_music_web.views.job_registry",
        registry,
    )
    return registry


def test_job_status_returns_json(request_factory, tmp_path, isolated_registry):
    job_id = isolated_registry.create_job(
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


@patch("interfaces.web.apps.video_music_web.views.ConfigManager")
def test_index_form_submits_in_the_current_tab(
    config_manager_class,
    request_factory,
):
    request = request_factory.get("/video-music/")

    response = IndexView.as_view()(request)

    assert response.status_code == 200
    assert b'<form method="post"' in response.content
    assert b'target="_self"' in response.content
    assert b'data-file-picker-container="audios_dir"' in response.content
    assert b'data-file-picker-container="video_path"' in response.content
    assert b"file_picker.js?v=2" in response.content
    assert "🎬 Generar vídeos".encode() in response.content
    assert b"Guardar valores predeterminados" not in response.content


@patch("interfaces.web.apps.video_music_web.views.Thread")
@patch("interfaces.web.apps.video_music_web.views.job_registry")
@patch("interfaces.web.apps.video_music_web.views.ConfigManager")
def test_index_post_starts_background_job(
    config_manager_class,
    registry,
    thread_class,
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


@patch("interfaces.web.apps.video_music_web.views.Thread")
@patch("interfaces.web.apps.video_music_web.views.job_registry")
@patch("interfaces.web.apps.video_music_web.views.ConfigManager")
def test_index_post_rejects_submission_while_another_job_is_active(
    config_manager_class,
    registry,
    thread_class,
    request_factory,
    tmp_path,
):
    audios_dir = tmp_path / "audio"
    audios_dir.mkdir()
    video_path = tmp_path / "base.mkv"
    video_path.touch()
    registry.create_job.side_effect = ActiveVideoMusicJobError("job-active")

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

    assert response.status_code == 200
    assert b"Ya hay un trabajo activo" in response.content
    assert b"job-active" in response.content
    config_manager_class.return_value.update_video_music_defaults.assert_not_called()
    thread_class.assert_not_called()


def test_job_progress_returns_page_for_existing_job(
    request_factory,
    tmp_path,
    isolated_registry,
):
    job_id = isolated_registry.create_job(
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
    assert "⏳ En espera".encode() in response.content
    assert b"queued" not in response.content
    assert (
        f'data-result-url="/video-music/jobs/{job_id}/results/"'.encode()
        in response.content
    )
    assert b"job_progress.js?v=2" in response.content
    assert b"Volver a Video Music" not in response.content
    assert b'href="/"' not in response.content


def test_job_progress_localizes_track_states_and_places_completed_last(
    request_factory,
    tmp_path,
    isolated_registry,
):
    job_id = isolated_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=5,
    )
    isolated_registry.job_started(
        job_id,
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        audio_files=[
            tmp_path / "audio" / "01-active.flac",
            tmp_path / "audio" / "02-completed.flac",
            tmp_path / "audio" / "03-failed.flac",
        ],
        total_tracks=3,
        max_items_per_dir=5,
    )

    active_audio = tmp_path / "audio" / "01-active.flac"
    completed_audio = tmp_path / "audio" / "02-completed.flac"
    failed_audio = tmp_path / "audio" / "03-failed.flac"

    isolated_registry.track_started(
        job_id,
        index=1,
        total=3,
        audio_path=active_audio,
        output_dir=tmp_path / "output",
    )
    isolated_registry.track_started(
        job_id,
        index=2,
        total=3,
        audio_path=completed_audio,
        output_dir=tmp_path / "output",
    )
    isolated_registry.track_completed(
        job_id,
        index=2,
        total=3,
        audio_path=completed_audio,
    )
    isolated_registry.track_started(
        job_id,
        index=3,
        total=3,
        audio_path=failed_audio,
        output_dir=tmp_path / "output",
    )
    isolated_registry.track_failed(
        job_id,
        index=3,
        total=3,
        audio_path=failed_audio,
        error=RuntimeError("Error de prueba"),
    )

    request = request_factory.get(f"/video-music/jobs/{job_id}/")
    response = JobProgressView.as_view()(request, job_id=job_id)
    content = response.content

    assert content.index(b"01-active") < content.index(b"03-failed")
    assert content.index(b"03-failed") < content.index(b"02-completed")
    assert b"|</span>" in content
    assert "🔄 En procesamiento".encode() in content
    assert "✅ Completada".encode() in content
    assert "❌ Fallida".encode() in content


def test_job_failure_preserves_multiline_validation_details(
    request_factory,
    tmp_path,
    isolated_registry,
):
    job_id = isolated_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=10,
    )
    isolated_registry.job_failed(
        job_id,
        ValueError(
            "La validación de duración ha fallado:\n"
            "- tema-01.flac: audio 12.5 s > vídeo base 10.0 s\n"
            "- tema-02.flac: audio 14.0 s > vídeo base 10.0 s"
        ),
    )

    request = request_factory.get(
        f"/video-music/jobs/{job_id}/results/"
    )
    response = JobResultView.as_view()(request, job_id=job_id)

    assert response.status_code == 200
    assert b"whitespace-pre-wrap break-words" in response.content
    assert (
        "tema-01.flac: audio 12.5 s &gt; vídeo base 10.0 s".encode()
        in response.content
    )
    assert (
        "tema-02.flac: audio 14.0 s &gt; vídeo base 10.0 s".encode()
        in response.content
    )


def test_job_progress_returns_404_for_unknown_job(request_factory):
    request = request_factory.get("/video-music/jobs/unknown/")

    with pytest.raises(Http404):
        JobProgressView.as_view()(request, job_id="unknown")


@patch("interfaces.web.apps.video_music_web.views.ConfigManager")
def test_index_does_not_render_job_results(
    config_manager_class,
    request_factory,
    tmp_path,
    isolated_registry,
):
    job_id = isolated_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=10,
    )
    isolated_registry.job_completed(
        job_id,
        total_tracks=0,
        output_dir=tmp_path / "output",
    )

    request = request_factory.get(f"/video-music/?job_id={job_id}")

    response = IndexView.as_view()(request)

    assert response.status_code == 200
    assert b"Resultado del procesamiento" not in response.content
    assert b"job-results" not in response.content


@patch("interfaces.web.apps.video_music_web.views.ConfigManager")
def test_job_result_returns_page_for_completed_job(
    config_manager_class,
    request_factory,
    tmp_path,
    isolated_registry,
):
    job_id = isolated_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=10,
    )
    audio_path = tmp_path / "audio" / "01-theme.flac"
    isolated_registry.job_started(
        job_id,
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        audio_files=[tmp_path / "audio" / "01-theme.flac"],
        total_tracks=1,
        max_items_per_dir=10,
    )
    isolated_registry.track_started(
        job_id,
        index=1,
        total=1,
        audio_path=audio_path,
        output_dir=tmp_path / "output",
    )
    isolated_registry.track_completed(
        job_id,
        index=1,
        total=1,
        audio_path=audio_path,
    )
    isolated_registry.job_completed(
        job_id,
        total_tracks=1,
        output_dir=tmp_path / "output",
    )

    request = request_factory.get(
        f"/video-music/jobs/{job_id}/results/"
    )
    response = JobResultView.as_view()(request, job_id=job_id)

    assert response.status_code == 200
    assert b"Resultados de Video Music" in response.content
    assert "✅ Completada".encode() in response.content
    assert b"completed" not in response.content
    assert b"Volver a Video Music" in response.content
    assert b"video-music-form" not in response.content
    assert (
        response.content.index(b"Volver a Video Music")
        < response.content.index(b"Detalle de las pistas")
    )


def test_job_result_redirects_to_progress_while_job_is_active(
    request_factory,
    tmp_path,
    isolated_registry,
):
    job_id = isolated_registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=10,
    )

    request = request_factory.get(
        f"/video-music/jobs/{job_id}/results/"
    )
    response = JobResultView.as_view()(request, job_id=job_id)

    assert response.status_code == 302
    assert response.url == f"/video-music/jobs/{job_id}/"


def test_job_result_returns_404_for_unknown_job(request_factory):
    request = request_factory.get(
        "/video-music/jobs/unknown/results/"
    )

    with pytest.raises(Http404):
        JobResultView.as_view()(request, job_id="unknown")
