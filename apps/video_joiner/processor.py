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
    """

    def __init__(self, max_items_per_dir: int | None = None):
        self._config = ConfigManager()
        self._probe_provider = FFProbeMediaProbeProvider()
        self._mkvmerge_runner = MKVMergeRunner()
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
                        extra_description=extra_description,
                    )
                )

            for future in as_completed(futures):
                future.result()

    def _build_mkvmerge_command(
        self,
        videos: Iterable[Path],
        output_path: Path
    ) -> list[str]:

        videos = list(videos)
        if not videos:
            raise ValueError("No videos provided for mkvmerge.")

        cmd = ["mkvmerge", "-o", str(output_path)]
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
        extra_description: str | None
    ) -> None:

        output_name = (
            f"{base_name} ({index + 1}-{total_parts})"
            if total_parts > 1
            else base_name
        )

        temp_dir = output_dir / output_name
        temp_dir.mkdir(exist_ok=True)

        try:
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

            final_output = output_dir / f"{output_name}.mkv"
            shutil.move(str(temp_output), str(final_output))

            timestamps_path = output_dir / f"{output_name}.txt"
            self._timestamp_builder.build(
                videos=final_videos,
                output_path=timestamps_path,
                prefix=timestamps_prefix,
                extra_description=extra_description
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
