from io import StringIO
from pathlib import Path

from rich.console import Console

from applications.video_music.output import (
    TrackStatus,
    VideoMusicResult,
    VideoMusicTrackResult,
)
from interfaces.cli.presenters.video_music_result_presenter import (
    VideoMusicResultPresenter,
)


def make_console() -> tuple[Console, StringIO]:
    output = StringIO()
    console = Console(
        file=output,
        force_terminal=False,
        color_system=None,
        width=140,
    )
    return console, output


def test_display_shows_execution_summary() -> None:
    console, output = make_console()
    presenter = VideoMusicResultPresenter(console=console)
    result = VideoMusicResult(
        output_dir=Path("output/videos"),
        total_tracks=3,
        tracks=(
            VideoMusicTrackResult(
                source_path=Path("audio/track_01.mp3"),
                output_path=Path("output/videos/track_01.mp4"),
                status=TrackStatus.COMPLETED,
                duration_seconds=125.5,
            ),
            VideoMusicTrackResult(
                source_path=Path("audio/track_02.mp3"),
                output_path=None,
                status=TrackStatus.FAILED,
                error_message="Audio conversion failed",
            ),
            VideoMusicTrackResult(
                source_path=Path("audio/track_03.mp3"),
                output_path=Path("output/videos/track_03.mp4"),
                status=TrackStatus.COMPLETED,
                duration_seconds=90.0,
            ),
        ),
        total_directories=2,
    )

    presenter.display(result)
    rendered = output.getvalue()
    normalized_rendered = rendered.replace("\\", "/")

    assert "Video Music — Execution Summary" in rendered
    assert "output/videos" in normalized_rendered
    assert "Total tracks" in rendered
    assert "3" in rendered
    assert "Processed tracks" in rendered
    assert "2" in rendered
    assert "Failed tracks" in rendered
    assert "Output directories" in rendered


def test_display_shows_track_details_and_statuses() -> None:
    console, output = make_console()
    presenter = VideoMusicResultPresenter(console=console)
    result = VideoMusicResult(
        output_dir=Path("output"),
        total_tracks=2,
        tracks=(
            VideoMusicTrackResult(
                source_path=Path("track_ok.mp3"),
                output_path=Path("output/track_ok.mp4"),
                status=TrackStatus.COMPLETED,
                duration_seconds=12.34,
            ),
            VideoMusicTrackResult(
                source_path=Path("track_bad.mp3"),
                output_path=None,
                status=TrackStatus.FAILED,
                error_message="Unsupported format",
            ),
        ),
        total_directories=1,
    )

    presenter.display(result)
    rendered = output.getvalue()
    normalized_rendered = rendered.replace("\\", "/")

    assert "Track Details" in rendered
    assert "track_ok.mp3" in rendered
    assert "track_bad.mp3" in rendered
    assert "COMPLETED" in rendered
    assert "FAILED" in rendered
    assert "12.34 s" in rendered
    assert "output/track_ok.mp4" in normalized_rendered
    assert "Unsupported format" in rendered


def test_display_uses_placeholders_for_missing_optional_values() -> None:
    console, output = make_console()
    presenter = VideoMusicResultPresenter(console=console)
    result = VideoMusicResult(
        output_dir=Path("output"),
        total_tracks=1,
        tracks=(
            VideoMusicTrackResult(
                source_path=Path("track_failed.mp3"),
                output_path=None,
                status=TrackStatus.FAILED,
                duration_seconds=None,
                error_message=None,
            ),
        ),
        total_directories=1,
    )

    presenter.display(result)
    rendered = output.getvalue()

    assert "track_failed.mp3" in rendered
    assert "FAILED" in rendered
    assert "—" in rendered


def test_display_handles_result_without_tracks() -> None:
    console, output = make_console()
    presenter = VideoMusicResultPresenter(console=console)
    result = VideoMusicResult(
        output_dir=Path("output"),
        total_tracks=0,
        tracks=(),
        total_directories=0,
    )

    presenter.display(result)
    rendered = output.getvalue()

    assert "Video Music — Execution Summary" in rendered
    assert "No track details are available." in rendered
    assert "Track Details" not in rendered
