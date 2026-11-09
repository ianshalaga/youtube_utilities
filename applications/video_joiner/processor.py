"""
NOTAS DE IMPLEMENTACIÓN (uso personal)

- VideoJoinerProcessor:
    - Es un orquestador, no ejecuta herramientas externas directamente.
- mkvmerge:
    - La concatenación correcta se realiza con el operador "+".
    - El nombre del archivo final NO es fiable: debe detectarse.
- Compatibilidad:
    - Todos los videos deben compartir parámetros técnicos.
- Particionado:
    - Se agrupan videos completos.
- Paralelización:
    - Se paraleliza por "parte final".
    - Cada parte usa su propio directorio temporal determinista.
"""

from pathlib import Path
from typing import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import shutil

from core.config_manager import ConfigManager
from services.media.ffprobe_provider import FFProbeProvider
from services.media.discovery.media_discovery import MediaDiscoveryService
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.video.compatibility_validator import VideoCompatibilityValidator
from services.media.video.joiner.partitioner import VideoPartitioner
from services.media.video.joiner.end_screen_selector import EndScreenSelector
from services.media.video.joiner.timestamp_file_builder import TimestampFileBuilder
from applications.video_joiner.progress import VideoJoinerProgressReporter


class VideoJoinerProcessor:
    """
    Orquesta la unión de múltiples videos en uno o más archivos finales.
    """

    def __init__(
        self,
        mkvmerge_runner: MKVMergeRunner,
        ffprobe_provider: FFProbeProvider,
        max_items_per_dir: int | None = None,
        console: VideoJoinerProgressReporter | None = None,
    ):
        self._config = ConfigManager()
        self._probe_provider = ffprobe_provider
        self._mkvmerge_runner = mkvmerge_runner
        self._console = console
        self._validator = VideoCompatibilityValidator(self._probe_provider)
        self._partitioner = VideoPartitioner(self._probe_provider)
        self._end_screen_selector = EndScreenSelector()
        self._timestamp_builder = TimestampFileBuilder(self._probe_provider)

        self._max_items_per_dir = (
            max_items_per_dir
            if max_items_per_dir is not None
            else self._config.video_joiner_max_items_per_dir
        )

        self._max_workers = min(
            max(1, os.cpu_count() - 1),
            self._max_items_per_dir
        )

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
        timestamps_secuence: bool = True,
        extra_description: str | None = None,
    ) -> None:
        try:
            self._process(
                videos_dir=videos_dir,
                output_dir=output_dir,
                base_name=base_name,
                target_duration=target_duration,
                end_screens_dir=end_screens_dir,
                random_end_screen=random_end_screen,
                timestamps_prefix=timestamps_prefix,
                timestamps_secuence=timestamps_secuence,
                extra_description=extra_description,
            )
        except Exception as error:
            if self._console is not None:
                self._console.job_failed(error)
            raise

    def _process(
        self,
        videos_dir: Path,
        output_dir: Path,
        base_name: str,
        *,
        target_duration: float | None = None,
        end_screens_dir: Path | None = None,
        random_end_screen: bool = False,
        timestamps_prefix: str = "",
        timestamps_secuence: bool = True,
        extra_description: str | None = None
    ) -> None:

        if not videos_dir.exists():
            raise FileNotFoundError(videos_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        videos = MediaDiscoveryService.discover(
            videos_dir,
            self._config.video_supported_extensions
        )

        if not videos:
            raise ValueError("No se encontraron videos para unir.")

        self._validator.validate(videos)

        partitions = (
            [videos]
            if target_duration is None
            else self._partitioner.partition(videos, target_duration)
        )

        total_parts = len(partitions)
        max_workers = min(self._max_workers, total_parts)

        if self._console is not None:
            self._console.job_started(
                videos_dir=videos_dir,
                output_dir=output_dir,
                total_videos=len(videos),
                total_parts=total_parts,
                target_duration=target_duration,
            )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for index, part_videos in enumerate(partitions):
                futures.append(
                    executor.submit(
                        self._process_single_part,
                        index=index,
                        part_videos=part_videos,
                        total_parts=total_parts,
                        output_dir=output_dir,
                        base_name=base_name,
                        end_screens_dir=end_screens_dir,
                        random_end_screen=random_end_screen,
                        timestamps_prefix=timestamps_prefix,
                        timestamps_secuence=timestamps_secuence,
                        extra_description=extra_description
                    )
                )

            for future in as_completed(futures):
                future.result()

        if self._console is not None:
            self._console.job_completed(total_parts, output_dir)

    def _build_mkvmerge_command(
        self,
        videos: Iterable[Path],
        output_path: Path
    ) -> list[str]:

        videos = list(videos)
        if not videos:
            raise ValueError("No videos provided for mkvmerge.")

        cmd = [self._config.paths_mkvmerge, "-o", str(output_path)]
        cmd.append(str(videos[0]))

        for video in videos[1:]:
            cmd.append("+")
            cmd.append(str(video))

        return cmd

    def _process_single_part(
        self,
        *,
        index: int,
        part_videos: list[Path],
        total_parts: int,
        output_dir: Path,
        base_name: str,
        end_screens_dir: Path | None,
        random_end_screen: bool,
        timestamps_prefix: str,
        timestamps_secuence: bool,
        extra_description: str | None
    ) -> None:

        output_name = (
            f"{base_name} ({index + 1}-{total_parts})"
            if total_parts > 1
            else base_name
        )

        final_output = output_dir / f"{output_name}.mkv"
        timestamps_path = output_dir / f"{output_name}.txt"

        if self._console is not None:
            self._console.part_started(
                index=index + 1,
                total_parts=total_parts,
                videos=part_videos,
                output_path=final_output,
            )

        temp_dir = output_dir / output_name

        try:
            temp_dir.mkdir(exist_ok=True)
            end_screen = None
            if end_screens_dir is not None:
                end_screen = self._end_screen_selector.select(
                    end_screens_dir,
                    randomize=random_end_screen
                )

            final_videos = (
                part_videos + [end_screen]
                if end_screen is not None
                else part_videos
            )

            self._validator.validate(final_videos)

            temp_output = temp_dir / f"{output_name}.mkv"

            cmd = self._build_mkvmerge_command(
                final_videos,
                temp_output
            )

            self._mkvmerge_runner.run(cmd)

            if not temp_output.exists():
                raise RuntimeError(
                    f"mkvmerge no generó el archivo esperado: {temp_output}"
                )

            shutil.move(str(temp_output), str(final_output))

            self._timestamp_builder.build(
                videos=final_videos,
                output_path=timestamps_path,
                prefix=timestamps_prefix,
                secuence=timestamps_secuence,
                extra_description=extra_description
            )

            if self._console is not None:
                self._console.part_completed(
                    index=index + 1,
                    total_parts=total_parts,
                    output_path=final_output,
                    timestamps_path=timestamps_path,
                )

        except Exception as error:
            if self._console is not None:
                self._console.part_failed(
                    index=index + 1,
                    total_parts=total_parts,
                    output_path=final_output,
                    error=error,
                )
            raise

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
