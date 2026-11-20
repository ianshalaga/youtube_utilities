from pathlib import Path
from typing import Iterable


class MediaDiscoveryService:
    """
    Descubre y ordena archivos multimedia dentro de un directorio.

    Realiza validaciones preventivas basadas en extensión de archivo.
    No garantiza compatibilidad multimedia real.
    """

    @staticmethod
    def discover(
        directory: Path,
        supported_extensions: Iterable[str]
    ) -> list[Path]:
        """
        Descubre y ordena archivos multimedia dentro de un directorio.

        Requiere padding numérico para un orden correcto.

        Args:
            directory:
                Directorio a inspeccionar.
            supported_extensions:
                Extensiones permitidas. Se aceptan con o sin punto inicial,
                y se normalizan ignorando mayúsculas y espacios externos.

        Returns:
            Lista ordenada de rutas válidas.
        """
        normalized_extensions = {
            extension.strip().lower().lstrip(".")
            for extension in supported_extensions
            if extension.strip().lstrip(".")
        }

        return sorted(
            p for p in directory.iterdir()
            if p.is_file()
            and p.suffix.lower().lstrip(".") in normalized_extensions
        )
