from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.publication_settings import PublicationSettings
from services.youtube.album_manifest.exceptions import ManifestConfigurationError


class YamlMapper:
    """Maps validated YAML data into an AlbumManifest."""

    def map(self, data: dict[str, Any]) -> AlbumManifest:
        """Convert validated YAML data into an AlbumManifest."""

        try:
            publication = PublicationSettings(
                first_publish_at=datetime.fromisoformat(
                    data["publication"]["first_publish_at"]
                ),
                timezone=data["publication"]["timezone"],
                interval_days=data["publication"]["interval_days"],
            )

            return AlbumManifest(
                name=data["album"],
                name_prefix=data["name_prefix"],
                videos=list(data["videos"]),
                description=data["description"],
                thumbnail=(
                    Path(data["thumbnail"])
                    if data["thumbnail"] is not None
                    else None
                ),
                playlists=list(data["playlists"]),
                made_for_kids=data["made_for_kids"],
                contains_synthetic_media=data["contains_synthetic_media"],
                tags=(
                    list(data["tags"])
                    if data["tags"] is not None
                    else None
                ),
                game=data["game"],
                publication=publication,
            )

        except (KeyError, TypeError, ValueError) as exc:
            raise ManifestConfigurationError(
                f"Unable to map manifest data: {exc}"
            ) from exc