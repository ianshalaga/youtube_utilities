from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

import questionary
from questionary import Choice
from rich.console import Console
from rich.table import Table
from rich.text import Text

from domain.youtube.job import Job, JobStatus
from domain.youtube.operation import OperationStatus, OperationType


class MenuAction(Enum):
    CREATE_JOB = "create_job"
    SELECT_JOB = "select_job"
    EXIT = "exit"


@dataclass(frozen=True)
class MenuSelection:
    action: MenuAction
    job_id: int | None = None


class YouTubeVideoManagerMenu:
    """Present selectable YouTube jobs and collect a keyboard selection."""

    _STATUS_ORDER = (
        JobStatus.CREATED,
        JobStatus.PENDING,
        JobStatus.FAILED,
        JobStatus.RUNNING,
    )
    _STATUS_STYLES = {
        JobStatus.CREATED: "cyan",
        JobStatus.PENDING: "yellow",
        JobStatus.FAILED: "red",
        JobStatus.RUNNING: "blue",
    }
    _OPERATION_ORDER = (
        OperationType.UPDATE_METADATA,
        OperationType.SET_THUMBNAIL,
        OperationType.ADD_TO_PLAYLIST,
    )
    _OPERATION_LABELS = {
        OperationType.UPDATE_METADATA: "Metadatos",
        OperationType.SET_THUMBNAIL: "Miniaturas",
        OperationType.ADD_TO_PLAYLIST: "Playlists",
    }
    _OPERATION_STATUS_ORDER = (
        OperationStatus.PENDING,
        OperationStatus.RUNNING,
        OperationStatus.FAILED,
        OperationStatus.COMPLETED,
    )
    _OPERATION_STATUS_SHORT = {
        OperationStatus.PENDING: ("P", "white"),
        OperationStatus.RUNNING: ("R", "blue"),
        OperationStatus.FAILED: ("F", "red"),
        OperationStatus.COMPLETED: ("C", "green"),
    }

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def select(self, jobs: Sequence[Job]) -> MenuSelection | None:
        """Print grouped job summaries and return the chosen menu item."""
        active_jobs = self._sorted_jobs(jobs)
        self._display_jobs(active_jobs)

        choices = [
            Choice(
                title="Crear un nuevo job desde el manifiesto",
                value=MenuSelection(MenuAction.CREATE_JOB),
            )
        ]
        choices.extend(
            Choice(
                title=self._job_choice_title(job),
                value=MenuSelection(MenuAction.SELECT_JOB, job.id),
            )
            for job in active_jobs
        )
        choices.append(
            Choice(
                title="Salir",
                value=MenuSelection(MenuAction.EXIT),
            )
        )

        return questionary.select(
            "Selecciona una acción o un job:",
            choices=choices,
            use_arrow_keys=True,
            use_shortcuts=False,
        ).ask()

    def _display_jobs(self, jobs: Sequence[Job]) -> None:
        if not jobs:
            self._console.print("No hay jobs activos.", style="dim")
            return

        self._console.print(
            "Operaciones: [white]P[/white]=pendientes · "
            "[blue]R[/blue]=en ejecución · [red]F[/red]=fallidas · "
            "[green]C[/green]=completadas",
            style="dim",
        )

        for status in self._STATUS_ORDER:
            status_jobs = [job for job in jobs if job.status is status]
            if not status_jobs:
                continue

            table = Table(
                title=Text(
                    f"[{status.value.upper()}] Jobs",
                    style=self._STATUS_STYLES[status],
                ),
                expand=True,
            )
            table.add_column("Job", min_width=24)
            for operation_type in self._OPERATION_ORDER:
                table.add_column(
                    self._OPERATION_LABELS[operation_type],
                    justify="center",
                )
            table.add_column("Total", justify="center")

            for job in sorted(status_jobs, key=lambda item: item.id or 0):
                counts = self._operation_counts(job)
                table.add_row(
                    self._job_label(job),
                    *(
                        self._format_counts(counts[operation_type])
                        for operation_type in self._OPERATION_ORDER
                    ),
                    self._format_counts(
                        Counter(
                            operation.status for operation in job.operations
                        )
                    ),
                )

            self._console.print(table)

    @classmethod
    def _operation_counts(
        cls,
        job: Job,
    ) -> dict[OperationType, Counter[OperationStatus]]:
        counts = {
            operation_type: Counter()
            for operation_type in cls._OPERATION_ORDER
        }
        for operation in job.operations:
            counts[operation.operation_type][operation.status] += 1
        return counts

    @classmethod
    def _format_counts(
        cls,
        counts: Counter[OperationStatus],
    ) -> Text:
        result = Text()
        for index, status in enumerate(cls._OPERATION_STATUS_ORDER):
            if index:
                result.append("  ")
            label, style = cls._OPERATION_STATUS_SHORT[status]
            result.append(f"{label}:{counts[status]}", style=style)
        return result

    @classmethod
    def _job_label(cls, job: Job) -> Text:
        label = Text()
        label.append(
            f"[{job.status.value.upper()}] ",
            style=cls._STATUS_STYLES[job.status],
        )
        label.append(job.name or "(sin nombre)")
        label.append(f"  ·  #{job.id if job.id is not None else '?'}", style="dim")
        return label

    @classmethod
    def _job_choice_title(cls, job: Job) -> str:
        name = job.name or "(sin nombre)"
        job_id = job.id if job.id is not None else "?"
        return f"{job.status.value.upper()} · {name} · #{job_id}"

    @classmethod
    def _sorted_jobs(cls, jobs: Sequence[Job]) -> list[Job]:
        status_order = {
            status: index
            for index, status in enumerate(cls._STATUS_ORDER)
        }
        return sorted(
            (job for job in jobs if job.status in status_order),
            key=lambda job: (
                status_order[job.status],
                job.id or 0,
            ),
        )
