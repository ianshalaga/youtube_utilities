from io import StringIO
from pathlib import Path

from rich.console import Console

from applications.video_joiner.console import VideoJoinerConsole


def test_console_renders_progress_and_completion_summary(tmp_path: Path) -> None:
    output = StringIO()
    console = VideoJoinerConsole(
        Console(file=output, width=120, color_system=None),
    )
    videos_dir = tmp_path / "videos"
    output_dir = tmp_path / "output"
    output_path = output_dir / "Compilation.mkv"
    timestamps_path = output_dir / "Compilation.txt"

    console.job_started(
        videos_dir=videos_dir,
        output_dir=output_dir,
        total_videos=2,
        total_parts=1,
        target_duration=None,
    )
    console.part_started(
        index=1,
        total_parts=1,
        videos=[videos_dir / "01-first.mp4", videos_dir / "02-second.mp4"],
        output_path=output_path,
    )
    console.part_completed(
        index=1,
        total_parts=1,
        output_path=output_path,
        timestamps_path=timestamps_path,
    )
    console.job_completed(total_parts=1, output_dir=output_dir)

    rendered = output.getvalue()
    assert "VIDEO JOINER" in rendered
    assert "UNIENDO VÍDEOS" in rendered
    assert "Completada" in rendered
    assert "PROCESAMIENTO COMPLETADO" in rendered
    assert console._parts[1]["output"] == str(output_path)
    assert console._parts[1]["timestamps"] == str(timestamps_path)


def test_console_renders_part_and_job_failure(tmp_path: Path) -> None:
    output = StringIO()
    console = VideoJoinerConsole(
        Console(file=output, width=120, color_system=None),
    )
    videos_dir = tmp_path / "videos"
    output_dir = tmp_path / "output"
    error = RuntimeError("No se pudo unir la parte")

    console.job_started(
        videos_dir=videos_dir,
        output_dir=output_dir,
        total_videos=1,
        total_parts=1,
        target_duration=600,
    )
    console.part_started(
        index=1,
        total_parts=1,
        videos=[videos_dir / "01-first.mp4"],
        output_path=output_dir / "Compilation.mkv",
    )
    console.part_failed(
        index=1,
        total_parts=1,
        output_path=output_dir / "Compilation.mkv",
        error=error,
    )
    console.job_failed(error)

    rendered = output.getvalue()
    assert "Fallida" in rendered
    assert "PROCESAMIENTO FALLIDO" in rendered
    assert str(error) in rendered
