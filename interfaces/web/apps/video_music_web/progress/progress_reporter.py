from pathlib import Path

from applications.video_music.progress import VideoMusicProgressReporter

from .job_progress import VideoMusicJobRegistry


class WebVideoMusicProgressReporter(VideoMusicProgressReporter):
    """Adapt Video Music progress events to the web job registry."""

    def __init__(
        self,
        *,
        job_id: str,
        registry: VideoMusicJobRegistry,
    ) -> None:
        self._job_id = job_id
        self._registry = registry

    def job_started(
        self,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path,
        total_tracks: int,
        max_items_per_dir: int | None,
    ) -> None:
        self._registry.job_started(
            self._job_id,
            video_path=video_path,
            audios_dir=audios_dir,
            output_dir=output_dir,
            total_tracks=total_tracks,
            max_items_per_dir=max_items_per_dir,
        )

    def partition_started(
        self,
        total_tracks: int,
        max_items_per_dir: int,
        total_directories: int,
    ) -> None:
        self._registry.partition_started(
            self._job_id,
            total_tracks=total_tracks,
            max_items_per_dir=max_items_per_dir,
            total_directories=total_directories,
        )

    def processing_started(self) -> None:
        self._registry.processing_started(self._job_id)

    def track_started(
        self,
        index: int,
        total: int,
        audio_path: Path,
        output_dir: Path,
    ) -> None:
        self._registry.track_started(
            self._job_id,
            index=index,
            total=total,
            audio_path=audio_path,
            output_dir=output_dir,
        )

    def audio_converted(
        self,
        audio_path: Path,
        output_path: Path,
    ) -> None:
        self._registry.record_activity(
            self._job_id,
            message="Audio convertido",
            audio_path=audio_path,
        )

    def duration_detected(
        self,
        audio_path: Path,
        duration: str,
    ) -> None:
        self._registry.record_activity(
            self._job_id,
            message=f"Duración detectada: {duration}",
            audio_path=audio_path,
            duration=duration,
        )

    def video_created(
        self,
        audio_path: Path,
        output_path: Path,
    ) -> None:
        self._registry.record_activity(
            self._job_id,
            message="Vídeo generado",
            audio_path=audio_path,
            output_path=output_path,
        )

    def temporary_files_cleaned(self, audio_path: Path) -> None:
        self._registry.record_activity(
            self._job_id,
            message="Archivos temporales eliminados",
            audio_path=audio_path,
        )

    def track_completed(
        self,
        index: int,
        total: int,
        audio_path: Path,
    ) -> None:
        self._registry.track_completed(
            self._job_id,
            index=index,
            total=total,
            audio_path=audio_path,
        )

    def track_failed(
        self,
        index: int,
        total: int,
        audio_path: Path,
        error: Exception,
    ) -> None:
        self._registry.track_failed(
            self._job_id,
            index=index,
            total=total,
            audio_path=audio_path,
            error=error,
        )

    def job_completed(
        self,
        total_tracks: int,
        output_dir: Path,
    ) -> None:
        self._registry.job_completed(
            self._job_id,
            total_tracks=total_tracks,
            output_dir=output_dir,
        )

    def job_failed(self, error: Exception) -> None:
        self._registry.job_failed(self._job_id, error)
