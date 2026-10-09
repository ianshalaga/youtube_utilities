"""Tests for the Video Music application processor."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from applications.video_music import processor as processor_module
from applications.video_music.input import VideoMusicInput
from applications.video_music.output import TrackStatus
from applications.video_music.processor import VideoMusicProcessor


class FakeAudioConverter:
    """Creates a temporary audio file without invoking ffmpeg."""

    def __init__(self, failing_stems: set[str] | None = None) -> None:
        self.failing_stems = failing_stems or set()

    def convert(self, *, src: Path, dst_dir: Path) -> Path:
        if src.stem in self.failing_stems:
            raise RuntimeError(f"Conversion failed for {src.name}")

        converted_path = dst_dir / f"{src.stem}.converted.wav"
        converted_path.write_bytes(b"fake audio")
        return converted_path


class FakeFFProbeProvider:
    def duration(self, path: Path) -> float:
        assert path.exists()
        return 12.5


class FakeMKVMergeRunner:
    """Simulates mkvmerge by creating the requested output file."""

    def run(self, command: list[str]) -> None:
        output_path = Path(command[command.index("-o") + 1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake video")


@pytest.fixture
def processor_factory(monkeypatch):
    """Build a processor with fake external dependencies."""

    monkeypatch.setattr(
        processor_module,
        "ConfigManager",
        lambda: SimpleNamespace(
            audio_supported_extensions={".mp3", ".wav", ".flac"},
            paths_mkvmerge="mkvmerge",
        ),
    )

    def create(*, failing_stems: set[str] | None = None):
        console = MagicMock()
        processor = VideoMusicProcessor(
            mkvmerge_runner=FakeMKVMergeRunner(),
            audio_converter=FakeAudioConverter(failing_stems),
            ffprobe_provider=FakeFFProbeProvider(),
            console=console,
        )
        return processor, console

    return create


def make_input(
    tmp_path: Path,
    *,
    max_items_per_dir: int = 10,
    video_exists: bool = True,
) -> VideoMusicInput:
    video_path = tmp_path / "base_video.mp4"
    if video_exists:
        video_path.write_bytes(b"fake video")

    audios_dir = tmp_path / "audios"
    audios_dir.mkdir(exist_ok=True)

    return VideoMusicInput(
        max_items_per_dir=max_items_per_dir,
        audios_dir=audios_dir,
        video_path=video_path,
        output_dir=tmp_path / "output",
    )


def set_discovered_audio_files(monkeypatch, audio_files: list[Path]) -> None:
    monkeypatch.setattr(
        processor_module.MediaDiscoveryService,
        "discover",
        staticmethod(lambda _directory, _extensions: audio_files),
    )


def make_audio_files(directory: Path, names: tuple[str, ...]) -> list[Path]:
    paths = []
    for name in names:
        path = directory / name
        path.write_bytes(b"fake audio source")
        paths.append(path)
    return paths


def test_process_rejects_non_positive_max_items_per_dir(
    tmp_path: Path,
    processor_factory,
) -> None:
    processor, _ = processor_factory()
    input_data = make_input(tmp_path, max_items_per_dir=0)

    with pytest.raises(ValueError, match="max_items_per_dir"):
        processor.process(input_data)


def test_process_rejects_missing_video(
    tmp_path: Path,
    processor_factory,
) -> None:
    processor, _ = processor_factory()
    input_data = make_input(tmp_path, video_exists=False)

    with pytest.raises(FileNotFoundError):
        processor.process(input_data)


def test_process_rejects_empty_audio_discovery(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, _ = processor_factory()
    input_data = make_input(tmp_path)
    set_discovered_audio_files(monkeypatch, [])

    with pytest.raises(ValueError, match="No se encontraron archivos de audio"):
        processor.process(input_data)


def test_process_returns_track_results_and_cleans_temporary_audio(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, console = processor_factory()
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("01-first.mp3", "02-second.flac"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)

    result = processor.process(input_data)

    assert result.output_dir == input_data.output_dir
    assert result.total_tracks == 2
    assert result.total_directories == 1
    assert result.processed_tracks == 2
    assert result.failed_tracks == 0
    assert [track.source_path for track in result.tracks] == audio_files
    assert all(track.status is TrackStatus.COMPLETED for track in result.tracks)
    assert all(track.duration_seconds == pytest.approx(12.5) for track in result.tracks)
    assert all(track.output_path is not None for track in result.tracks)
    assert all(track.output_path.exists() for track in result.tracks)
    assert not list(input_data.output_dir.glob("*.converted.wav"))
    console.job_completed.assert_called_once_with(2, input_data.output_dir)


def test_process_partitions_outputs_when_track_limit_is_exceeded(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, console = processor_factory()
    input_data = make_input(tmp_path, max_items_per_dir=2)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("01-first.mp3", "02-second.mp3", "03-third.mp3"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)

    result = processor.process(input_data)

    assert result.total_tracks == 3
    assert result.total_directories == 2
    assert result.processed_tracks == 3
    assert [track.source_path for track in result.tracks] == audio_files
    assert [track.output_path.parent.name for track in result.tracks] == [
        "1",
        "1",
        "2",
    ]
    console.partition_started.assert_called_once_with(
        total_tracks=3,
        max_items_per_dir=2,
        total_directories=2,
    )


def test_process_records_track_failure_and_continues_other_tracks(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, console = processor_factory(failing_stems={"02-bad"})
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("01-good.mp3", "02-bad.mp3", "03-also-good.mp3"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)

    result = processor.process(input_data)

    assert result.total_tracks == 3
    assert result.processed_tracks == 2
    assert result.failed_tracks == 1
    assert [track.status for track in result.tracks] == [
        TrackStatus.COMPLETED,
        TrackStatus.FAILED,
        TrackStatus.COMPLETED,
    ]
    failed_track = result.tracks[1]
    assert failed_track.source_path == audio_files[1]
    assert failed_track.output_path is None
    assert "Conversion failed" in failed_track.error_message
    console.track_failed.assert_called_once()
    console.job_completed.assert_called_once_with(3, input_data.output_dir)
