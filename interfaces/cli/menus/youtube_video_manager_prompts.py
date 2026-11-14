from datetime import datetime

import questionary
from questionary import Choice
from rich.console import Console

from domain.youtube.job import Job
from domain.youtube.publication_settings import PublicationSettings


class YouTubeVideoManagerPrompts:
    """Collect job-specific decisions from the CLI user."""

    def __init__(self, console: Console | None = None) -> None:
        self._console = console or Console()

    def ask_created_job_publication(
        self,
        job: Job,
    ) -> PublicationSettings | None:
        publication = job.publication
        if publication is None:
            self._console.print(
                "[bold red]Este job no tiene ajustes de publicación guardados.[/bold red]"
            )
            return None

        current_date = publication.first_publish_at.strftime(
            "%Y-%m-%d %H:%M"
        )
        self._console.print(
            f"Programación actual: [cyan]{current_date}[/cyan] · "
            f"cada [cyan]{publication.interval_days} días[/cyan] · "
            f"[cyan]{publication.timezone.key}[/cyan]"
        )
        action = questionary.select(
            "¿Qué quieres hacer con la programación?",
            choices=[
                Choice("Conservarla e iniciar el job", value="keep"),
                Choice("Actualizarla antes de iniciar", value="update"),
                Choice("Volver al menú", value="cancel"),
            ],
            use_arrow_keys=True,
            use_shortcuts=False,
        ).ask()

        if action in {None, "cancel"}:
            return None
        if action == "keep":
            return publication

        first_publish_at = self._ask_first_publish_at(current_date)
        if first_publish_at is None:
            return None

        interval_days = self._ask_interval_days(publication.interval_days)
        if interval_days is None:
            return None

        timezone = publication.timezone.key
        update_timezone = questionary.confirm(
            "¿Quieres actualizar también la timezone?",
            default=False,
        ).ask()
        if update_timezone is None:
            return None
        if update_timezone:
            timezone = self._ask_timezone(timezone)
            if timezone is None:
                return None

        try:
            return PublicationSettings(
                first_publish_at=first_publish_at,
                timezone=timezone,
                interval_days=interval_days,
            )
        except (TypeError, ValueError) as error:
            self._console.print(f"[red]{error}[/red]")
            return None

    def ask_failed_job_action(self) -> str | None:
        return questionary.select(
            "El job falló. ¿Qué quieres hacer?",
            choices=[
                Choice(
                    "Reintentar desde la operación fallida",
                    value="retry",
                ),
                Choice("Eliminar el job", value="delete"),
            ],
            use_arrow_keys=True,
            use_shortcuts=False,
        ).ask()

    def ask_running_job_action(self) -> str | None:
        return questionary.select(
            "El job quedó en estado RUNNING. ¿Qué quieres hacer?",
            choices=[
                Choice(
                    "Reanudar desde la operación interrumpida",
                    value="resume",
                ),
                Choice("Eliminar el job", value="delete"),
            ],
            use_arrow_keys=True,
            use_shortcuts=False,
        ).ask()

    def _ask_first_publish_at(self, default: str) -> datetime | None:
        while True:
            value = questionary.text(
                "Nueva first_publish_at (YYYY-MM-DD HH:MM)",
                default=default,
            ).ask()
            if value is None:
                return None
            try:
                parsed = datetime.strptime(value, "%Y-%m-%d %H:%M")
            except ValueError:
                self._console.print(
                    "[red]Formato no válido. Usa YYYY-MM-DD HH:MM.[/red]"
                )
                continue
            return parsed

    def _ask_interval_days(self, default: int) -> int | None:
        while True:
            value = questionary.text(
                "Nuevo interval_days",
                default=str(default),
            ).ask()
            if value is None:
                return None
            try:
                interval_days = int(value)
            except ValueError:
                interval_days = 0
            if interval_days > 0:
                return interval_days
            self._console.print(
                "[red]interval_days debe ser un entero mayor que cero.[/red]"
            )

    def _ask_timezone(self, default: str) -> str | None:
        while True:
            timezone = questionary.text(
                "Nueva timezone IANA",
                default=default,
            ).ask()
            if timezone is None:
                return None
            try:
                PublicationSettings(
                    first_publish_at=datetime(2000, 1, 1),
                    timezone=timezone,
                    interval_days=1,
                )
            except (TypeError, ValueError) as error:
                self._console.print(f"[red]{error}[/red]")
                continue
            return timezone
