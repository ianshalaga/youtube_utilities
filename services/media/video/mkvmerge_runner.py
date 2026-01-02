from pathlib import Path
import subprocess
from core.config_manager import ConfigManager
from core.time_utils import seconds_to_hhmmss_ms
from domain.media.audio import Audio
from domain.media.video import Video
from services.media.audio.converter import AudioConverter
from services.media.probe import FFprobeMediaProbeProvider

config = ConfigManager()
audio_converter = AudioConverter()


class MKVMergeRunner:
    def __init__(self):
        pass

    def cut_video(self, video: Video, audio: Audio, output_dir: Path):
        if not video.path.exists():
            raise FileNotFoundError(video.path)

        if not audio.path.exists():
            raise FileNotFoundError(audio.path)

        output_dir.mkdir(exist_ok=True, parents=True)

        tmp_audio_path = audio_converter.convert(
            src=audio.path,
            dst_dir=output_dir
        )

        try:
            converted_audio = Audio(
                tmp_audio_path,
                FFprobeMediaProbeProvider()
            )

            duration = seconds_to_hhmmss_ms(converted_audio.duration)

            output_pattern = output_dir / f"{audio.path.stem}.mkv"

            cmd = [
                config.paths_mkvmerge,
                "-o", str(output_pattern),
                "--split", f"parts:00:00:00-{duration}",
                "--no-audio",
                "--no-subtitles",
                str(video.path),
                "--audio-tracks", "0",
                str(tmp_audio_path),
            ]

            subprocess.run(cmd, check=True)

            self._cleanup_segments(output_dir, audio.path.stem)

        finally:
            if tmp_audio_path.exists():
                tmp_audio_path.unlink()

    def _cleanup_segments(self, output_dir: Path, base_name: str):
        files = sorted(output_dir.glob(f"{base_name}-*.mkv"))
        if not files:
            return

        main_file = files[0]
        final_name = output_dir / f"{base_name}.mkv"
        main_file.rename(final_name)

        for f in files[1:]:
            f.unlink()
