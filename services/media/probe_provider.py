from pathlib import Path
import subprocess
import json

from domain.media.base import MediaProbeProvider
from domain.media.video.video_signature import VideoSignature
from core.config_manager import ConfigManager


class FFProbeMediaProbeProvider(MediaProbeProvider):
    """
    Proveedor de metadatos multimedia basado en ffprobe.

    Responsabilidades:
    - Ejecutar ffprobe como herramienta externa de inspección multimedia.
    - Parsear la salida JSON generada por ffprobe.
    - Exponer consultas semánticas de metadatos de video y audio.
    - Cachear resultados para evitar ejecuciones redundantes.

    Este provider actúa como capa de infraestructura pura.
    No contiene lógica de negocio ni validaciones de dominio.

    Consumidores típicos:
    - VideoCompatibilityValidator
    - VideoPartitioner
    - EndScreenSelector
    - TimestampFileBuilder
    """

    def __init__(self):
        """
        Inicializa el proveedor de ffprobe.

        Mantiene un cache interno en memoria cuya clave es la
        ruta del archivo multimedia (Path) y cuyo valor es el
        diccionario completo devuelto por ffprobe.

        Se asume que los archivos no mutan durante el ciclo
        de vida del provider.
        """
        self._cache: dict[Path, dict] = {}
        self._config = ConfigManager()

    def _probe(self, path: Path) -> dict:
        """
        Ejecuta ffprobe sobre un archivo multimedia y devuelve
        el resultado completo como un diccionario Python.

        El resultado se cachea para llamadas posteriores,
        evitando ejecuciones repetidas de ffprobe sobre el
        mismo archivo.

        Args:
            path:
                Ruta del archivo multimedia a inspeccionar.

        Returns:
            dict:
                Estructura completa de metadatos generada
                por ffprobe en formato JSON.

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

    # ───────────────────────────────
    # Consultas públicas
    # ───────────────────────────────

    def duration(self, path: Path) -> float:
        """
        Devuelve la duración total del archivo multimedia
        expresada en segundos.

        Esta información proviene de los metadatos globales
        del contenedor (format.duration).

        Args:
            path:
                Ruta del archivo multimedia.

        Returns:
            float:
                Duración total del archivo en segundos.
        """
        data = self._probe(path)
        return float(data["format"]["duration"])

    def video_signature(self, path: Path) -> VideoSignature:
        """
        Construye una firma de video comparable a partir
        de los metadatos del archivo.

        La firma representa las características relevantes
        para validar compatibilidad entre videos, tales como:
        - codec de video
        - resolución
        - framerate
        - codecs de audio
        - cantidad de streams de audio

        Args:
            path:
                Ruta del archivo multimedia.

        Returns:
            VideoSignature:
                Value Object inmutable que representa
                la firma técnica del video.
        """
        video = self._video_stream(path)
        audios = self._audio_streams(path)

        frame_rate = self._parse_frame_rate(video["r_frame_rate"])

        return VideoSignature(
            codec=video["codec_name"],
            width=int(video["width"]),
            height=int(video["height"]),
            frame_rate=frame_rate,
            audio_codecs=tuple(a["codec_name"] for a in audios),
            audio_stream_count=len(audios),
        )

    # ───────────────────────────────
    # Helpers privados
    # ───────────────────────────────

    def _video_stream(self, path: Path) -> dict:
        """
        Devuelve el stream de video principal del archivo.

        Se asume que el archivo contiene al menos un stream
        de tipo video.

        Args:
            path:
                Ruta del archivo multimedia.

        Returns:
            dict:
                Diccionario correspondiente al stream de video.
        """
        data = self._probe(path)
        return next(
            s for s in data["streams"]
            if s["codec_type"] == "video"
        )

    def _audio_streams(self, path: Path) -> list[dict]:
        """
        Devuelve todos los streams de audio presentes
        en el archivo multimedia.

        Args:
            path:
                Ruta del archivo multimedia.

        Returns:
            list[dict]:
                Lista de streams de audio.
        """
        data = self._probe(path)
        return [
            s for s in data["streams"]
            if s["codec_type"] == "audio"
        ]

    @staticmethod
    def _parse_frame_rate(value: str) -> float:
        """
        Convierte una representación racional de framerate
        devuelta por ffprobe en un valor float.

        Ejemplo:
            '30000/1001' → 29.97

        Args:
            value:
                Framerate en formato 'numerador/denominador'.

        Returns:
            float:
                Framerate expresado como número decimal.
        """
        num, den = value.split("/")
        return float(num) / float(den)
