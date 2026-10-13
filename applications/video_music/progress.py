
from pathlib import Path
from typing import Protocol


class VideoMusicProgressReporter(Protocol):
    """Contract for reporting Video Music processing progress."""

    def job_started(
        self,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path,
        total_tracks: int,
        max_items_per_dir: int | None,
    ) -> None: ...

    def partition_started(
        self,
        total_tracks: int,
        max_items_per_dir: int,
        total_directories: int,
    ) -> None: ...

    def processing_started(self) -> None: ...

    def track_started(
        self,
        index: int,
        total: int,
        audio_path: Path,
        output_dir: Path,
    ) -> None: ...

    def audio_converted(
        self,
        audio_path: Path,
        output_path: Path,
    ) -> None: ...

    def duration_detected(
        self,
        audio_path: Path,
        duration: str,
    ) -> None: ...

    def video_created(
        self,
        audio_path: Path,
        output_path: Path,
    ) -> None: ...

    def temporary_files_cleaned(
        self,
        audio_path: Path,
    ) -> None: ...

    def track_completed(
        self,
        index: int,
        total: int,
        audio_path: Path,
    ) -> None: ...

    def track_failed(
        self,
        index: int,
        total: int,
        audio_path: Path,
        error: Exception,
    ) -> None: ...

    def job_completed(
        self,
        total_tracks: int,
        output_dir: Path,
    ) -> None: ...
