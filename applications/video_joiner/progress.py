from pathlib import Path
from typing import Protocol


class VideoJoinerProgressReporter(Protocol):
    """Contract for reporting Video Joiner processing progress."""

    def job_started(
        self,
        videos_dir: Path,
        output_dir: Path,
        total_videos: int,
        total_parts: int,
        target_duration: float | None,
    ) -> None: ...

    def part_started(
        self,
        index: int,
        total_parts: int,
        videos: list[Path],
        output_path: Path,
    ) -> None: ...

    def part_completed(
        self,
        index: int,
        total_parts: int,
        output_path: Path,
        timestamps_path: Path,
    ) -> None: ...

    def part_failed(
        self,
        index: int,
        total_parts: int,
        output_path: Path,
        error: Exception,
    ) -> None: ...

    def job_completed(self, total_parts: int, output_dir: Path) -> None: ...

    def job_failed(self, error: Exception) -> None: ...
