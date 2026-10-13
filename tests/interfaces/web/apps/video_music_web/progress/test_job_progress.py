
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from interfaces.web.apps.video_music_web.progress.job_progress import (
    VideoMusicJobRegistry,
)


def create_job(registry, tmp_path, max_items_per_dir=2):
    return registry.create_job(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        max_items_per_dir=max_items_per_dir,
    )


def test_create_job_initializes_queued_state(tmp_path):
    registry = VideoMusicJobRegistry()

    job_id = create_job(registry, tmp_path)
    job = registry.get_job(job_id)

    assert job is not None
    assert job.job_id == job_id
    assert job.status == "queued"
    assert job.message == "Trabajo en espera"
    assert job.total_tracks == 0
    assert job.tracks == []


def test_job_started_initializes_tracks_and_directories(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id = create_job(registry, tmp_path, max_items_per_dir=2)

    registry.job_started(
        job_id,
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        total_tracks=5,
        max_items_per_dir=2,
    )

    job = registry.get_job(job_id)

    assert job is not None
    assert job.status == "running"
    assert job.total_tracks == 5
    assert job.total_directories == 3
    assert len(job.tracks) == 5
    assert all(track.status == "pending" for track in job.tracks)


def test_track_lifecycle_updates_counts_and_details(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id = create_job(registry, tmp_path)

    registry.job_started(
        job_id,
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        total_tracks=2,
        max_items_per_dir=2,
    )

    audio_path = tmp_path / "audio" / "01-theme.flac"
    output_path = tmp_path / "output" / "01-theme.mkv"

    registry.track_started(
        job_id,
        index=1,
        total=2,
        audio_path=audio_path,
        output_dir=tmp_path / "output",
    )

    job = registry.get_job(job_id)

    assert job is not None
    assert job.running_tracks == 1
    assert job.tracks[0].status == "running"
    assert job.tracks[0].name == "01-theme"

    registry.record_activity(
        job_id,
        message="Duración detectada: 03:25.000",
        audio_path=audio_path,
        duration="03:25.000",
    )
    registry.record_activity(
        job_id,
        message="Vídeo generado",
        audio_path=audio_path,
        output_path=output_path,
    )

    registry.track_completed(
        job_id,
        index=1,
        total=2,
        audio_path=audio_path,
    )

    registry.track_started(
        job_id,
        index=2,
        total=2,
        audio_path=tmp_path / "audio" / "02-theme.flac",
        output_dir=tmp_path / "output",
    )

    registry.track_failed(
        job_id,
        index=2,
        total=2,
        audio_path=tmp_path / "audio" / "02-theme.flac",
        error=RuntimeError("Error de prueba"),
    )

    job = registry.get_job(job_id)

    assert job is not None
    assert job.completed_tracks == 1
    assert job.failed_tracks == 1
    assert job.running_tracks == 0

    first_track = job.tracks[0]
    assert first_track.status == "completed"
    assert first_track.duration == "03:25.000"
    assert first_track.output_path == str(output_path)

    second_track = job.tracks[1]
    assert second_track.status == "failed"
    assert second_track.error_message == "Error de prueba"


def test_job_completed_preserves_failed_track_count(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id = create_job(registry, tmp_path)

    registry.job_started(
        job_id,
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        total_tracks=1,
        max_items_per_dir=2,
    )

    audio_path = tmp_path / "audio" / "theme.flac"

    registry.track_started(
        job_id,
        index=1,
        total=1,
        audio_path=audio_path,
        output_dir=tmp_path / "output",
    )
    registry.track_failed(
        job_id,
        index=1,
        total=1,
        audio_path=audio_path,
        error=RuntimeError("Falló una pista"),
    )
    registry.job_completed(
        job_id,
        total_tracks=1,
        output_dir=tmp_path / "output",
    )

    job = registry.get_job(job_id)

    assert job is not None
    assert job.status == "completed"
    assert job.completed_tracks == 0
    assert job.failed_tracks == 1


def test_job_level_failure_is_recorded(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id = create_job(registry, tmp_path)

    registry.job_failed(job_id, RuntimeError("Error global"))

    job = registry.get_job(job_id)

    assert job is not None
    assert job.status == "failed"
    assert job.error_message == "Error global"


def test_get_job_returns_detached_snapshot(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id = create_job(registry, tmp_path)

    snapshot = registry.get_job(job_id)

    assert snapshot is not None
    snapshot.message = "Modificación externa"

    stored_job = registry.get_job(job_id)

    assert stored_job is not None
    assert stored_job.message == "Trabajo en espera"


def test_unknown_job_raises_key_error():
    registry = VideoMusicJobRegistry()

    try:
        registry.processing_started("unknown")
    except KeyError as error:
        assert "unknown" in str(error)
    else:
        raise AssertionError("Se esperaba KeyError")


def test_concurrent_track_updates_keep_counts_consistent(tmp_path):
    registry = VideoMusicJobRegistry()
    job_id = create_job(registry, tmp_path, max_items_per_dir=5)
    total_tracks = 20

    registry.job_started(
        job_id,
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        total_tracks=total_tracks,
        max_items_per_dir=5,
    )

    def process_track(index):
        audio_path = tmp_path / "audio" / f"{index:02d}.flac"

        registry.track_started(
            job_id,
            index=index,
            total=total_tracks,
            audio_path=audio_path,
            output_dir=tmp_path / "output",
        )
        registry.track_completed(
            job_id,
            index=index,
            total=total_tracks,
            audio_path=audio_path,
        )

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(process_track, range(1, total_tracks + 1)))

    job = registry.get_job(job_id)

    assert job is not None
    assert job.completed_tracks == total_tracks
    assert job.failed_tracks == 0
    assert job.running_tracks == 0
    assert all(track.status == "completed" for track in job.tracks)
