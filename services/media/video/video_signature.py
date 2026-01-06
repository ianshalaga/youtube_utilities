from dataclasses import dataclass


@dataclass(frozen=True)
class VideoSignature:
    codec: str
    width: int
    height: int
    frame_rate: float
    audio_codecs: tuple[str, ...]
    audio_stream_count: int
