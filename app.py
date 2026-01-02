from pathlib import Path
from domain.media.audio import Audio
from services.media.probe import FFprobeMediaProbeProvider
from services.media.audio.converter import AudioConverter
from core.config_manager import ConfigManager
import os

config = ConfigManager()
audio_converter = AudioConverter()

path_text = "F:/DESCARGAS/Música/YouTube/Soul Saga OST/01 Soul Edge/Super Battle Sound Attack/01 Opening Title Ver.1 [Arcade Demo Intro (Ver. 1)].mp3"
output_path = Path()

audio = Audio(Path(path_text), FFprobeMediaProbeProvider())

print(audio.duration)

dst = audio_converter.convert(audio.path, audio.path.parent)

print(dst)
