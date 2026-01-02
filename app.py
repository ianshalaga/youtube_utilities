from pathlib import Path
from domain.media.audio import Audio
from services.media.probe import FFprobeMediaProbeProvider
from services.media.audio.converter import AudioConverter
from core.config_manager import ConfigManager
import os
from domain.media.video import Video
from domain.media.audio import Audio
from services.media.video.mkvmerge_runner import MKVMergeRunner

config = ConfigManager()
audio_converter = AudioConverter()

# path_text = "F:/DESCARGAS/Música/YouTube/Soul Saga OST/01 Soul Edge/Super Battle Sound Attack/01 Opening Title Ver.1 [Arcade Demo Intro (Ver. 1)].mp3"
# output_path = Path()

# audio = Audio(Path(path_text), FFprobeMediaProbeProvider())

# print(audio.duration)

# dst = audio_converter.convert(audio.path, audio.path.parent)

# print(dst)

audio_path = "F:/DESCARGAS/Nueva/01 Opening Title Ver.1 [Arcade Demo Intro (Ver. 1)].mp3"
video_path = "F:/DESCARGAS/Nueva/02 Opening Title Ver.2 [Arcade Demo Intro (Ver. 2)].mkv"

video = Video(Path(video_path), FFprobeMediaProbeProvider())
audio = Audio(Path(audio_path), FFprobeMediaProbeProvider())

mkvmerge_runner = MKVMergeRunner()
mkvmerge_runner.cut_video(video, audio, Path("F:/DESCARGAS/Nueva/videos"))
