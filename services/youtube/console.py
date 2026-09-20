from __future__ import annotations

from rich.console import Console

from domain.youtube.video import Video


class YouTubeConsole:
    """Console presentation for the YouTube Video Manager workflow."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def new_job(self) -> None:
        """Report that a new Job has been created for execution."""
        self._console.print(
            "▶ [bold green]NEW JOB[/bold green]"
        )
        self._console.print()

    def existing_job(self) -> None:
        """Report that an existing pending Job is being resumed."""
        self._console.print(
            "↻ [bold cyan]EXISTING JOB · RESUMING[/bold cyan]"
        )
        self._console.print()

    def retrying_job(self) -> None:
        """Report that a failed Job is being retried."""
        self._console.print(
            "↻ [bold yellow]FAILED JOB · RETRYING[/bold yellow]"
        )
        self._console.print()

    def video_started(self, video: Video, index: int, total: int) -> None:
        """Display the video context before its operations are executed."""
        self._console.print(
            f"▶ [bold white]VIDEO {index:02d}/{total:02d}[/bold white]"
        )
        self._console.print(f"  [bold]{video.metadata.title}[/bold]")
        self._console.print(f"  ID: [dim]{video.video_id}[/dim]")
        self._console.print()

    def job_completed(self) -> None:
        """Report successful Job completion."""
        self._console.print()
        self._console.print(
            "✓ [bold green]JOB COMPLETED[/bold green]"
        )

    def job_quota_exceeded(self) -> None:
        """Report that execution stopped because the YouTube quota was exhausted."""
        self._console.print()
        self._console.print(
            "⚠ [bold yellow]YOUTUBE QUOTA EXCEEDED · JOB PAUSED[/bold yellow]"
        )

    def job_failed(self) -> None:
        """Report that the Job failed permanently."""
        self._console.print()
        self._console.print(
            "✗ [bold red]JOB FAILED[/bold red]"
        )
