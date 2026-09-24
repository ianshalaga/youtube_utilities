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
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from core.config_manager import ConfigManager
from core.time_utils import seconds_to_hhmmss_ms
from services.filesystem.output_partitioner import OutputDirectoryPartitioner
from services.media.discovery.media_discovery import MediaDiscoveryService
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.audio.converter import AudioConverter
from services.media.ffprobe_provider import FFProbeProvider
from .console import VideoMusicConsole


class VideoMusicProcessor:
    """
    Orquesta la generación de videos musicales a partir de un video base
    y un conjunto de archivos de audio.

    Responsabilidades:
    - Mantener el orden original de las pistas
    - Limitar la cantidad de videos por directorio de salida
    - Decidir si existe particionado
    - Crear subdirectorios numerados cuando sea necesario
    - Convertir audio cuando sea necesario
    - Construir comandos mkvmerge específicos del caso de uso
    - Delegar la ejecución a MKVMergeRunner

    Esta clase contiene la lógica de dominio del caso de uso
    "video + canciones".
    """

    def __init__(
        self,
        mkvmerge_runner: MKVMergeRunner,
        audio_converter: AudioConverter,
        ffprobe_provider: FFProbeProvider,
        max_items_per_dir: int | None = None,
        console: VideoMusicConsole | None = None,
    ):
        self._config = ConfigManager()
        self._mkvmerge_runner = mkvmerge_runner
        self._audio_converter = audio_converter
        self._ffprobe_provider = ffprobe_provider
        self._console = console or VideoMusicConsole()
        self._output_partitioner: OutputDirectoryPartitioner | None

        self._max_items_per_dir = (
            max_items_per_dir
            if max_items_per_dir is not None
            else self._config.video_music_max_items_per_dir
        )

        self._output_partitioner = (
            OutputDirectoryPartitioner(self._max_items_per_dir)
            if self._max_items_per_dir is not None
            else None
        )

        # Evita crear más threads que trabajo real
        cpu_workers = max(1, os.cpu_count() - 1)
        if self._max_items_per_dir is None:
            self._max_workers = cpu_workers
        else:
            self._max_workers = min(cpu_workers, self._max_items_per_dir)

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

        self._console.job_started(
            video_path=video_path,
            audios_dir=audios_dir,
            output_dir=output_dir,
            total_tracks=total_songs,
            max_items_per_dir=self._max_items_per_dir,
        )

        # ───────────────────────────────
        # MODO SIN SUBDIRECTORIOS
        # ───────────────────────────────
        if (
            self._max_items_per_dir is None
            or total_songs <= self._max_items_per_dir
        ):
            self._console.processing_started()

            with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
                futures = []

                for index, audio_path in enumerate(audio_files, start=1):
                    futures.append(
                        executor.submit(
                            self._process_single,
                            video_path,
                            audio_path,
                            output_dir,
                            index,
                            total_songs,
                        )
                    )

                for future in as_completed(futures):
                    future.result()

            self._console.job_completed(total_songs, output_dir)
            return

        # ───────────────────────────────
        # MODO CON SUBDIRECTORIOS
        # ───────────────────────────────
        total_directories = (
            (total_songs + self._max_items_per_dir - 1)
            // self._max_items_per_dir
        )
        self._console.partition_started(
            total_tracks=total_songs,
            max_items_per_dir=self._max_items_per_dir,
            total_directories=total_directories,
        )
        self._console.processing_started()

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = []

            for index, audio_path in enumerate(audio_files):
                assert self._output_partitioner is not None
                subdir = self._output_partitioner.get_output_dir(
                    index=index,
                    total_items=total_songs,
                    root_dir=output_dir
                )

                subdir.mkdir(exist_ok=True)

                futures.append(
                    executor.submit(
                        self._process_single,
                        video_path,
                        audio_path,
                        subdir,
                        index + 1,
                        total_songs,
                    )
                )

            for future in as_completed(futures):
                future.result()

        self._console.job_completed(total_songs, output_dir)

    def _process_single(
        self,
        video_path: Path,
        audio_path: Path,
        output_dir: Path,
        index: int,
        total: int,
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
        self._console.track_started(
            index=index,
            total=total,
            audio_path=audio_path,
            output_dir=output_dir,
        )

        try:
            tmp_audio_path = self._audio_converter.convert(
                src=audio_path,
                dst_dir=output_dir
            )
            self._console.audio_converted(audio_path, tmp_audio_path)

            duration_seconds = self._ffprobe_provider.duration(tmp_audio_path)
            duration = seconds_to_hhmmss_ms(duration_seconds)
            self._console.duration_detected(audio_path, duration)

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
            self._console.video_created(audio_path, output_path)

        except Exception as error:
            self._console.track_failed(index, total, audio_path, error)
            raise

        finally:
            if "tmp_audio_path" in locals() and tmp_audio_path.exists():
                tmp_audio_path.unlink()
                self._console.temporary_files_cleaned(audio_path)

        self._console.track_completed(index, total, audio_path)

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
