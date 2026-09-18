from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from textwrap import dedent

import pytest

from domain.youtube.publication_settings import PublicationSettings
from services.youtube.album_manifest.exceptions import (
    ManifestConfigurationError,
    ManifestParseError,
)
from services.youtube.album_manifest.yaml_reader import YamlReader


def test_yaml_reader_reads_valid_manifest(tmp_path):
    reader = YamlReader()

    manifest_content = dedent(
        """
        album: "Test Album"
        name_prefix: "Test Album"
        videos:
          - "Song One"
          - "Song Two"
        description: "Test album description."
        thumbnail: "C:/test/thumbnail.jpg"
        playlists:
          - "PL_TEST_001"
          - "PL_TEST_002"
        made_for_kids: false
        contains_synthetic_media: false
        tags:
          - "test"
          - "album"
        game: "Test Game"
        publication:
          first_publish_at: "2026-11-11T02:00:00"
          timezone: "Europe/Paris"
          interval_days: 1
        """
    )

    manifest_path = tmp_path / "test_manifest.yaml"
    manifest_path.write_text(manifest_content, encoding="utf-8")

    manifest = reader.read(manifest_path)

    assert manifest.name == "Test Album"
    assert manifest.name_prefix == "Test Album"
    assert manifest.videos == ("Song One", "Song Two")
    assert manifest.description == "Test album description."
    assert manifest.thumbnail == Path("C:/test/thumbnail.jpg")
    assert manifest.playlists == ("PL_TEST_001", "PL_TEST_002")
    assert manifest.made_for_kids is False
    assert manifest.contains_synthetic_media is False
    assert manifest.tags == ("test", "album")
    assert manifest.game == "Test Game"

    assert manifest.publication.first_publish_at == datetime(
        2026,
        11,
        11,
        2,
        0,
        tzinfo=ZoneInfo("Europe/Paris"),
    )
    assert manifest.publication.timezone == ZoneInfo("Europe/Paris")
    assert manifest.publication.interval_days == 1

    assert isinstance(manifest.thumbnail, Path)
    assert isinstance(manifest.publication.first_publish_at, datetime)
    assert isinstance(manifest.publication, PublicationSettings)


def test_yaml_reader_rejects_invalid_yaml(tmp_path):
    reader = YamlReader()

    invalid_yaml = dedent(
        """
        album: "Test Album"
          invalid indentation
        """
    )

    manifest_path = tmp_path / "invalid.yaml"
    manifest_path.write_text(invalid_yaml, encoding="utf-8")

    with pytest.raises(ManifestParseError):
        reader.read(manifest_path)


def test_yaml_reader_rejects_invalid_configuration(tmp_path):
    reader = YamlReader()

    invalid_configuration = dedent(
        """
        album: "Test Album"
        """
    )

    manifest_path = tmp_path / "invalid_configuration.yaml"
    manifest_path.write_text(
        invalid_configuration,
        encoding="utf-8",
    )

    with pytest.raises(ManifestConfigurationError):
        reader.read(manifest_path)

def test_yaml_reader_rejects_missing_publication_timezone(tmp_path):
    reader = YamlReader()

    manifest_content = dedent(
        """
        album: "Test Album"
        name_prefix: "Test Album"
        videos:
          - "Song One"
        description: "Test album description."
        thumbnail: null
        playlists: []
        made_for_kids: false
        contains_synthetic_media: false
        tags: null
        game: "Test Game"
        publication:
          first_publish_at: "2026-11-11T02:00:00"
          interval_days: 1
        """
    )

    manifest_path = tmp_path / "missing_timezone.yaml"
    manifest_path.write_text(manifest_content, encoding="utf-8")

    with pytest.raises(ManifestConfigurationError):
        reader.read(manifest_path)


def test_yaml_reader_rejects_invalid_publication_timezone(tmp_path):
    reader = YamlReader()

    manifest_content = dedent(
        """
        album: "Test Album"
        name_prefix: "Test Album"
        videos:
          - "Song One"
        description: "Test album description."
        thumbnail: null
        playlists: []
        made_for_kids: false
        contains_synthetic_media: false
        tags: null
        game: "Test Game"
        publication:
          first_publish_at: "2026-11-11T02:00:00"
          timezone: "Invalid/Timezone"
          interval_days: 1
        """
    )

    manifest_path = tmp_path / "invalid_timezone.yaml"
    manifest_path.write_text(manifest_content, encoding="utf-8")

    with pytest.raises(ManifestConfigurationError):
        reader.read(manifest_path)


def test_yaml_reader_rejects_non_string_publication_timezone(tmp_path):
    reader = YamlReader()

    manifest_content = dedent(
        """
        album: "Test Album"
        name_prefix: "Test Album"
        videos:
          - "Song One"
        description: "Test album description."
        thumbnail: null
        playlists: []
        made_for_kids: false
        contains_synthetic_media: false
        tags: null
        game: "Test Game"
        publication:
          first_publish_at: "2026-11-11T02:00:00"
          timezone: 123
          interval_days: 1
        """
    )

    manifest_path = tmp_path / "non_string_timezone.yaml"
    manifest_path.write_text(manifest_content, encoding="utf-8")

    with pytest.raises(ManifestConfigurationError):
        reader.read(manifest_path)
