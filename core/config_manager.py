import json
from pathlib import Path


class ConfigManager:
    FILE = Path("config.json")

    def __init__(self):
        if not self.FILE.exists():
            raise FileNotFoundError("config.json no encontrado")
        self.data = json.loads(self.FILE.read_text(encoding="utf-8"))

    def save(self):
        self.FILE.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    # PATHS
    @property
    def paths_mkvmerge(self) -> dict:
        return self.data["paths"]["mkvmerge"]

    @property
    def paths_ffmpeg(self) -> dict:
        return self.data["paths"]["ffmpeg"]

    @property
    def paths_probe(self) -> dict:
        return self.data["paths"]["probe"]

    # AUDIO
    @property
    def audio_target_codec(self) -> str:
        return self.data["audio"]["target_codec"]

    @property
    def audio_target_container(self) -> str:
        return self.data["audio"]["target_container"]

    @property
    def audio_target_bitrate(self) -> str:
        return self.data["audio"]["target_bitrate"]

    @property
    def audio_target_samplerate(self) -> int:
        return self.data["audio"]["target_samplerate"]

    @property
    def audio_lufs_target(self) -> int:
        return self.data["audio"]["lufs_target"]

    @property
    def audio_true_peak(self) -> int:
        return self.data["audio"]["true_peak"]

    @property
    def audio_lra(self) -> int:
        return self.data["audio"]["lra"]

    @property
    def audio_supported_extensions(self) -> list:
        return self.data["audio"]["supported_extensions"]

    # APPS
    @property
    def video_music_max_items_per_dir(self) -> int:
        return self.data["apps"]["video_music"]["max_items_per_dir"]

    @property
    def video_music_default_video_path(self) -> str:
        return self.data["apps"]["video_music"]["default_video_path"]

    @property
    def video_music_default_audios_dir(self) -> str:
        return self.data["apps"]["video_music"]["default_audios_dir"]

    @property
    def video_music_default_output_dir(self) -> str:
        return self.data["apps"]["video_music"]["default_output_dir"]
