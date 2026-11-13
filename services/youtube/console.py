from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    def videos_missing_from_uploads(self, titles: tuple[str, ...]) -> None:
        table = Table(title="Videos missing from the uploads playlist")
        table.add_column("#", style="dim", justify="right")
        table.add_column("Manifest title", style="yellow")
        for index, title in enumerate(titles, start=1):
            table.add_row(str(index), title)
        self._console.print(table)

    def video_id_fallback_started(self, path: Path) -> None:
        self._console.print(
            Panel(
                f"Checking the configured video ID overrides file:\n[cyan]{path}[/cyan]",
                title="Trying ID fallback",
                border_style="cyan",
            )
        )

    def video_id_fallback_resolved(self, titles: tuple[str, ...]) -> None:
        if not titles:
            return
        table = Table(title="Videos resolved by ID")
        table.add_column("Manifest title", style="green")
        for title in titles:
            table.add_row(title)
        self._console.print(table)

    def video_id_fallback_error(self, message: str) -> None:
        self._console.print(
            Panel(
                message,
                title="Invalid video ID overrides",
                border_style="red",
            )
        )

    def video_id_fallback_failed(
        self,
        titles: tuple[str, ...],
        path: Path,
    ) -> None:
        table = Table(title="Videos still unresolved", border_style="red")
        table.add_column("Manifest title", style="red")
        for title in titles:
            table.add_row(title)
        self._console.print(table)
        self._console.print(
            f"[yellow]Add each title and its YouTube ID to [bold]{path}[/bold], "
            "or upload the missing videos, then run the app again.[/yellow]"
        )

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

    def thumbnail_rate_limit_deferred(self, video: Video) -> None:
        self._console.print(
            "⚠ [bold yellow]THUMBNAIL RATE LIMIT · OPERATION DEFERRED[/bold yellow]"
        )
        self._console.print(f"  [bold]{video.metadata.title}[/bold]")
        self._console.print(f"  ID: [dim]{video.video_id}[/dim]")

    def job_operations_deferred(self, count: int) -> None:
        label = "operation" if count == 1 else "operations"
        self._console.print(
            f"↻ [bold yellow]JOB PENDING · {count} thumbnail {label} deferred[/bold yellow]"
        )

    def job_failed(self) -> None:
        """Report that the Job failed permanently."""
        self._console.print()
        self._console.print(
            "✗ [bold red]JOB FAILED[/bold red]"
        )
