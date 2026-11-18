from pathlib import Path
from unittest.mock import Mock

import pytest

from services.media.ffprobe_provider import FFProbeProvider


def make_provider(video_stream: dict) -> FFProbeProvider:
    provider = FFProbeProvider.__new__(FFProbeProvider)
    provider._ffprobe = Mock(
        return_value={"streams": [{"codec_type": "video", **video_stream}]}
    )
    return provider


def test_video_duration_uses_video_stream_duration() -> None:
    provider = make_provider({"duration": "12.75"})

    assert provider.video_duration(Path("base.mkv")) == pytest.approx(12.75)


def test_video_duration_falls_back_to_duration_ticks_and_time_base() -> None:
    provider = make_provider(
        {
            "duration_ts": "900000",
            "time_base": "1/90000",
        }
    )

    assert provider.video_duration(Path("base.mkv")) == pytest.approx(10.0)


def test_video_duration_rejects_missing_stream_duration_metadata() -> None:
    provider = make_provider({})

    with pytest.raises(ValueError, match="duración del flujo de vídeo"):
        provider.video_duration(Path("base.mkv"))
