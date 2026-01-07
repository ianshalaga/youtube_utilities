from dataclasses import dataclass


@dataclass(frozen=True)
class VideoEncodingDescriptor:
    video_codec: str
    video_bitrate: str | None
    pixel_format: str
    width: int
    height: int
    frame_rate: float

    audio_codec: str | None
    audio_bitrate: str | None
    sample_rate: int | None
    channels: int | None
