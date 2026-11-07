from __future__ import annotations

import re
from typing import Any

from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo
from services.youtube.api.methods import YouTubeMethods


class YouTubeDiscovery:
    """Discover the current album videos uploaded to YouTube."""

    _VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

    def __init__(self, methods: YouTubeMethods) -> None:
        self._methods = methods

    def discover(
        self,
        expected_video_titles: tuple[str, ...],
    ) -> tuple[YouTubeVideo, ...]:
        """Discover the YouTube videos that correspond to the expected titles.

        Numbered videos are matched by their numeric prefix. Compilation
        videos are matched by their complete title. The uploads playlist is
        scanned using up to three maxResults configurations. Each subsequent
        configuration starts again from the beginning of the playlist and
        accumulates only videos that have not already been found.
        """

        if not expected_video_titles:
            raise ValueError("expected_video_titles must not be empty.")

        expected_numbered_titles: dict[str, str] = {}
        expected_compilation_titles: set[str] = set()

        for title in expected_video_titles:
            number = self._extract_number_prefix(title)

            if number is None:
                expected_compilation_titles.add(title)
            else:
                expected_numbered_titles[number] = title

        uploads_playlist_id = self._get_uploads_playlist_id()

        videos: list[YouTubeVideo] = []
        found_numbers: set[str] = set()
        found_compilations: set[str] = set()

        max_results_values = self._build_max_results_strategy()

        for max_results in max_results_values:
            page_token: str | None = None
            required_pages = (
                len(expected_video_titles) + max_results - 1
            ) // max_results

            for _ in range(required_pages):
                response = self._methods.playlist_items_list(
                    playlist_id=uploads_playlist_id,
                    page_token=page_token,
                    max_results=max_results,
                )

                for item in response.get("items", []):
                    video = self._map_video(item)

                    if video.privacy_status is not PrivacyStatus.PRIVATE:
                        continue

                    number = self._extract_number_prefix(video.title)

                    if number is not None:
                        if number not in expected_numbered_titles:
                            continue

                        if number in found_numbers:
                            continue

                        found_numbers.add(number)
                        videos.append(video)
                    else:
                        if video.title not in expected_compilation_titles:
                            continue

                        if video.title in found_compilations:
                            continue

                        found_compilations.add(video.title)
                        videos.append(video)

                if (
                    len(found_numbers) == len(expected_numbered_titles)
                    and len(found_compilations)
                    == len(expected_compilation_titles)
                ):
                    return tuple(videos)

                page_token = response.get("nextPageToken")

                if page_token is None:
                    break

        missing_titles = [
            title
            for title in expected_video_titles
            if not self._is_expected_video_found(
                title,
                found_numbers,
                found_compilations,
            )
        ]

        raise MissingYouTubeVideosError(
            discovered_videos=tuple(videos),
            missing_titles=tuple(missing_titles),
            message=(
                "Not all expected YouTube videos were discovered after "
                f"{len(max_results_values)} pagination strategies. "
                f"Missing: {', '.join(missing_titles)}."
            ),
        )

    def discover_by_video_ids(
        self,
        expected_titles: tuple[str, ...],
        video_ids_by_title: dict[str, str],
    ) -> tuple[tuple[YouTubeVideo, ...], tuple[str, ...]]:
        """Resolve missing manifest videos directly by their configured IDs.

        Numbered videos are accepted only when the numeric prefix returned by
        YouTube matches the prefix in the manifest title.
        """
        expected_ids = {
            title: video_ids_by_title[title]
            for title in expected_titles
            if title in video_ids_by_title
            and self._VIDEO_ID_PATTERN.fullmatch(
                video_ids_by_title[title]
            )
        }
        videos_by_id: dict[str, YouTubeVideo] = {}
        ids = list(dict.fromkeys(expected_ids.values()))

        for start in range(0, len(ids), 50):
            response = self._methods.videos_list(
                video_ids=ids[start : start + 50]
            )
            for item in response.get("items", []):
                video_id = item.get("id")
                snippet = item.get("snippet", {})
                status = item.get("status", {})
                if (
                    not video_id
                    or status.get("privacyStatus") != PrivacyStatus.PRIVATE.value
                ):
                    continue
                videos_by_id[video_id] = YouTubeVideo(
                    video_id=video_id,
                    title=snippet["title"],
                    description=snippet.get("description"),
                    privacy_status=PrivacyStatus.PRIVATE,
                )

        resolved: list[YouTubeVideo] = []
        unresolved: list[str] = []
        for title in expected_titles:
            video_id = expected_ids.get(title)
            video = videos_by_id.get(video_id) if video_id else None
            expected_number = self._extract_number_prefix(title)
            actual_number = (
                self._extract_number_prefix(video.title)
                if video is not None
                else None
            )

            if video is None or (
                expected_number is not None
                and actual_number != expected_number
            ):
                unresolved.append(title)
                continue

            resolved.append(video)

        return tuple(resolved), tuple(unresolved)

    @staticmethod
    def _build_max_results_strategy() -> tuple[int, ...]:
        """Build maxResults values using the two-thirds rule."""

        values = [50]

        for _ in range(2):
            next_value = (values[-1] * 2 + 2) // 3
            values.append(next_value)

        return tuple(values)

    @staticmethod
    def _extract_number_prefix(title: str) -> str | None:
        """Return the leading numeric prefix from a video title."""

        number = ""
        for character in title:
            if not character.isdigit():
                break
            number += character

        return number or None

    @staticmethod
    def _is_expected_video_found(
        title: str,
        found_numbers: set[str],
        found_compilations: set[str],
    ) -> bool:
        """Return whether an expected title has already been discovered."""

        number = YouTubeDiscovery._extract_number_prefix(title)

        if number is None:
            return title in found_compilations

        return number in found_numbers

    def _get_uploads_playlist_id(self) -> str:
        """Return the authenticated user's uploads playlist ID."""

        response = self._methods.channels_list()

        items = response.get("items", [])

        if not items:
            raise RuntimeError("Authenticated YouTube channel was not found.")

        playlist_id = (
            items[0]
            .get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
        )

        if not playlist_id:
            raise RuntimeError("YouTube uploads playlist was not found.")

        return playlist_id

    @staticmethod
    def _map_video(item: dict[str, Any]) -> YouTubeVideo:
        """Create a YouTubeVideo from a playlist item."""

        content_details = item.get("contentDetails", {})
        snippet = item.get("snippet", {})
        status = item.get("status", {})

        return YouTubeVideo(
            video_id=content_details["videoId"],
            title=snippet["title"],
            description=snippet.get("description"),
            privacy_status=PrivacyStatus(status["privacyStatus"]),
        )


class MissingYouTubeVideosError(RuntimeError):
    """Raised when uploads playlist discovery leaves expected titles missing."""

    def __init__(
        self,
        *,
        discovered_videos: tuple[YouTubeVideo, ...],
        missing_titles: tuple[str, ...],
        message: str,
    ) -> None:
        super().__init__(message)
        self.discovered_videos = discovered_videos
        self.missing_titles = missing_titles
