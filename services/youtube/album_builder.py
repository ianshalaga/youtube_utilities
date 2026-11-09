# services\youtube\album_builder.py

from __future__ import annotations

import re
from datetime import timedelta, datetime
from typing import Iterable

from domain.youtube.album import Album
from domain.youtube.album_manifest import AlbumManifest
from domain.youtube.video import Video, VideoType
from domain.youtube.video_metadata import VideoMetadata
from domain.youtube.youtube_video import YouTubeVideo


class AlbumBuildError(RuntimeError):
    """Raised when an Album cannot be built from the manifest and YouTube videos."""


class AlbumBuilder:
    """
    Builds an Album by combining the album manifest with discovered YouTube videos.

    The manifest defines the desired album configuration, while YouTubeDiscovery
    provides the YouTube-specific information required to identify each video.

    The resulting Album contains the complete desired configuration and can be
    passed to the planning phase.
    """

    _SONG_TITLE_PATTERN = re.compile(r"^(\d+)\s+(.+)$")

    def build(
        self,
        manifest: AlbumManifest,
        youtube_videos: tuple[YouTubeVideo, ...],
    ) -> Album:
        """
        Build an Album from an album manifest and discovered YouTube videos.

        YouTube videos may be returned in a different order from the manifest.
        Songs are matched by numeric prefix; unnumbered compilations are
        matched by exact title and emitted in their manifest order.

        Raises:
            AlbumBuildError: If the manifest and YouTube videos cannot be matched.
        """
        if not youtube_videos:
            raise AlbumBuildError(
                "No private YouTube videos were discovered."
            )

        manifest_songs, manifest_compilations = self._parse_manifest(manifest)

        youtube_songs, youtube_compilations = self._parse_youtube_videos(
            youtube_videos,
            expect_compilations=bool(manifest_compilations),
        )

        missing, extra = self._find_mismatches(
            manifest_songs=manifest_songs,
            manifest_compilations=manifest_compilations,
            youtube_songs=youtube_songs,
            youtube_compilations=youtube_compilations,
        )

        if missing or extra:
            raise AlbumBuildError(
                self._format_mismatch_error(
                    missing=missing,
                    extra=extra,
                )
            )

        videos = self._build_videos(
            manifest=manifest,
            manifest_songs=manifest_songs,
            manifest_compilations=manifest_compilations,
            youtube_songs=youtube_songs,
            youtube_compilations=youtube_compilations,
        )

        return Album(
            name=manifest.name,
            description=manifest.description,
            playlists=list(manifest.playlists),
            game=manifest.game,
            publication=manifest.publication,
            tags=list(manifest.tags) if manifest.tags is not None else None,
            thumbnail=manifest.thumbnail,
            videos=videos,
        )

    def _parse_manifest(
        self,
        manifest: AlbumManifest,
    ) -> tuple[dict[int, str], tuple[str, ...]]:
        songs: dict[int, str] = {}
        compilations: list[str] = []
        compilations_started = False

        for title in manifest.videos:
            match = self._SONG_TITLE_PATTERN.match(title)

            if match is None:
                if title in compilations:
                    raise AlbumBuildError(
                        f"Manifest contains duplicate compilation title {title!r}."
                    )

                compilations_started = True
                compilations.append(title)
                continue

            if compilations_started:
                raise AlbumBuildError(
                    "Manifest songs must appear before compilation videos."
                )

            position = int(match.group(1))

            if position in songs:
                raise AlbumBuildError(
                    f"Manifest contains duplicate song position {position}."
                )

            songs[position] = title

        return songs, tuple(compilations)

    def _parse_youtube_videos(
        self,
        youtube_videos: Iterable[YouTubeVideo],
        *,
        expect_compilations: bool,
    ) -> tuple[dict[int, YouTubeVideo], dict[str, YouTubeVideo]]:
        songs: dict[int, YouTubeVideo] = {}
        compilations: dict[str, YouTubeVideo] = {}

        for video in youtube_videos:
            match = self._SONG_TITLE_PATTERN.match(video.title)

            if match is None:
                if not expect_compilations:
                    continue

                if video.title in compilations:
                    raise AlbumBuildError(
                        "YouTube discovery contains duplicate compilation title "
                        f"{video.title!r}."
                    )

                compilations[video.title] = video
                continue

            position = int(match.group(1))

            if position in songs:
                raise AlbumBuildError(
                    "YouTube discovery contains duplicate song position "
                    f"{position}."
                )

            songs[position] = video

        return songs, compilations
    

    @staticmethod
    def _find_mismatches(
        manifest_songs: dict[int, str],
        manifest_compilations: tuple[str, ...],
        youtube_songs: dict[int, YouTubeVideo],
        youtube_compilations: dict[str, YouTubeVideo],
    ) -> tuple[list[str], list[str]]:
        missing: list[str] = []
        extra: list[str] = []

        manifest_positions = set(manifest_songs)
        youtube_positions = set(youtube_songs)

        for position in sorted(manifest_positions - youtube_positions):
            missing.append(manifest_songs[position])

        for position in sorted(youtube_positions - manifest_positions):
            extra.append(youtube_songs[position].title)

        manifest_compilation_titles = set(manifest_compilations)
        youtube_compilation_titles = set(youtube_compilations)

        missing.extend(
            title
            for title in manifest_compilations
            if title not in youtube_compilation_titles
        )
        extra.extend(
            title
            for title in youtube_compilations
            if title not in manifest_compilation_titles
        )

        return missing, extra

    @staticmethod
    def _format_mismatch_error(
        missing: list[str],
        extra: list[str],
    ) -> str:
        lines = ["Album videos do not match between manifest and YouTube."]

        if missing:
            lines.append("Missing from YouTube:")
            lines.extend(f"  {title}" for title in missing)

        if extra:
            lines.append("Extra on YouTube:")
            lines.extend(f"  {title}" for title in extra)

        return "\n".join(lines)

    def _build_videos(
        self,
        manifest: AlbumManifest,
        manifest_songs: dict[int, str],
        manifest_compilations: tuple[str, ...],
        youtube_songs: dict[int, YouTubeVideo],
        youtube_compilations: dict[str, YouTubeVideo],
    ) -> list[Video]:
        videos: list[Video] = []

        for position, (track_number, manifest_title) in enumerate(
            sorted(manifest_songs.items()),
            start=1,
        ):
            youtube_video = youtube_songs[track_number]

            metadata = self._build_song_metadata(
                manifest=manifest,
                manifest_title=manifest_title,
                position=position,
            )

            videos.append(
                Video(
                    video_id=youtube_video.video_id,
                    position=position,
                    video_type=VideoType.SONG,
                    metadata=metadata,
                )
            )

        for compilation_title in manifest_compilations:
            youtube_compilation = youtube_compilations[compilation_title]
            compilation_position = len(videos) + 1

            metadata = self._build_compilation_metadata(
                manifest=manifest,
                youtube_video=youtube_compilation,
                position=compilation_position,
            )

            videos.append(
                Video(
                    video_id=youtube_compilation.video_id,
                    position=compilation_position,
                    video_type=VideoType.COMPILATION,
                    metadata=metadata,
                )
            )

        return videos

    def _build_song_metadata(
        self,
        manifest: AlbumManifest,
        manifest_title: str,
        position: int,
    ) -> VideoMetadata:
        song_title = self._remove_position_prefix(manifest_title)

        desired_title = self._build_song_title(
            name_prefix=manifest.name_prefix,
            song_title=song_title,
        )

        publish_at = self._calculate_publish_at(
            manifest=manifest,
            position=position,
        )

        return VideoMetadata(
            title=desired_title,
            description=manifest.description,
            tags=list(manifest.tags) if manifest.tags is not None else None,
            playlists=list(manifest.playlists),
            game=manifest.game,
            made_for_kids=manifest.made_for_kids,
            contains_synthetic_media=manifest.contains_synthetic_media,
            publish_at=publish_at,
            thumbnail=manifest.thumbnail,
        )

    def _build_compilation_metadata(
        self,
        manifest: AlbumManifest,
        youtube_video: YouTubeVideo,
        position: int,
    ) -> VideoMetadata:
        current_description = youtube_video.description or ""

        combined_description = (
            f"{current_description}\n\n{manifest.description}"
        )

        if len(combined_description) > 5000:
            desired_description = current_description
        else:
            desired_description = combined_description

        publish_at = self._calculate_publish_at(
            manifest=manifest,
            position=position,
        )

        return VideoMetadata(
            title=youtube_video.title,
            description=desired_description,
            tags=list(manifest.tags) if manifest.tags is not None else None,
            playlists=list(manifest.playlists),
            game=manifest.game,
            made_for_kids=manifest.made_for_kids,
            contains_synthetic_media=manifest.contains_synthetic_media,
            publish_at=publish_at,
            thumbnail=manifest.thumbnail,
        )

    @classmethod
    def _build_song_title(
        cls,
        name_prefix: str,
        song_title: str,
    ) -> str:
        title = f"{name_prefix}: {song_title}"

        while len(title) > 100:
            last_space = title.rfind(" ")

            if last_space == -1:
                return title[:100]

            title = title[:last_space]

        return title

    @classmethod
    def _remove_position_prefix(cls, title: str) -> str:
        match = cls._SONG_TITLE_PATTERN.match(title)

        if match is None:
            raise AlbumBuildError(
                f"Song title does not contain a valid position: {title!r}."
            )

        return match.group(2)

    @staticmethod
    def _calculate_publish_at(
        manifest: AlbumManifest,
        position: int,
    ) -> datetime:
        publication = manifest.publication

        return publication.first_publish_at + timedelta(
            days=(position - 1) * publication.interval_days
        )
