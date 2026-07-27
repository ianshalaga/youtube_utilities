"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- End screen:
    - Se trata como un video normal.
    - No se valida compatibilidad aquí.
- MediaDiscoveryService:
    - Se reutiliza para descubrir videos válidos.
- random.choice():
    - Selecciona un elemento aleatorio de una secuencia.
    - Lanza IndexError si la secuencia está vacía.
"""

from pathlib import Path
import random

from core.config_manager import ConfigManager
from services.media.discovery.media_discovery import MediaDiscoveryService


class EndScreenSelector:
    """
    Selecciona un video de pantalla final (end screen)
    desde un directorio.
    """

    def __init__(self):
        self._config = ConfigManager()

    def select(
        self,
        end_screens_dir: Path,
        *,
        randomize: bool = False
    ) -> Path:
        """
        Selecciona un video de pantalla final.

        Args:
            end_screens_dir:
                Directorio que contiene los videos de end screen.
            random:
                Si True, selecciona un video aleatorio.
                Si False, selecciona el primero en orden.

        Returns:
            Ruta del video seleccionado.

        Raises:
            FileNotFoundError:
                Si el directorio no existe.
            ValueError:
                Si no se encuentran videos válidos.
        """
        if not end_screens_dir.exists():
            raise FileNotFoundError(end_screens_dir)

        videos = MediaDiscoveryService.discover(
            end_screens_dir,
            self._config.video_supported_extensions
        )

        if not videos:
            raise ValueError(
                "No se encontraron videos de end screen."
            )

        if randomize:
            return random.choice(videos)

        # Selección determinista (primer archivo ordenado)
        return videos[0]
