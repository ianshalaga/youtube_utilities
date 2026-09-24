from __future__ import annotations

from pathlib import Path
from threading import Lock

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table


class VideoMusicConsole:
    """Console presentation for the Video Music workflow.

    The console keeps mutable job state and renders it through Rich Live,
    preventing concurrent worker threads from interleaving terminal output.
    """

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()
        self._lock = Lock()
        self._live: Live | None = None

        self._video_path: Path | None = None
        self._audios_dir: Path | None = None
        self._output_dir: Path | None = None
        self._total_tracks = 0
        self._max_items_per_dir: int | None = None
        self._total_directories = 1

        self._statuses: dict[int, str] = {}
        self._track_names: dict[int, str] = {}
        self._durations: dict[int, str] = {}
        self._errors: dict[int, str] = {}

        self._completed = 0
        self._failed = 0
        self._running = 0
        self._current_directory = 1

    def job_started(
        self,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path,
        total_tracks: int,
        max_items_per_dir: int | None,
    ) -> None:
        """Initialize the job state and display its context."""
        with self._lock:
            self._video_path = video_path
            self._audios_dir = audios_dir
            self._output_dir = output_dir
            self._total_tracks = total_tracks
            self._max_items_per_dir = max_items_per_dir

            if max_items_per_dir:
                self._total_directories = max(
                    1,
                    (total_tracks + max_items_per_dir - 1)
                    // max_items_per_dir,
                )
            else:
                self._total_directories = 1

            self._statuses.clear()
            self._track_names.clear()
            self._durations.clear()
            self._errors.clear()

            self._completed = 0
            self._failed = 0
            self._running = 0
            self._current_directory = 1

            self._render_static_header()

    def partition_started(
        self,
        total_tracks: int,
        max_items_per_dir: int,
        total_directories: int,
    ) -> None:
        """Update the partitioning information."""
        with self._lock:
            self._total_tracks = total_tracks
            self._max_items_per_dir = max_items_per_dir
            self._total_directories = total_directories

    def processing_started(self) -> None:
        """Start the live processing display."""
        with self._lock:
            if self._live is None:
                self._live = Live(
                    self._render(),
                    console=self._console,
                    refresh_per_second=8,
                    transient=False,
                )
                self._live.start(refresh=True)

    def track_started(
        self,
        index: int,
        total: int,
        audio_path: Path,
        output_dir: Path,
    ) -> None:
        """Mark a track as running."""
        with self._lock:
            self._total_tracks = total
            self._track_names[index] = audio_path.stem
            self._statuses[index] = "running"
            self._running += 1

            if self._max_items_per_dir:
                self._current_directory = (
                    (index - 1) // self._max_items_per_dir
                ) + 1

            self._refresh()

    def audio_converted(
        self,
        audio_path: Path,
        output_path: Path,
    ) -> None:
        """Record successful temporary audio conversion."""
        # Conversion is an internal processing step. Keep the public display
        # compact and update the live state only.
        return

    def duration_detected(
        self,
        audio_path: Path,
        duration: str,
    ) -> None:
        """Record the detected duration for the corresponding track."""
        with self._lock:
            for index, name in self._track_names.items():
                if name == audio_path.stem:
                    self._durations[index] = duration
                    break
            self._refresh()

    def video_created(
        self,
        audio_path: Path,
        output_path: Path,
    ) -> None:
        """Record successful video generation."""
        return

    def temporary_files_cleaned(
        self,
        audio_path: Path,
    ) -> None:
        """Record cleanup of temporary files."""
        return

    def track_completed(
        self,
        index: int,
        total: int,
        audio_path: Path,
    ) -> None:
        """Mark a track as successfully completed."""
        with self._lock:
            self._total_tracks = total
            self._track_names[index] = audio_path.stem
            self._statuses[index] = "completed"
            self._completed += 1
            self._running = max(0, self._running - 1)
            self._refresh()

    def track_failed(
        self,
        index: int,
        total: int,
        audio_path: Path,
        error: Exception,
    ) -> None:
        """Mark a track as failed."""
        with self._lock:
            self._total_tracks = total
            self._track_names[index] = audio_path.stem
            self._statuses[index] = "failed"
            self._errors[index] = str(error)
            self._failed += 1
            self._running = max(0, self._running - 1)
            self._refresh()

    def job_completed(
        self,
        total_tracks: int,
        output_dir: Path,
    ) -> None:
        """Stop live rendering and display the final summary."""
        with self._lock:
            self._total_tracks = total_tracks
            self._output_dir = output_dir
            self._completed = max(self._completed, total_tracks - self._failed)
            self._stop_live()
            self._console.print()
            self._console.print(
                Panel(
                    self._summary_table(),
                    title="[bold green]✓ JOB COMPLETED[/bold green]",
                    border_style="green",
                    expand=False,
                )
            )

    def job_failed(self, error: Exception) -> None:
        """Stop live rendering and display the job-level failure."""
        with self._lock:
            self._stop_live()
            self._console.print()
            self._console.print(
                Panel(
                    f"[red]{error}[/red]",
                    title="[bold red]✗ JOB FAILED[/bold red]",
                    border_style="red",
                    expand=False,
                )
            )

    def _render_static_header(self) -> None:
        """Render the non-live job context."""
        self._console.print()
        self._console.print(
            Panel(
                self._job_context_table(),
                title="[bold white]VIDEO MUSIC[/bold white]",
                border_style="blue",
                expand=False,
            )
        )
        self._console.print()

    def _job_context_table(self) -> Table:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()

        table.add_row("Video", str(self._video_path))
        table.add_row("Audio source", str(self._audios_dir))
        table.add_row("Output", str(self._output_dir))
        table.add_row("Tracks", str(self._total_tracks))

        partition = (
            "Disabled"
            if self._max_items_per_dir is None
            else f"{self._max_items_per_dir} tracks / directory"
        )
        table.add_row("Partition", partition)

        return table

    def _render(self) -> Group:
        progress = Progress(
            TextColumn("[bold]Progress[/bold]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("·"),
            TextColumn("{task.percentage:>5.1f}%"),
            expand=True,
        )
        progress.add_task(
            "tracks",
            total=self._total_tracks,
            completed=self._completed,
        )

        table = Table.grid(padding=(0, 1))
        table.add_column(width=4)
        table.add_column(width=8)
        table.add_column(ratio=1)
        table.add_column(width=12)

        visible = sorted(self._statuses.items())[-12:]

        for index, status in visible:
            name = self._track_names.get(index, "")
            duration = self._durations.get(index, "")

            if status == "completed":
                icon = "[green]✓[/green]"
                state = "[green]DONE[/green]"
            elif status == "failed":
                icon = "[red]✗[/red]"
                state = "[red]FAILED[/red]"
            else:
                icon = "[yellow]◐[/yellow]"
                state = "[yellow]RUNNING[/yellow]"

            table.add_row(
                icon,
                f"{index:03d}/{self._total_tracks:03d}",
                f"{name}",
                duration or state,
            )

        if not visible:
            table.add_row("", "", "[dim]Waiting for tracks...[/dim]", "")

        stats = (
            f"[bold]Running:[/bold] {self._running}    "
            f"[bold green]Completed:[/bold green] {self._completed}    "
            f"[bold red]Failed:[/bold red] {self._failed}"
        )

        directory = (
            f"Directory {self._current_directory}/{self._total_directories}"
        )

        return Group(
            f"[bold cyan]▶ PROCESSING TRACKS[/bold cyan]  [dim]{directory}[/dim]",
            progress,
            table,
            stats,
        )

    def _summary_table(self) -> Table:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()

        table.add_row("Tracks", str(self._total_tracks))
        table.add_row("Completed", str(self._completed))
        table.add_row("Failed", str(self._failed))
        table.add_row("Directories", str(self._total_directories))
        table.add_row("Output", str(self._output_dir))

        return table

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._render(), refresh=True)

    def _stop_live(self) -> None:
        if self._live is not None:
            self._live.update(self._render(), refresh=True)
            self._live.stop()
            self._live = None
