from __future__ import annotations

from datetime import datetime
from typing import Any


class AlbumManifestValidator:
    """Validates the structure and types of an album manifest."""

    REQUIRED_KEYS = {
        "album",
        "name_prefix",
        "videos",
        "description",
        "thumbnail",
        "playlists",
        "made_for_kids",
        "contains_synthetic_media",
        "tags",
        "game",
        "publication",
    }

    PUBLICATION_REQUIRED_KEYS = {
        "first_publish_at",
        "interval_days",
    }

    def validate(self, data: Any) -> list[str]:
        """
        Validate the manifest structure.

        Returns:
            A list containing every structural or type error found.
        """

        errors: list[str] = []

        if not isinstance(data, dict):
            return ["Manifest root must be a mapping."]

        errors.extend(self._validate_required_keys(data))
        errors.extend(self._validate_fields(data))

        publication = data.get("publication")

        if isinstance(publication, dict):
            errors.extend(
                self._validate_publication(publication)
            )

        return errors

    def _validate_required_keys(
        self,
        data: dict[str, Any],
    ) -> list[str]:
        return [
            f"Missing required key: '{key}'."
            for key in sorted(self.REQUIRED_KEYS - data.keys())
        ]

    def _validate_fields(
        self,
        data: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []

        for field in (
            "album",
            "name_prefix",
            "description",
            "game",
        ):
            if field in data and not isinstance(data[field], str):
                errors.append(
                    f"'{field}' must be a string."
                )

        if "videos" in data:
            errors.extend(
                self._validate_string_list(
                    data["videos"],
                    "videos",
                )
            )

        if "playlists" in data:
            errors.extend(
                self._validate_string_list(
                    data["playlists"],
                    "playlists",
                )
            )

        if "tags" in data:
            tags = data["tags"]

            if tags is not None:
                errors.extend(
                    self._validate_string_list(
                        tags,
                        "tags",
                    )
                )

        if "thumbnail" in data:
            if (
                data["thumbnail"] is not None
                and not isinstance(data["thumbnail"], str)
            ):
                errors.append(
                    "'thumbnail' must be a string or null."
                )

        if "made_for_kids" in data:
            if not isinstance(data["made_for_kids"], bool):
                errors.append(
                    "'made_for_kids' must be a boolean."
                )

        if "contains_synthetic_media" in data:
            if not isinstance(
                data["contains_synthetic_media"],
                bool,
            ):
                errors.append(
                    "'contains_synthetic_media' must be a boolean."
                )

        if "publication" in data:
            if not isinstance(data["publication"], dict):
                errors.append(
                    "'publication' must be a mapping."
                )

        return errors

    def _validate_publication(
        self,
        publication: dict[str, Any],
    ) -> list[str]:
        errors: list[str] = []

        errors.extend(
            f"Missing required key: 'publication.{key}'."
            for key in sorted(
                self.PUBLICATION_REQUIRED_KEYS
                - publication.keys()
            )
        )

        if "first_publish_at" in publication:
            value = publication["first_publish_at"]

            if not isinstance(value, str):
                errors.append(
                    "'publication.first_publish_at' "
                    "must be a string."
                )
            else:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    errors.append(
                        "'publication.first_publish_at' "
                        "must be a valid ISO 8601 datetime."
                    )

        if "interval_days" in publication:
            value = publication["interval_days"]

            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(
                    "'publication.interval_days' "
                    "must be an integer."
                )

        return errors

    @staticmethod
    def _validate_string_list(
        value: Any,
        field: str,
    ) -> list[str]:
        errors: list[str] = []

        if not isinstance(value, list):
            return [f"'{field}' must be a list."]

        for index, item in enumerate(value):
            if not isinstance(item, str):
                errors.append(
                    f"'{field}[{index}]' must be a string."
                )

        return errors