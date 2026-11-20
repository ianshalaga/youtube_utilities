from pathlib import Path

from services.media.discovery.media_discovery import MediaDiscoveryService


def test_discover_normalizes_configured_extensions(tmp_path: Path) -> None:
    mp3_file = tmp_path / "track.mp3"
    flac_file = tmp_path / "track.flac"
    wav_file = tmp_path / "track.wav"
    unsupported_file = tmp_path / "track.ogg"

    for path in (mp3_file, flac_file, wav_file, unsupported_file):
        path.touch()

    result = MediaDiscoveryService.discover(
        tmp_path,
        [" MP3 ", ".FLAC", "..wav"],
    )

    assert result == [flac_file, mp3_file, wav_file]
