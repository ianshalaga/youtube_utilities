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
from applications.video_music.input import VideoMusicInput
from applications.video_music.output import (
    TrackStatus,
    VideoMusicResult,
    VideoMusicTrackResult,
)
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
        console: VideoMusicConsole | None = None,
    ):
        self._config = ConfigManager()
        self._mkvmerge_runner = mkvmerge_runner
        self._audio_converter = audio_converter
        self._ffprobe_provider = ffprobe_provider
        self._console = console or VideoMusicConsole()

    def process(self, input_data: VideoMusicInput) -> VideoMusicResult:
        """
        Procesa un directorio de canciones y devuelve el resultado de cada pista.

        Raises:
            ValueError: Si el límite es inválido o no se encuentran audios.
            FileNotFoundError: Si el video base no existe.
        """
        video_path = input_data.video_path
        audios_dir = input_data.audios_dir
        output_dir = input_data.output_dir
        max_items_per_dir = input_data.max_items_per_dir

        if max_items_per_dir <= 0:
            raise ValueError("max_items_per_dir debe ser mayor que cero.")

        if not video_path.exists():
            raise FileNotFoundError(video_path)

        audio_files = MediaDiscoveryService.discover(
            audios_dir,
            self._config.audio_supported_extensions,
        )

        if not audio_files:
            raise ValueError("No se encontraron archivos de audio.")

        output_dir.mkdir(parents=True, exist_ok=True)

        total_tracks = len(audio_files)
        total_directories = max(
            1,
            (total_tracks + max_items_per_dir - 1) // max_items_per_dir,
        )

        cpu_workers = max(1, (os.cpu_count() or 1) - 1)
        max_workers = min(cpu_workers, max_items_per_dir)
        output_partitioner = OutputDirectoryPartitioner(max_items_per_dir)

        self._console.job_started(
            video_path=video_path,
            audios_dir=audios_dir,
            output_dir=output_dir,
            total_tracks=total_tracks,
            max_items_per_dir=max_items_per_dir,
        )

        if total_tracks > max_items_per_dir:
            self._console.partition_started(
                total_tracks=total_tracks,
                max_items_per_dir=max_items_per_dir,
                total_directories=total_directories,
            )

        self._console.processing_started()

        # Se reserva una posición por pista para conservar el orden original,
        # aunque los trabajos concurrentes terminen en distinto orden.
        track_results: list[VideoMusicTrackResult | None] = [
            None
        ] * total_tracks

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}

            for index, audio_path in enumerate(audio_files):
                if total_tracks > max_items_per_dir:
                    track_output_dir = output_partitioner.get_output_dir(
                        index=index,
                        total_items=total_tracks,
                        root_dir=output_dir,
                    )
                    track_output_dir.mkdir(parents=True, exist_ok=True)
                else:
                    track_output_dir = output_dir

                future = executor.submit(
                    self._process_single,
                    video_path,
                    audio_path,
                    track_output_dir,
                    index + 1,
                    total_tracks,
                )
                futures[future] = index

            for future in as_completed(futures):
                track_results[futures[future]] = future.result()

        self._console.job_completed(total_tracks, output_dir)

        # Cada tarea debe producir un resultado. La comprobación evita devolver
        # silenciosamente un resultado incompleto si cambia el flujo interno.
        if any(result is None for result in track_results):
            raise RuntimeError(
                "La ejecución terminó sin producir un resultado para cada pista."
            )

        return VideoMusicResult(
            output_dir=output_dir,
            total_tracks=total_tracks,
            tracks=tuple(track_results),
            total_directories=total_directories,
        )

    def _process_single(
        self,
        video_path: Path,
        audio_path: Path,
        output_dir: Path,
        index: int,
        total: int,
    ) -> VideoMusicTrackResult:
        """
        Procesa una pista y devuelve su resultado individual.

        Los fallos de una pista se representan en VideoMusicTrackResult para
        permitir que las demás pistas continúen procesándose.
        """
        self._console.track_started(
            index=index,
            total=total,
            audio_path=audio_path,
            output_dir=output_dir,
        )

        tmp_audio_path: Path | None = None
        duration_seconds: float | None = None
        output_path = output_dir / f"{audio_path.stem}.mkv"
        processing_error: Exception | None = None

        try:
            tmp_audio_path = self._audio_converter.convert(
                src=audio_path,
                dst_dir=output_dir,
            )

            self._console.audio_converted(audio_path, tmp_audio_path)

            duration_seconds = self._ffprobe_provider.duration(tmp_audio_path)
            duration = seconds_to_hhmmss_ms(duration_seconds)

            self._console.duration_detected(audio_path, duration)

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
            processing_error = error

        finally:
            if tmp_audio_path is not None and tmp_audio_path.exists():
                try:
                    tmp_audio_path.unlink()
                    self._console.temporary_files_cleaned(audio_path)
                except Exception as cleanup_error:
                    if processing_error is None:
                        processing_error = cleanup_error

        if processing_error is not None:
            self._console.track_failed(
                index,
                total,
                audio_path,
                processing_error,
            )

            return VideoMusicTrackResult(
                source_path=audio_path,
                output_path=output_path if output_path.exists() else None,
                status=TrackStatus.FAILED,
                duration_seconds=duration_seconds,
                error_message=str(processing_error),
            )

        self._console.track_completed(index, total, audio_path)

        return VideoMusicTrackResult(
            source_path=audio_path,
            output_path=output_path,
            status=TrackStatus.COMPLETED,
            duration_seconds=duration_seconds,
        )

    def _cleanup_segments(
        self,
        output_dir: Path,
        base_name: str
    ) -> None:
        """
        Elimina segmentos sobrantes generados por mkvmerge y
        conserva únicamente el archivo principal.

        Args:
            output_dir:
                Directorio donde se encuentran los segmentos.
            base_name:
                Nombre base del archivo.
        """
        files = sorted(
            output_dir.glob(f"{base_name}-*.mkv")
        )

        if not files:
            return

        main_file = files[0]

        final_path = output_dir / f"{base_name}.mkv"

        main_file.rename(final_path)

        for f in files[1:]:
            f.unlink()