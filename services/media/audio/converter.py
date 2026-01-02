from pathlib import Path
import os
from core.config_manager import ConfigManager
import subprocess

config = ConfigManager()


class AudioConverter:
    def __init__(self):
        pass

    def convert(self, src: Path, dst_dir: Path) -> Path:
        dst_dir.mkdir(exist_ok=True)
        dst_path = dst_dir / f"{src.stem}_tmp.{config.audio_target_container}"

        cmd = [
            config.paths_ffmpeg,
            "-y",  # force overwrite
            "-i", str(src),  # input
            "-vn",  # audio only
            # normalize
            "-af", f"loudnorm=I={config.audio_lufs_target}:TP={config.audio_true_peak}:LRA={config.audio_lra}",
            "-c:a", config.audio_target_codec,  # aac
            "-b:a", config.audio_target_bitrate,  # 320k
            "-ar", str(config.audio_target_samplerate),  # 48000
            str(dst_path)  # output
        ]

        subprocess.run(cmd, check=True)
        return dst_path
