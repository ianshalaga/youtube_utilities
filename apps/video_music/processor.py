"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- Path.iterdir(): devuelve un iterador de Path, no una lista.
- sorted(Path): ordena lexicográficamente; funciona correctamente
  cuando los nombres de archivo comienzan con 01, 02, 03, etc.
- // (floor division): división entera, devuelve el cociente truncado.
  Se usa para agrupar elementos en bloques de tamaño fijo.
- enumerate(iterable): devuelve pares (índice, elemento).
- f"{value:0Nd}": formateo con padding de ceros a la izquierda.
- raise ValueError: excepción adecuada para errores de uso/entrada.
- ThreadPoolExecutor:
    - Ejecuta tareas I/O-bound en paralelo.
    - Adecuado para subprocess.run (ffmpeg / mkvmerge).
- executor.submit():
    - Envía una tarea al pool y devuelve un Future.
- as_completed():
    - Permite manejar errores tan pronto como ocurren.
- future.result():
    - Re-lanza la excepción si la tarea falló.
"""

from pathlib import Path
from math import ceil
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from core.config_manager import ConfigManager
from core.time_utils import seconds_to_hhmmss_ms
from services.filesystem.output_partitioner import OutputDirectoryPartitioner
from services.media.discovery.media_discovery import MediaDiscoveryService
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.audio.converter import AudioConverter
from services.media.probe_provider import FFProbeMediaProbeProvider


class VideoMusicProcessor:
    """
    Orquesta la generación de videos musicales a partir de un video base
    y un conjunto de archivos de audio.

    Responsabilidades:
    - Mantener el orden original de las pistas
    - Limitar la cantidad de videos por directorio de salida
    - Crear subdirectorios numerados cuando sea necesario
    - Convertir audio cuando sea necesario
    - Construir comandos mkvmerge específicos del caso de uso
    - Delegar la ejecución a MKVMergeRunner

    Esta clase contiene la lógica de dominio del caso de uso
    "video + canciones".
    """

    def __init__(self, max_items_per_dir: int | None = None):
        self._config = ConfigManager()
        self._mkvmerge_runner = MKVMergeRunner()
        self._audio_converter = AudioConverter()
        self._probe_provider = FFProbeMediaProbeProvider()

        self._max_items_per_dir = (
            max_items_per_dir
            if max_items_per_dir is not None
            else self._config.video_music_max_items_per_dir
        )

        # Evita crear más threads que trabajo real
        self._max_workers = min(
            max(1, os.cpu_count() - 1),
            self._max_items_per_dir
        )

    def process(
        self,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path
    ) -> None:
        """
        Procesa un directorio de canciones y genera un video por cada pista.

        Dependiendo de la cantidad de canciones y del límite configurado,
        los resultados se escribirán directamente en el directorio de salida
        o bien se dividirán en subdirectorios numerados.

        Args:
            video_path:
                Ruta al archivo de video base.
            audios_dir:
                Directorio que contiene los archivos de audio.
            output_dir:
                Directorio donde se escribirán los videos resultantes.

        Raises:
            ValueError:
                Si no se encuentran archivos de audio.
            FileNotFoundError:
                Si el video base no existe.
        """
        if not video_path.exists():
            raise FileNotFoundError(video_path)

        audio_files = MediaDiscoveryService.discover(
            audios_dir,
            self._config.audio_supported_extensions
        )

        if not audio_files:
            raise ValueError("No se encontraron archivos de audio.")

        output_dir.mkdir(parents=True, exist_ok=True)

        total_songs = len(audio_files)

        # ───────────────────────────────
        # MODO SIN SUBDIRECTORIOS
        # ───────────────────────────────
        if total_songs <= self._max_items_per_dir:
            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = []

                for audio_path in audio_files:
                    futures.append(
                        executor.submit(
                            self._process_single,
                            video_path,
                            audio_path,
                            output_dir
                        )
                    )

                for future in as_completed(futures):
                    future.result()

            return

        # ───────────────────────────────
        # MODO CON SUBDIRECTORIOS
        # ───────────────────────────────
        total_subdirs = ceil(total_songs / self._max_items_per_dir)
        padding = len(str(total_subdirs))

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = []

            for index, audio_path in enumerate(audio_files):
                subdir = self._get_subdir_path(index, padding, output_dir)
                subdir.mkdir(exist_ok=True)

                futures.append(
                    executor.submit(
                        self._process_single,
                        video_path,
                        audio_path,
                        subdir
                    )
                )

            for future in as_completed(futures):
                future.result()

    def _process_single(
        self,
        video_path: Path,
        audio_path: Path,
        output_dir: Path
    ) -> None:
        """
        Procesa una única pista de audio contra el video base.

        Flujo:
        1. Convierte el audio a un formato temporal
        2. Obtiene la duración exacta del audio convertido
        3. Construye el comando mkvmerge
        4. Ejecuta mkvmerge
        5. Limpia el archivo temporal

        Args:
            video_path:
                Ruta al video base.
            audio_path:
                Ruta a la pista de audio.
            output_dir:
                Directorio de salida.
        """
        tmp_audio_path = self._audio_converter.convert(
            src=audio_path,
            dst_dir=output_dir
        )

        try:
            duration_seconds = self._probe_provider.duration(tmp_audio_path)
            duration = seconds_to_hhmmss_ms(duration_seconds)

            output_path = output_dir / f"{audio_path.stem}.mkv"

            cmd = [
                self._config.paths_mkvmerge,
                "-o", str(output_path),
                "--split", f"parts:00:00:00-{duration}",
                "--no-audio",
                "--no-subtitles",
                str(video_path),
                "--audio-tracks", "0",
                str(tmp_audio_path),
            ]

            self._mkvmerge_runner.run(cmd)

            self._cleanup_segments(output_dir, audio_path.stem)

        finally:
            if tmp_audio_path.exists():
                tmp_audio_path.unlink()

    def _get_subdir_path(
        self,
        file_index: int,
        padding: int,
        output_dir: Path
    ) -> Path:
        """
        Calcula el subdirectorio de salida correspondiente a un archivo.

        Args:
            file_index:
                Índice del archivo dentro de la lista total.
            padding:
                Cantidad de dígitos a usar en el nombre del directorio.
            output_dir:
                Directorio raíz de salida.

        Returns:
            Ruta completa al subdirectorio correspondiente.
        """
        subdir_number = (file_index // self._max_items_per_dir) + 1
        return output_dir / f"{subdir_number:0{padding}d}"

    def _cleanup_segments(self, output_dir: Path, base_name: str) -> None:
        """
        Elimina segmentos sobrantes generados por mkvmerge y
        conserva únicamente el archivo principal.

        Args:
            output_dir:
                Directorio donde se encuentran los segmentos.
            base_name:
                Nombre base del archivo.
        """
        files = sorted(output_dir.glob(f"{base_name}-*.mkv"))
        if not files:
            return

        main_file = files[0]
        final_path = output_dir / f"{base_name}.mkv"
        main_file.rename(final_path)

        for f in files[1:]:
            f.unlink()
