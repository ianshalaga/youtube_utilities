from pathlib import Path
from math import ceil
from domain.media.audio import Audio
from domain.media.video import Video
from services.media.video.mkvmerge_runner import MKVMergeRunner
from core.config_manager import ConfigManager


class VideoMusicProcessor:
    def __init__(self, max_items_per_dir: int | None = None):
        self.config = ConfigManager()
        self.mkvmerge = MKVMergeRunner()
        self.max_items_per_dir = (
            max_items_per_dir
            if max_items_per_dir is not None
            else self.config.video_music_max_items_per_dir
        )

    def process(
        self,
        video_path: Path,
        songs_dir: Path,
        output_dir: Path
    ) -> None:
        video = Video(video_path)

        audio_files = sorted(
            p for p in songs_dir.iterdir()
            if p.is_file()
        )

        if not audio_files:
            raise ValueError("No se encontraron archivos de audio.")

        output_dir.mkdir(parents=True, exist_ok=True)

        total_songs = len(audio_files)

        # ───────────────────────────────
        # MODO SIN SUBDIRECTORIOS
        # ───────────────────────────────
        if total_songs <= self.max_items_per_dir:
            for audio_path in audio_files:
                audio = Audio(audio_path)
                self.mkvmerge.cut_video(
                    video=video,
                    audio=audio,
                    output_dir=output_dir
                )
            return

        # ───────────────────────────────
        # MODO CON SUBDIRECTORIOS
        # ───────────────────────────────
        total_subdirs = ceil(total_songs / self.max_items_per_dir)
        padding = len(str(total_subdirs))

        for index, audio_path in enumerate(audio_files):
            subdir_number = (index // self.max_items_per_dir) + 1
            subdir_name = f"{subdir_number:0{padding}d}"
            subdir = output_dir / subdir_name
            subdir.mkdir(exist_ok=True)

            audio = Audio(audio_path)

            self.mkvmerge.cut_video(
                video=video,
                audio=audio,
                output_dir=subdir
            )
