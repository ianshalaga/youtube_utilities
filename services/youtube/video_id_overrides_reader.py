from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class VideoIdOverridesError(ValueError):
    """Raised when the YouTube video ID override file is invalid."""


class VideoIdOverridesReader:
    """Read manifest-title to YouTube-ID mappings from a YAML file."""

    def read(self, path: Path) -> dict[str, str]:
        try:
            with path.open("r", encoding="utf-8") as file:
                data: Any = yaml.safe_load(file)
        except OSError as exc:
            raise VideoIdOverridesError(
                f"Unable to read video ID overrides '{path}': {exc}"
            ) from exc
        except yaml.YAMLError as exc:
            raise VideoIdOverridesError(
                f"Invalid YAML in video ID overrides '{path}': {exc}"
            ) from exc

        if not isinstance(data, dict) or not isinstance(data.get("videos"), dict):
            raise VideoIdOverridesError(
                "Video ID overrides must contain a 'videos' mapping."
            )

        overrides: dict[str, str] = {}
        for title, video_id in data["videos"].items():
            if not isinstance(title, str) or not title.strip():
                raise VideoIdOverridesError(
                    "Video ID override titles must be non-empty strings."
                )
            if not isinstance(video_id, str) or not video_id.strip():
                raise VideoIdOverridesError(
                    f"Video ID for {title!r} must be a non-empty string."
                )
            overrides[title] = video_id.strip()

        return overrides
