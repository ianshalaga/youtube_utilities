"""Domain representation of a YouTube album manifest.

This module contains the domain representation of the information
provided by the user for an album.

The manifest is independent of the format used to provide it.
YAML parsing belongs to the infrastructure layer.
"""

from __future__ import annotations

from pathlib import Path

from domain.youtube.publication_settings import PublicationSettings


class AlbumManifest:
    """Represents the desired configuration of a YouTube album."""

    def __init__(
        self,
        name: str,
        name_prefix: str,
        videos: list[str],
        description: str,
        thumbnail: Path | None,
        playlists: list[str],
        made_for_kids: bool,
        contains_synthetic_media: bool,
        tags: list[str] | None,
        game: str,
        publication: PublicationSettings,
    ) -> None:
        if len(description) > 5000:
            raise ValueError(
                "Album manifest description must not exceed 5000 characters."
            )

        if not isinstance(publication, PublicationSettings):
            raise TypeError(
                "publication must be a PublicationSettings instance."
            )

        self._name = name
        self._name_prefix = name_prefix
        self._videos = list(videos)
        self._description = description
        self._thumbnail = thumbnail
        self._playlists = list(playlists)
        self._made_for_kids = made_for_kids
        self._contains_synthetic_media = contains_synthetic_media
        self._tags = list(tags) if tags is not None else None
        self._game = game
        self._publication = publication

    @property
    def name(self) -> str:
        """Return the album name."""
        return self._name

    @property
    def name_prefix(self) -> str:
        """Return the prefix used to compose video names."""
        return self._name_prefix

    @property
    def videos(self) -> tuple[str, ...]:
        """Return the desired video specifications."""
        return tuple(self._videos)

    @property
    def description(self) -> str:
        """Return the desired album description."""
        return self._description

    @property
    def thumbnail(self) -> Path | None:
        """Return the album thumbnail path."""
        return self._thumbnail

    @property
    def playlists(self) -> tuple[str, ...]:
        """Return the YouTube playlist IDs."""
        return tuple(self._playlists)

    @property
    def made_for_kids(self) -> bool:
        """Return whether the videos are made for kids."""
        return self._made_for_kids

    @property
    def contains_synthetic_media(self) -> bool:
        """Return whether the videos contain synthetic media."""
        return self._contains_synthetic_media

    @property
    def tags(self) -> tuple[str, ...] | None:
        """Return the desired video tags."""
        return tuple(self._tags) if self._tags is not None else None

    @property
    def game(self) -> str:
        """Return the game associated with the album."""
        return self._game

    @property
    def publication(self) -> PublicationSettings:
        return self._publication

    def __repr__(self) -> str:
        return (
            f"AlbumManifest("
            f"name={self._name!r}, "
            f"video_count={len(self._videos)})"
        )