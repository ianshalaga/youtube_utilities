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
        self.calls: list[Path] = []

    def convert(self, *, src: Path, dst_dir: Path) -> Path:
        self.calls.append(src)
        if src.stem in self.failing_stems:
            raise RuntimeError(f"Conversion failed for {src.name}")

        converted_path = dst_dir / f"{src.stem}.converted.wav"
        converted_path.write_bytes(b"fake audio")
        return converted_path


class FakeFFProbeProvider:
    def __init__(
        self,
        video_duration_seconds: float = 30.0,
        audio_durations_by_name: dict[str, float] | None = None,
    ) -> None:
        self._video_duration_seconds = video_duration_seconds
        self._audio_durations_by_name = audio_durations_by_name or {}

    def duration(self, path: Path) -> float:
        assert path.exists()
        return self._audio_durations_by_name.get(path.name, 12.5)

    def video_duration(self, path: Path) -> float:
        assert path.exists()
        return self._video_duration_seconds


class FakeMKVMergeRunner:
    """Simulates mkvmerge by creating the requested output file."""

    def run(self, command: list[str]) -> None:
        output_path = Path(command[command.index("-o") + 1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake video")


class FakeSplittingMKVMergeRunner:
    """Simulates mkvmerge's numbered output when splitting a file."""

    def __init__(self) -> None:
        self.workspace_dirs: list[Path] = []

    def run(self, command: list[str]) -> None:
        output_path = Path(command[command.index("-o") + 1])
        self.workspace_dirs.append(output_path.parent)
        split_output_path = output_path.with_name(
            f"{output_path.stem}-001{output_path.suffix}"
        )
        split_output_path.write_text(
            Path(command[-1]).stem,
            encoding="utf-8",
        )


@pytest.fixture
def processor_factory():
    """Build a processor with fake external dependencies."""

    def create(
        *,
        failing_stems: set[str] | None = None,
        video_duration_seconds: float = 30.0,
        audio_durations_by_name: dict[str, float] | None = None,
    ):
        console = MagicMock()
        processor = VideoMusicProcessor(
            mkvmerge_runner=FakeMKVMergeRunner(),
            audio_converter=FakeAudioConverter(failing_stems),
            ffprobe_provider=FakeFFProbeProvider(
                video_duration_seconds,
                audio_durations_by_name,
            ),
            audio_supported_extensions={"mp3", "wav", "flac"},
            paths_mkvmerge="mkvmerge",
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


def test_process_rejects_audio_files_with_duplicate_stems(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, console = processor_factory()
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("theme.mp3", "theme.flac"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)

    with pytest.raises(ValueError, match="mismo nombre base") as error:
        processor.process(input_data)

    assert "theme.mp3" in str(error.value)
    assert "theme.flac" in str(error.value)
    assert not input_data.output_dir.exists()
    console.job_started.assert_not_called()


def test_process_clears_existing_output_before_creating_results(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, _ = processor_factory()
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(input_data.audios_dir, ("01-track.mp3",))
    set_discovered_audio_files(monkeypatch, audio_files)

    stale_directory = input_data.output_dir / "old-partition"
    stale_directory.mkdir(parents=True)
    stale_file = input_data.output_dir / "old-result.mkv"
    stale_file.write_bytes(b"old result")
    (stale_directory / "old-track.mkv").write_bytes(b"old result")

    result = processor.process(input_data)

    assert not stale_file.exists()
    assert not stale_directory.exists()
    assert result.tracks[0].output_path.is_file()


def test_process_isolates_split_segments_for_prefix_stems(
    tmp_path: Path,
    monkeypatch,
) -> None:
    console = MagicMock()
    mkvmerge_runner = FakeSplittingMKVMergeRunner()
    processor = VideoMusicProcessor(
        mkvmerge_runner=mkvmerge_runner,
        audio_converter=FakeAudioConverter(),
        ffprobe_provider=FakeFFProbeProvider(),
        audio_supported_extensions={"mp3", "wav", "flac"},
        paths_mkvmerge="mkvmerge",
        console=console,
    )
    input_data = make_input(tmp_path, max_items_per_dir=10)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("theme.mp3", "theme-001.wav"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)

    result = processor.process(input_data)

    assert [track.output_path.name for track in result.tracks] == [
        "theme.mkv",
        "theme-001.mkv",
    ]
    output_contents = [
        track.output_path.read_text(encoding="utf-8")
        for track in result.tracks
    ]
    assert output_contents == ["theme.converted", "theme-001.converted"]
    assert len(set(mkvmerge_runner.workspace_dirs)) == 2
    assert all(
        workspace_dir.parent == input_data.output_dir
        for workspace_dir in mkvmerge_runner.workspace_dirs
    )
    assert not list(input_data.output_dir.glob(".video_music-*"))


def test_process_places_workspaces_inside_their_output_partitions(
    tmp_path: Path,
    monkeypatch,
) -> None:
    mkvmerge_runner = FakeSplittingMKVMergeRunner()
    processor = VideoMusicProcessor(
        mkvmerge_runner=mkvmerge_runner,
        audio_converter=FakeAudioConverter(),
        ffprobe_provider=FakeFFProbeProvider(),
        audio_supported_extensions={"mp3", "wav", "flac"},
        paths_mkvmerge="mkvmerge",
        console=MagicMock(),
    )
    input_data = make_input(tmp_path, max_items_per_dir=1)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("01-first.mp3", "02-second.flac"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)

    result = processor.process(input_data)

    output_partitions = {
        track.output_path.parent
        for track in result.tracks
        if track.output_path is not None
    }
    workspace_partitions = {
        workspace_dir.parent
        for workspace_dir in mkvmerge_runner.workspace_dirs
    }

    assert output_partitions == {
        input_data.output_dir / "1",
        input_data.output_dir / "2",
    }
    assert workspace_partitions == output_partitions
    assert not list(input_data.output_dir.glob("**/.video_music-*"))


def test_process_rejects_output_directory_that_contains_source_audios(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, _ = processor_factory()
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(input_data.audios_dir, ("01-track.mp3",))
    set_discovered_audio_files(monkeypatch, audio_files)
    input_data = VideoMusicInput(
        max_items_per_dir=input_data.max_items_per_dir,
        audios_dir=input_data.audios_dir,
        video_path=input_data.video_path,
        output_dir=input_data.audios_dir,
    )

    with pytest.raises(ValueError, match="audios fuente"):
        processor.process(input_data)

    assert audio_files[0].exists()


def test_process_returns_track_results_and_cleans_temporary_audio(
    tmp_path: Path,
    processor_factory,
) -> None:
    processor, console = processor_factory()
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("01-first.mp3", "02-second.flac"),
    )

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


def test_process_rejects_batch_before_processing_when_audio_exceeds_video(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, console = processor_factory(
        video_duration_seconds=10.0,
        audio_durations_by_name={
            "short-track.mp3": 8.0,
            "long-track.flac": 12.5,
        },
    )
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(
        input_data.audios_dir,
        ("short-track.mp3", "long-track.flac"),
    )
    set_discovered_audio_files(monkeypatch, audio_files)
    input_data.output_dir.mkdir()
    previous_output = input_data.output_dir / "previous-result.mkv"
    previous_output.write_bytes(b"keep until preflight passes")

    with pytest.raises(ValueError, match="No se inició el procesamiento") as error:
        processor.process(input_data)

    assert "long-track.flac" in str(error.value)
    assert "short-track.mp3" not in str(error.value)
    assert "12.500 s" in str(error.value)
    assert "10.000 s" in str(error.value)
    assert processor._audio_converter.calls == []
    assert previous_output.read_bytes() == b"keep until preflight passes"
    assert not list(input_data.output_dir.glob("**/.video_music-*"))
    console.job_started.assert_not_called()


def test_process_allows_audio_matching_base_video_duration(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, _ = processor_factory(video_duration_seconds=12.5)
    input_data = make_input(tmp_path)
    audio_files = make_audio_files(input_data.audios_dir, ("same-length.mp3",))
    set_discovered_audio_files(monkeypatch, audio_files)

    result = processor.process(input_data)

    assert result.processed_tracks == 1
    assert result.failed_tracks == 0
    assert result.tracks[0].output_path.is_file()
