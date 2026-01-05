"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- ffprobe:
    - "-show_format": devuelve metadatos globales del archivo.
    - "-show_streams": devuelve información detallada por stream.
    - "-of json": salida estructurada y fácil de cachear.
- subprocess.run(..., check=True):
    - Lanza CalledProcessError si ffprobe falla.
- Cache interno (_cache):
    - Evita ejecutar ffprobe múltiples veces sobre el mismo archivo.
    - La clave es Path; se asume inmutabilidad del archivo durante la ejecución.
- json.loads():
    - Convierte stdout en estructura dict navegable.
"""

from pathlib import Path
import subprocess
import json

from domain.media.base import MediaProbeProvider
from core.config_manager import ConfigManager


class FFProbeMediaProbeProvider(MediaProbeProvider):
    """
    Proveedor de metadatos multimedia basado en ffprobe.

    Responsabilidades:
    - Ejecutar ffprobe como herramienta externa
    - Obtener y parsear metadatos en formato JSON
    - Proveer información de duración a consumidores del dominio
    - Cachear resultados para evitar ejecuciones redundantes

    Esta clase es infraestructura pura y no contiene
    lógica de negocio ni validaciones de dominio.
    """

    def __init__(self):
        """
        Inicializa el provider de ffprobe.

        Mantiene un cache en memoria para evitar llamadas
        repetidas a ffprobe sobre el mismo archivo.
        """
        self._cache: dict[Path, dict] = {}
        self._config = ConfigManager()

    def _probe(self, path: Path) -> dict:
        """
        Ejecuta ffprobe sobre un archivo multimedia y devuelve
        el resultado completo como diccionario.

        El resultado se cachea para llamadas posteriores.

        Args:
            path:
                Ruta del archivo multimedia a inspeccionar.

        Returns:
            dict:
                Estructura completa de metadatos generada por ffprobe.

        Raises:
            subprocess.CalledProcessError:
                Si ffprobe falla durante la ejecución.
            json.JSONDecodeError:
                Si la salida de ffprobe no es JSON válido.
        """
        if path not in self._cache:
            cmd = [
                self._config.paths_probe,
                "-v", "error",
                "-show_format",
                "-show_streams",
                "-of", "json",
                str(path),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            self._cache[path] = json.loads(result.stdout)

        return self._cache[path]

    def duration(self, path: Path) -> float:
        """
        Devuelve la duración total del archivo multimedia en segundos.

        Args:
            path:
                Ruta del archivo multimedia.

        Returns:
            float:
                Duración total del archivo en segundos.
        """
        data = self._probe(path)
        return float(data["format"]["duration"])
