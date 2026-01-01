from pathlib import Path
from domain.media.audio import Audio
from services.media.probe import FFprobeMediaProbeProvider

path_text = "F:/DESCARGAS/Música/YouTube/Soul Saga OST/01 Soul Edge/Super Battle Sound Attack/01 Opening Title Ver.1 [Arcade Demo Intro (Ver. 1)].mp3"

media = Audio(Path(path_text), FFprobeMediaProbeProvider())

print(media.duration())
