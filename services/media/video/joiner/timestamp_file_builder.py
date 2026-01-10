"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- Los timestamps se generan acumulando duraciones en orden.
- El tiempo siempre comienza en 00:00:00 por cada archivo.
- La duración se obtiene vía MediaProvider.
- El nombre del video se toma desde Path.stem.
- El padding numérico se calcula dinámicamente.
- El archivo resultante es compatible con timestamps de YouTube.
"""

from pathlib import Path
from typing import Iterable

from services.media.media_provider import MediaProvider
from core.time_utils import seconds_to_youtube_timestamp


class TimestampFileBuilder:
    """
    Construye un archivo de texto con timestamps para YouTube
    a partir de una lista ordenada de videos.
    """

    def __init__(self, media_provider: MediaProvider):
        self.media_provider = media_provider

    def build(
        self,
        *,
        videos: Iterable[Path],
        output_path: Path,
        prefix: str = "",
        secuence: bool = True,
        extra_description: str | None = None
    ) -> None:
        """
        Genera un archivo de timestamps.

        Args:
            videos:
                Lista ordenada de videos (incluye end screen si aplica).
            output_path:
                Ruta del archivo .txt a generar.
            prefix:
                Texto a anteponer a cada línea (opcional).
            extra_description:
                Texto adicional al final del archivo.
        """
        videos = list(videos)

        if not videos:
            raise ValueError("No hay videos para generar timestamps.")

        durations = [
            self.media_provider.duration(video)
            for video in videos
        ]

        total_duration = sum(durations)
        use_hours = total_duration >= 3600

        lines: list[str] = []

        current_time = 0.0
        padding = len(str(len(videos)))

        for index, (video, duration) in enumerate(zip(videos, durations), start=1):
            timestamp = seconds_to_youtube_timestamp(
                current_time, use_hours=use_hours)

            number = f"{index:0{padding}d}"
            name = video.stem

            # Construcción de la línea
            if secuence:
                line = f"{timestamp} {prefix}{number} {name}".strip()
            else:
                line = f"{timestamp} {name}".strip()
            lines.append(line)

            current_time += duration

        # Separación visual antes del texto adicional
        if extra_description:
            lines.append("")
            lines.append(extra_description.strip())

        output_path.write_text(
            "\n".join(lines),
            encoding="utf-8"
        )
