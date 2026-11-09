from pathlib import Path
from threading import Lock

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich.table import Table


class VideoJoinerConsole:
    """Rich presentation for Video Joiner processing events."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()
        self._lock = Lock()
        self._live: Live | None = None
        self._videos_dir: Path | None = None
        self._output_dir: Path | None = None
        self._target_duration: float | None = None
        self._total_videos = 0
        self._total_parts = 0
        self._completed = 0
        self._failed = 0
        self._parts: dict[int, dict[str, str]] = {}

    def job_started(
        self,
        videos_dir: Path,
        output_dir: Path,
        total_videos: int,
        total_parts: int,
        target_duration: float | None,
    ) -> None:
        with self._lock:
            self._videos_dir = videos_dir
            self._output_dir = output_dir
            self._target_duration = target_duration
            self._total_videos = total_videos
            self._total_parts = total_parts
            self._completed = 0
            self._failed = 0
            self._parts = {
                index: {"status": "Pendiente", "videos": "", "error": ""}
                for index in range(1, total_parts + 1)
            }
            self._render_header()
            self._live = Live(
                self._render(),
                console=self._console,
                refresh_per_second=8,
                transient=False,
            )
            self._live.start(refresh=True)

    def part_started(
        self,
        index: int,
        total_parts: int,
        videos: list[Path],
        output_path: Path,
    ) -> None:
        with self._lock:
            self._total_parts = total_parts
            self._parts[index] = {
                "status": "En proceso",
                "videos": ", ".join(video.name for video in videos),
                "output": str(output_path),
                "error": "",
            }
            self._refresh()

    def part_completed(
        self,
        index: int,
        total_parts: int,
        output_path: Path,
        timestamps_path: Path,
    ) -> None:
        with self._lock:
            self._parts[index].update(
                status="Completada",
                output=str(output_path),
                timestamps=str(timestamps_path),
            )
            self._completed += 1
            self._refresh()

    def part_failed(
        self,
        index: int,
        total_parts: int,
        output_path: Path,
        error: Exception,
    ) -> None:
        with self._lock:
            part = self._parts.setdefault(index, {})
            part.update(
                status="Fallida",
                output=str(output_path),
                error=str(error),
            )
            self._failed += 1
            self._refresh()

    def job_completed(self, total_parts: int, output_dir: Path) -> None:
        with self._lock:
            self._total_parts = total_parts
            self._output_dir = output_dir
            self._completed = max(self._completed, total_parts - self._failed)
            self._stop_live()
            self._console.print()
            self._console.print(
                Panel(
                    self._summary_table(),
                    title="[bold green]✓ PROCESAMIENTO COMPLETADO[/bold green]",
                    border_style="green",
                    expand=False,
                )
            )

    def job_failed(self, error: Exception) -> None:
        with self._lock:
            self._stop_live()
            self._console.print()
            self._console.print(
                Panel(
                    Text(str(error), style="red"),
                    title="[bold red]✗ PROCESAMIENTO FALLIDO[/bold red]",
                    border_style="red",
                    expand=False,
                )
            )

    def _render_header(self) -> None:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()
        table.add_row("Vídeos", Text(str(self._videos_dir)))
        table.add_row("Salida", Text(str(self._output_dir)))
        table.add_row("Archivos detectados", str(self._total_videos))
        table.add_row("Partes previstas", str(self._total_parts))
        table.add_row(
            "Duración objetivo",
            "Sin particionar" if self._target_duration is None
            else f"{self._target_duration:g} s",
        )
        self._console.print()
        self._console.print(
            Panel(
                table,
                title="[bold white]VIDEO JOINER[/bold white]",
                border_style="blue",
                expand=False,
            )
        )

    def _render(self) -> Group:
        progress = Progress(
            TextColumn("[bold]Partes[/bold]"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TextColumn("·"),
            TextColumn("{task.percentage:>5.1f}%"),
            expand=True,
        )
        progress.add_task(
            "parts",
            total=self._total_parts,
            completed=self._completed + self._failed,
        )

        table = Table(expand=True)
        table.add_column("#", width=5, justify="right")
        table.add_column("Estado", width=14)
        table.add_column("Vídeos", ratio=2)
        table.add_column("Salida", ratio=2)
        table.add_column("Detalle", ratio=2)

        for index, part in sorted(self._parts.items()):
            status = part.get("status", "Pendiente")
            style = {
                "Completada": "green",
                "Fallida": "red",
                "En proceso": "yellow",
            }.get(status, "dim")
            detail = part.get("error") or part.get("timestamps", "")
            table.add_row(
                str(index),
                f"[{style}]{status}[/{style}]",
                Text(part.get("videos", "")),
                Text(part.get("output", "")),
                Text(detail),
            )

        return Group(
            "[bold cyan]▶ UNIENDO VÍDEOS[/bold cyan]",
            progress,
            table,
            f"[green]Completadas: {self._completed}[/green]    "
            f"[red]Fallidas: {self._failed}[/red]",
        )

    def _summary_table(self) -> Table:
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bold")
        table.add_column()
        table.add_row("Partes completadas", str(self._completed))
        table.add_row("Partes fallidas", str(self._failed))
        table.add_row("Directorio de salida", Text(str(self._output_dir)))
        for index, part in sorted(self._parts.items()):
            if part.get("status") == "Completada":
                table.add_row(f"Parte {index}", Text(part.get("output", "")))
                table.add_row(
                    "Marcas de tiempo",
                    Text(part.get("timestamps", "")),
                )
        return table

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._render(), refresh=True)

    def _stop_live(self) -> None:
        if self._live is not None:
            self._live.update(self._render(), refresh=True)
            self._live.stop()
            self._live = None
