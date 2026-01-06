"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- VideoJoinerProcessor:
    - Es un orquestador, no ejecuta herramientas externas.
    - Coordina servicios especializados.
- mkvmerge:
    - Permite concatenar archivos compatibles sin recodificación.
- Compatibilidad:
    - Para unir videos deben coincidir:
        - codec
        - resolución
        - framerate
        - número y tipo de pistas
- Particionado por duración:
    - No se corta arbitrariamente.
    - Se agrupan videos completos minimizando la diferencia
      con la duración objetivo.
- Timestamps:
    - Se generan acumulando duraciones en orden.
    - Se reinician por cada parte.
- End screen:
    - Se trata como un video más al final del grupo.
"""

from pathlib import Path
from typing import Iterable

from core.config_manager import ConfigManager
from services.filesystem.output_partitioner import OutputDirectoryPartitioner
from services.media.probe_provider import FFProbeMediaProbeProvider
from services.media.discovery.media_discovery import MediaDiscoveryService
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.video.compatibility_validator import VideoCompatibilityValidator
from services.media.video.joiner.partitioner import VideoPartitioner
from services.media.video.joiner.end_screen_selector import EndScreenSelector
from services.media.video.joiner.timestamp_file_builder import TimestampFileBuilder


class VideoJoinerProcessor:
    """
    Orquesta la unión de múltiples videos en uno o más archivos finales.

    Responsabilidades:
    - Descubrir y ordenar los archivos de video de entrada
    - Validar compatibilidad entre todos los videos
    - Dividir los videos en partes según duración objetivo
    - Seleccionar pantallas finales si corresponde
    - Construir comandos mkvmerge
    - Generar archivos de timestamps para YouTube

    Esta clase no ejecuta herramientas externas directamente;
    delega dicha responsabilidad a servicios especializados.
    """

    def __init__(self):
        self._config = ConfigManager()
        self._probe_provider = FFProbeMediaProbeProvider()
        self._mkvmerge_runner = MKVMergeRunner()
        self._validator = VideoCompatibilityValidator(self._probe_provider)
        self._partitioner = VideoPartitioner(self._probe_provider)
        self._end_screen_selector = EndScreenSelector()
        self._timestamp_builder = TimestampFileBuilder(self._probe_provider)

    def process(
        self,
        videos_dir: Path,
        output_dir: Path,
        base_name: str,
        *,
        target_duration: float | None = None,
        end_screens_dir: Path | None = None,
        random_end_screen: bool = False,
        timestamps_prefix: str = "",
        extra_description: str | None = None
    ) -> None:
        """
        Une videos desde un directorio en uno o más archivos finales.

        Args:
            videos_dir:
                Directorio que contiene los videos a unir.
            output_dir:
                Directorio donde se escribirán los resultados.
            base_name:
                Nombre base del video final.
            target_duration:
                Duración objetivo (en segundos) por video final.
                Si es None, se genera un único archivo.
            end_screens_dir:
                Directorio que contiene pantallas del final opcionales.
            random_end_screen:
                Si True, selecciona una pantalla del final aleatoria.
            timestamps_prefix:
                Prefijo a anteponer en cada línea de timestamps.
            extra_description:
                Texto adicional que se agrega al final del archivo
                de timestamps.

        Raises:
            ValueError:
                Si no se encuentran videos o no son compatibles.
        """
        if not videos_dir.exists():
            raise FileNotFoundError(videos_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        videos = MediaDiscoveryService.discover(
            videos_dir,
            self._config.video_supported_extensions
        )

        if not videos:
            raise ValueError("No se encontraron videos para unir.")

        # Validación global de compatibilidad
        self._validator.validate(videos)

        # Particionado según duración objetivo
        if target_duration is None:
            partitions = [videos]
        else:
            partitions = self._partitioner.partition(
                videos,
                target_duration
            )

        total_parts = len(partitions)

        for index, part_videos in enumerate(partitions, start=1):
            # Selección opcional de end screen
            end_screen = None
            if end_screens_dir is not None:
                end_screen = self._end_screen_selector.select(
                    end_screens_dir,
                    random=random_end_screen
                )

            final_videos = (
                part_videos + [end_screen]
                if end_screen is not None
                else part_videos
            )

            # Nombre del archivo final
            output_name = (
                f"{base_name} ({index}/{total_parts})"
                if total_parts > 1
                else base_name
            )

            output_path = output_dir / f"{output_name}.mkv"

            # Construcción y ejecución del comando mkvmerge
            cmd = self._build_mkvmerge_command(
                final_videos,
                output_path
            )
            self._mkvmerge_runner.run(cmd)

            # Generación del archivo de timestamps
            timestamps_path = output_dir / f"{output_name}.txt"
            self._timestamp_builder.build(
                videos=final_videos,
                output_path=timestamps_path,
                prefix=timestamps_prefix,
                extra_description=extra_description
            )

    def _build_mkvmerge_command(
        self,
        videos: Iterable[Path],
        output_path: Path
    ) -> list[str]:
        """
        Construye el comando mkvmerge para unir videos.

        Args:
            videos:
                Lista de videos a unir.
            output_path:
                Ruta del archivo final.

        Returns:
            Lista de argumentos del comando mkvmerge.
        """
        cmd = ["mkvmerge", "-o", str(output_path)]

        for video in videos:
            cmd.append(str(video))

        return cmd
