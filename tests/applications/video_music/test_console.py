from pathlib import Path

from rich.console import Console

from applications.video_music.console import VideoMusicConsole


def test_console_displays_named_pending_tracks_and_keeps_completed_last(
    tmp_path: Path,
) -> None:
    output = Console(record=True, width=140)
    video_music_console = VideoMusicConsole(console=output)
    audio_files = [
        tmp_path / "audio" / f"track_{index:02d}.flac"
        for index in range(1, 14)
    ]

    video_music_console.job_started(
        video_path=tmp_path / "base.mkv",
        audios_dir=tmp_path / "audio",
        output_dir=tmp_path / "output",
        audio_files=audio_files,
        total_tracks=len(audio_files),
        max_items_per_dir=10,
    )
    video_music_console.track_started(
        index=2,
        total=len(audio_files),
        audio_path=audio_files[1],
        output_dir=tmp_path / "output",
    )
    video_music_console.track_completed(
        index=2,
        total=len(audio_files),
        audio_path=audio_files[1],
    )
    output.print(video_music_console._render())

    rendered = output.export_text()

    assert "⏳" in rendered
    assert "PENDING" in rendered
    assert "track_01" in rendered
    assert "track_13" in rendered
    assert rendered.index("track_01") < rendered.index("track_13")
    assert rendered.index("track_13") < rendered.index("track_02")
