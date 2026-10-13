
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TrackProgress:
    index: int
    status: str = "pending"
    source_path: str | None = None
    name: str = ""
    output_dir: str | None = None
    output_path: str | None = None
    duration: str | None = None
    error_message: str | None = None
    message: str = "Pendiente"


@dataclass
class VideoMusicJobProgress:
    job_id: str
    status: str = "queued"
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    video_path: str = ""
    audios_dir: str = ""
    output_dir: str = ""
    max_items_per_dir: int = 0

    total_tracks: int = 0
    total_directories: int = 1
    current_directory: int = 1

    completed_tracks: int = 0
    failed_tracks: int = 0
    running_tracks: int = 0

    message: str = "Trabajo en espera"
    error_message: str | None = None
    tracks: list[TrackProgress] = field(default_factory=list)


class VideoMusicJobRegistry:
    """Thread-safe in-memory registry for Video Music jobs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._jobs: dict[str, VideoMusicJobProgress] = {}

    def create_job(
        self,
        *,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path,
        max_items_per_dir: int,
    ) -> str:
        job_id = uuid4().hex

        job = VideoMusicJobProgress(
            job_id=job_id,
            video_path=str(video_path),
            audios_dir=str(audios_dir),
            output_dir=str(output_dir),
            max_items_per_dir=max_items_per_dir,
        )

        with self._lock:
            self._jobs[job_id] = job

        return job_id

    def get_job(
        self,
        job_id: str,
    ) -> VideoMusicJobProgress | None:
        """Return a detached snapshot, never the mutable internal object."""
        with self._lock:
            job = self._jobs.get(job_id)
            return deepcopy(job) if job is not None else None

    def job_started(
        self,
        job_id: str,
        *,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path,
        total_tracks: int,
        max_items_per_dir: int | None,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)

            job.status = "running"
            job.video_path = str(video_path)
            job.audios_dir = str(audios_dir)
            job.output_dir = str(output_dir)
            job.total_tracks = total_tracks

            if max_items_per_dir is not None:
                job.max_items_per_dir = max_items_per_dir
                job.total_directories = max(
                    1,
                    (total_tracks + max_items_per_dir - 1)
                    // max_items_per_dir,
                )

            job.tracks = [
                TrackProgress(index=index)
                for index in range(1, total_tracks + 1)
            ]

            job.message = "Procesamiento iniciado"
            self._touch(job)

    def partition_started(
        self,
        job_id: str,
        *,
        total_tracks: int,
        max_items_per_dir: int,
        total_directories: int,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            job.total_tracks = total_tracks
            job.max_items_per_dir = max_items_per_dir
            job.total_directories = total_directories
            job.message = "Procesando pistas por directorios"
            self._touch(job)

    def processing_started(self, job_id: str) -> None:
        with self._lock:
            job = self._require_job(job_id)
            job.status = "running"
            job.message = "Procesando pistas"
            self._touch(job)

    def track_started(
        self,
        job_id: str,
        *,
        index: int,
        total: int,
        audio_path: Path,
        output_dir: Path,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            track = self._require_track(job, index)

            track.status = "running"
            track.source_path = str(audio_path)
            track.name = audio_path.stem
            track.output_dir = str(output_dir)
            track.message = "Procesando"
            job.total_tracks = total

            if job.max_items_per_dir > 0:
                job.current_directory = (
                    (index - 1) // job.max_items_per_dir
                ) + 1

            job.message = f"Procesando pista {index} de {total}"
            self._update_counts(job)
            self._touch(job)

    def record_activity(
        self,
        job_id: str,
        *,
        message: str,
        audio_path: Path | None = None,
        output_path: Path | None = None,
        duration: str | None = None,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            job.message = message

            if audio_path is not None:
                track = self._find_track(job, audio_path)

                if track is not None:
                    track.message = message

                    if output_path is not None:
                        track.output_path = str(output_path)

                    if duration is not None:
                        track.duration = duration

            self._touch(job)

    def track_completed(
        self,
        job_id: str,
        *,
        index: int,
        total: int,
        audio_path: Path,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            track = self._require_track(job, index)

            track.source_path = str(audio_path)
            track.name = audio_path.stem
            track.status = "completed"
            track.message = "Completada"

            job.total_tracks = total
            job.message = f"Pista {index} completada"
            self._update_counts(job)
            self._touch(job)

    def track_failed(
        self,
        job_id: str,
        *,
        index: int,
        total: int,
        audio_path: Path,
        error: Exception,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)
            track = self._require_track(job, index)

            track.source_path = str(audio_path)
            track.name = audio_path.stem
            track.status = "failed"
            track.error_message = str(error)
            track.message = "Fallida"

            job.total_tracks = total
            job.message = f"Falló la pista {index}"
            self._update_counts(job)
            self._touch(job)

    def job_completed(
        self,
        job_id: str,
        *,
        total_tracks: int,
        output_dir: Path,
    ) -> None:
        with self._lock:
            job = self._require_job(job_id)

            job.total_tracks = total_tracks
            job.output_dir = str(output_dir)
            job.status = "completed"
            job.message = "Procesamiento finalizado"

            self._update_counts(job)
            self._touch(job)

    def job_failed(self, job_id: str, error: Exception) -> None:
        """Record a job-level exception raised outside individual tracks."""
        with self._lock:
            job = self._require_job(job_id)
            job.status = "failed"
            job.error_message = str(error)
            job.message = "El procesamiento ha fallado"
            self._touch(job)

    def _require_job(self, job_id: str) -> VideoMusicJobProgress:
        job = self._jobs.get(job_id)

        if job is None:
            raise KeyError(f"Trabajo desconocido: {job_id}")

        return job

    @staticmethod
    def _require_track(
        job: VideoMusicJobProgress,
        index: int,
    ) -> TrackProgress:
        if index < 1 or index > len(job.tracks):
            raise IndexError(f"Índice de pista inválido: {index}")

        return job.tracks[index - 1]

    @staticmethod
    def _find_track(
        job: VideoMusicJobProgress,
        audio_path: Path,
    ) -> TrackProgress | None:
        for track in job.tracks:
            if track.source_path == str(audio_path):
                return track

        return None

    @staticmethod
    def _update_counts(job: VideoMusicJobProgress) -> None:
        job.completed_tracks = sum(
            track.status == "completed" for track in job.tracks
        )
        job.failed_tracks = sum(
            track.status == "failed" for track in job.tracks
        )
        job.running_tracks = sum(
            track.status == "running" for track in job.tracks
        )

    @staticmethod
    def _touch(job: VideoMusicJobProgress) -> None:
        job.updated_at = _now()
