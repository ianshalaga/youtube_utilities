from pathlib import Path
from typing import Any

import yaml

from services.youtube.album_manifest.exceptions import (
    ManifestError,
    ManifestParseError,
)

class YamlParser:
    @staticmethod
    def parse(path: Path) -> Any:
        """Parse the YAML document."""

        try:
            with path.open(
                "r",
                encoding="utf-8",
            ) as file:
                return yaml.safe_load(file)

        except yaml.YAMLError as exc:
            problem = getattr(
                exc,
                "problem",
                None,
            )
            mark = getattr(
                exc,
                "problem_mark",
                None,
            )

            if mark is not None:
                location = (
                    f"line {mark.line + 1}, "
                    f"column {mark.column + 1}"
                )
            else:
                location = "unknown location"

            detail = problem or str(exc)

            raise ManifestParseError(
                f"Invalid YAML at {location}: {detail}"
            ) from exc

        except OSError as exc:
            raise ManifestError(
                f"Unable to read manifest '{path}': {exc}"
            ) from exc