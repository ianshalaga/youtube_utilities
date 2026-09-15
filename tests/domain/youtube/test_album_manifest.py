# tests\domain\youtube\test_album_manifest.py

from datetime import datetime

from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.publication_settings import PublicationSettings


def test_album_manifest_creates_expected_values():
    manifest = AlbumManifest(
        name="Test Album",
        name_prefix="Test OST",
        videos=[
            "01 Opening Theme",
            "02 Battle Theme",
            "Test Compilation",
        ],
        description="Test album description",
        thumbnail=None,
        playlists=["PL_TEST"],
        made_for_kids=False,
        contains_synthetic_media=False,
        tags=None,
        game="Test Game",
        publication=PublicationSettings(
            first_publish_at=datetime(2026, 10, 1, 18, 0),
            interval_days=1,
        ),
    )

    assert manifest.name == "Test Album"
    assert manifest.name_prefix == "Test OST"
    assert manifest.videos == (
        "01 Opening Theme",
        "02 Battle Theme",
        "Test Compilation",
    )
    assert manifest.description == "Test album description"
    assert manifest.thumbnail is None
    assert manifest.playlists == ("PL_TEST",)
    assert manifest.made_for_kids is False
    assert manifest.contains_synthetic_media is False
    assert manifest.tags is None
    assert manifest.game == "Test Game"

    assert manifest.publication.first_publish_at == datetime(
        2026,
        10,
        1,
        18,
        0,
    )
    assert manifest.publication.interval_days == 1

    assert isinstance(manifest, AlbumManifest)
    assert isinstance(manifest.publication, PublicationSettings)