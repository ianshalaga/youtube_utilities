from pathlib import Path

import pytest

from services.youtube.video_id_overrides_reader import (
    VideoIdOverridesError,
    VideoIdOverridesReader,
)


def test_reader_loads_title_to_video_id_mapping(tmp_path: Path) -> None:
    path = tmp_path / "video_id_overrides.yaml"
    path.write_text(
        'videos:\n  "067 Manifest title": "aB3dEfGhI12"\n',
        encoding="utf-8",
    )

    assert VideoIdOverridesReader().read(path) == {
        "067 Manifest title": "aB3dEfGhI12"
    }


@pytest.mark.parametrize(
    "contents",
    [
        "[]\n",
        "videos: []\n",
        'videos:\n  "067 Manifest title": 123\n',
        'videos:\n  "": "youtube-id"\n',
    ],
)
def test_reader_rejects_invalid_mappings(
    tmp_path: Path,
    contents: str,
) -> None:
    path = tmp_path / "video_id_overrides.yaml"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(VideoIdOverridesError):
        VideoIdOverridesReader().read(path)
