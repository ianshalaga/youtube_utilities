from datetime import datetime

import pytest

from services.youtube.album_manifest.album_manifest_validator import (
    AlbumManifestValidator,
)


@pytest.fixture
def validator() -> AlbumManifestValidator:
    return AlbumManifestValidator()


def test_validates_publication_timezone(validator):
    errors = validator.validate(
        {
            "album": "Test Album",
            "name_prefix": "Test Album",
            "videos": ["Song One"],
            "description": "Description",
            "thumbnail": None,
            "playlists": [],
            "made_for_kids": False,
            "contains_synthetic_media": False,
            "tags": None,
            "game": "Test Game",
            "publication": {
                "first_publish_at": "2026-11-11T09:00:00",
                "timezone": "Europe/Paris",
                "interval_days": 1,
            },
        }
    )

    assert errors == []


def test_rejects_missing_publication_timezone(validator):
    errors = validator.validate(
        {
            "publication": {
                "first_publish_at": "2026-11-11T09:00:00",
                "interval_days": 1,
            }
        }
    )

    assert "Missing required key: 'publication.timezone'." in errors


def test_rejects_non_string_publication_timezone(validator):
    errors = validator.validate(
        {
            "publication": {
                "first_publish_at": "2026-11-11T09:00:00",
                "timezone": 123,
                "interval_days": 1,
            }
        }
    )

    assert "'publication.timezone' must be a string." in errors


def test_rejects_invalid_publication_timezone(validator):
    errors = validator.validate(
        {
            "publication": {
                "first_publish_at": "2026-11-11T09:00:00",
                "timezone": "Invalid/Timezone",
                "interval_days": 1,
            }
        }
    )

    assert (
        "'publication.timezone' must be a valid IANA timezone."
        in errors
    )


def test_rejects_timezone_offset_in_first_publish_at(validator):
    errors = validator.validate(
        {
            "publication": {
                "first_publish_at": "2026-11-11T09:00:00+01:00",
                "timezone": "Europe/Paris",
                "interval_days": 1,
            }
        }
    )

    assert (
        "'publication.first_publish_at' "
        "must not include a timezone offset."
    ) in errors


def test_rejects_invalid_first_publish_at(validator):
    errors = validator.validate(
        {
            "publication": {
                "first_publish_at": "not-a-datetime",
                "timezone": "Europe/Paris",
                "interval_days": 1,
            }
        }
    )

    assert (
        "'publication.first_publish_at' "
        "must be a valid ISO 8601 datetime."
    ) in errors


def test_reports_missing_timezone_and_invalid_interval_together(validator):
    errors = validator.validate(
        {
            "publication": {
                "first_publish_at": "2026-11-11T09:00:00",
                "interval_days": "1",
            }
        }
    )

    assert "Missing required key: 'publication.timezone'." in errors
    assert (
        "'publication.interval_days' must be an integer."
    ) in errors
