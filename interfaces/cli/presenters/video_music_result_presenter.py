"""Present the final result of a Video Music execution in the CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from applications.video_music.output import (
    TrackStatus,
    VideoMusicResult,
)


class VideoMusicResultPresenter:
    """Render a VideoMusicResult for terminal users."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def display(self, result: VideoMusicResult) -> None:
        """Display the execution summary and per-track results."""
        summary = Table.grid(padding=(0, 2))
        summary.add_column(style="bold")
        summary.add_column()

        summary.add_row("Output directory", str(result.output_dir))
        summary.add_row("Total tracks", str(result.total_tracks))
        summary.add_row("Processed tracks", str(result.processed_tracks))
        summary.add_row("Failed tracks", str(result.failed_tracks))
        summary.add_row("Output directories", str(result.total_directories))

        self._console.print()
        self._console.print(
            Panel(
                summary,
                title="Video Music — Execution Summary",
                expand=False,
            )
        )

        if not result.tracks:
            self._console.print("No track details are available.")
            return

        tracks_table = Table(title="Track Details", expand=True)
        tracks_table.add_column("#", justify="right", style="dim", no_wrap=True)
        tracks_table.add_column("Track", min_width=18)
        tracks_table.add_column("Status", no_wrap=True)
        tracks_table.add_column("Duration", justify="right", no_wrap=True)
        tracks_table.add_column("Output", overflow="fold")
        tracks_table.add_column("Error", overflow="fold")

        for index, track in enumerate(result.tracks, start=1):
            if track.status is TrackStatus.COMPLETED:
                status_label = "[green]COMPLETED[/green]"
            elif track.status is TrackStatus.FAILED:
                status_label = "[red]FAILED[/red]"
            else:
                status_label = str(track.status.value)

            duration = (
                f"{track.duration_seconds:.2f} s"
                if track.duration_seconds is not None
                else "—"
            )
            output_path = str(track.output_path) if track.output_path else "—"
            error_message = track.error_message or "—"

            tracks_table.add_row(
                str(index),
                track.source_path.name,
                status_label,
                duration,
                output_path,
                error_message,
            )

        self._console.print(tracks_table)
