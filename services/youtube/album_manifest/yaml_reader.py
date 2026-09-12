from __future__ import annotations

from pathlib import Path

from domain.youtube.album_manifest import AlbumManifest

from services.youtube.album_manifest.album_manifest_validator import (
    AlbumManifestValidator,
)
from services.youtube.album_manifest.exceptions import (
    ManifestConfigurationError,
)
from services.youtube.album_manifest.yaml_parser import YamlParser
from services.youtube.album_manifest.yaml_mapper import YamlMapper


class YamlReader:
    """Orchestrates the YAML album manifest reading pipeline."""

    def __init__(self) -> None:
        self._parser = YamlParser()
        self._validator = AlbumManifestValidator()
        self._mapper = YamlMapper()

    def read(self, path: Path) -> AlbumManifest:
        """Read a YAML file and return an AlbumManifest."""

        data = self._parser.parse(path)
        errors = self._validator.validate(data)

        if errors:
            raise ManifestConfigurationError(
                "Invalid manifest configuration:\n"
                + "\n".join(
                    f"- {error}"
                    for error in errors
                )
            )

        return self._mapper.map(data)