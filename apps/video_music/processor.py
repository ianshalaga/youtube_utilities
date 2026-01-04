from pathlib import Path
from math import ceil
from core.config_manager import ConfigManager
from domain.media.base import MediaProbeProvider
from domain.media.audio import Audio
from domain.media.video import Video
from services.media.video.mkvmerge_runner import MKVMergeRunner
from services.media.probe_provider import FFprobeMediaProbeProvider


class VideoMusicProcessor:
    def __init__(
        self,
        max_items_per_dir: int | None = None,
        probe_provider: MediaProbeProvider | None = None
    ):
        self._config = ConfigManager()
        self._mkvmerge = MKVMergeRunner()
        self._probe_provider = probe_provider or FFprobeMediaProbeProvider()
        self._max_items_per_dir = (
            max_items_per_dir
            if max_items_per_dir is not None
            else self._config.video_music_max_items_per_dir
        )

    def process(
        self,
        video_path: Path,
        audios_dir: Path,
        output_dir: Path
    ) -> None:
        video = Video(video_path, self._probe_provider)

        audio_files = sorted(
            p for p in audios_dir.iterdir()
            if p.is_file() and p.suffix.lower().lstrip(".") in self._config.audio_supported_extensions
        )

        if not audio_files:
            raise ValueError("No se encontraron archivos de audio.")

        output_dir.mkdir(parents=True, exist_ok=True)

        total_songs = len(audio_files)

        # ───────────────────────────────
        # MODO SIN SUBDIRECTORIOS
        # ───────────────────────────────
        if total_songs <= self._max_items_per_dir:
            for audio_path in audio_files:
                audio = Audio(audio_path, self._probe_provider)
                self._mkvmerge.cut_video(
                    video=video,
                    audio=audio,
                    output_dir=output_dir
                )
            return

        # ───────────────────────────────
        # MODO CON SUBDIRECTORIOS
        # ───────────────────────────────
        total_subdirs = ceil(total_songs / self._max_items_per_dir)
        padding = len(str(total_subdirs))

        for index, audio_path in enumerate(audio_files):
            subdir = self._get_subdir_path(index, padding, output_dir)
            subdir.mkdir(exist_ok=True)

            audio = Audio(audio_path, self._probe_provider)

            self._mkvmerge.cut_video(
                video=video,
                audio=audio,
                output_dir=subdir
            )

    def _get_subdir_path(
        self,
        file_index: int,
        padding: int,
        output_dir: Path
    ) -> Path:
        subdir_number = (file_index // self._max_items_per_dir) + 1
        subdir_name = f"{subdir_number:0{padding}d}"
        subdir = output_dir / subdir_name
        return subdir
