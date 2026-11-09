from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from applications.video_joiner import processor as processor_module
from applications.video_joiner.processor import VideoJoinerProcessor


class FakeMKVMergeRunner:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error

    def run(self, command: list[str]) -> None:
        if self.error is not None:
            raise self.error

        output_path = Path(command[command.index("-o") + 1])
        output_path.write_bytes(b"joined video")


@pytest.fixture
def processor_factory(monkeypatch):
    monkeypatch.setattr(
        processor_module,
        "ConfigManager",
        lambda: SimpleNamespace(
            video_supported_extensions={"mp4"},
            paths_mkvmerge="mkvmerge",
            video_joiner_max_items_per_dir=2,
        ),
    )

    class NoOpValidator:
        def __init__(self, _provider) -> None:
            pass

        def validate(self, _videos) -> None:
            pass

    monkeypatch.setattr(
        processor_module,
        "VideoCompatibilityValidator",
        NoOpValidator,
    )

    def create(tmp_path: Path, *, error: Exception | None = None):
        console = Mock()
        processor = VideoJoinerProcessor(
            mkvmerge_runner=FakeMKVMergeRunner(error),
            ffprobe_provider=Mock(),
            max_items_per_dir=2,
            console=console,
        )
        monkeypatch.setattr(
            processor._timestamp_builder,
            "build",
            lambda **kwargs: kwargs["output_path"].write_text(
                "timestamps",
                encoding="utf-8",
            ),
        )
        return processor, console

    return create


def make_video_inputs(tmp_path: Path) -> tuple[Path, Path, list[Path]]:
    videos_dir = tmp_path / "videos"
    videos_dir.mkdir()
    videos = [videos_dir / "01-first.mp4", videos_dir / "02-second.mp4"]
    for video in videos:
        video.write_bytes(b"fake video")
    return videos_dir, tmp_path / "output", videos


def test_process_reports_job_and_part_events_on_success(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    processor, console = processor_factory(tmp_path)
    videos_dir, output_dir, videos = make_video_inputs(tmp_path)
    monkeypatch.setattr(
        processor_module.MediaDiscoveryService,
        "discover",
        staticmethod(lambda _directory, _extensions: videos),
    )

    processor.process(videos_dir, output_dir, "Compilation")

    console.job_started.assert_called_once_with(
        videos_dir=videos_dir,
        output_dir=output_dir,
        total_videos=2,
        total_parts=1,
        target_duration=None,
    )
    console.part_started.assert_called_once_with(
        index=1,
        total_parts=1,
        videos=videos,
        output_path=output_dir / "Compilation.mkv",
    )
    console.part_completed.assert_called_once_with(
        index=1,
        total_parts=1,
        output_path=output_dir / "Compilation.mkv",
        timestamps_path=output_dir / "Compilation.txt",
    )
    console.job_completed.assert_called_once_with(1, output_dir)
    console.part_failed.assert_not_called()
    console.job_failed.assert_not_called()
    assert (output_dir / "Compilation.mkv").is_file()
    assert (output_dir / "Compilation.txt").is_file()


def test_process_reports_part_and_job_failure(
    tmp_path: Path,
    monkeypatch,
    processor_factory,
) -> None:
    error = RuntimeError("mkvmerge failed")
    processor, console = processor_factory(tmp_path, error=error)
    videos_dir, output_dir, videos = make_video_inputs(tmp_path)
    monkeypatch.setattr(
        processor_module.MediaDiscoveryService,
        "discover",
        staticmethod(lambda _directory, _extensions: videos),
    )

    with pytest.raises(RuntimeError, match="mkvmerge failed"):
        processor.process(videos_dir, output_dir, "Compilation")

    console.part_failed.assert_called_once_with(
        index=1,
        total_parts=1,
        output_path=output_dir / "Compilation.mkv",
        error=error,
    )
    console.job_failed.assert_called_once_with(error)
    console.job_completed.assert_not_called()
