from pathlib import Path
import sys
from math import ceil

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.youtube.api.client import YouTubeClient


CLIENT_SECRETS_PATH = Path(
    "F:/@Seyfer/Proyectos/youtube_utilities/"
    "config/youtube/client_secret.json"
)

TOKEN_PATH = Path(
    "F:/@Seyfer/Proyectos/youtube_utilities/"
    "config/youtube/token.json"
)


EXPECTED_VIDEO_IDS = {
    "EVtr5P0EdfM",  # 001
    "RQl40sSXN1Y",  # 002
    "2g77oey5nyE",  # 003
    "Ubxgr_myhWs",  # 004
    "isCKDehW44o",  # 005
    "Xww_JAJbhVY",  # 006
    "Rd_lv1wj4LM",  # 007
    "BV675i9EVQs",  # 008
    "GMU4ik2KalI",  # 009
    "En6Zr5tJ3H8",  # 010
    "0G4AuzIiKlw",  # 011
    "3W4BhDtYDOI",  # 012
}


INITIAL_MAX_RESULTS = 5
PAGINATION_PASSES = 3
MAX_PAGES = 20


def get_uploads_playlist_id(service) -> str:
    """Return the authenticated user's uploads playlist ID."""

    response = (
        service.channels()
        .list(
            part="contentDetails",
            mine=True,
        )
        .execute()
    )

    items = response.get("items", [])

    if not items:
        raise RuntimeError(
            "Authenticated YouTube channel was not found."
        )

    playlist_id = (
        items[0]
        .get("contentDetails", {})
        .get("relatedPlaylists", {})
        .get("uploads")
    )

    if not playlist_id:
        raise RuntimeError(
            "YouTube uploads playlist was not found."
        )

    return playlist_id


def lookup_expected_videos(
    service,
    playlist_id: str,
) -> dict[str, dict]:
    """Look up each expected video directly by videoId in the uploads playlist."""

    results: dict[str, dict] = {}

    print()
    print("=" * 70)
    print("DIRECT VIDEO-ID LOOKUP")
    print("=" * 70)

    for video_id in sorted(EXPECTED_VIDEO_IDS):
        response = (
            service.playlistItems()
            .list(
                part="snippet,contentDetails,status",
                playlistId=playlist_id,
                videoId=video_id,
            )
            .execute()
        )

        items = response.get("items", [])

        if not items:
            print(f"    {video_id}  NOT FOUND")
            continue

        if len(items) > 1:
            print(
                f"    {video_id}  WARNING: "
                f"{len(items)} playlist items returned"
            )

        item = items[0]
        snippet = item["snippet"]

        result = {
            "position": snippet["position"],
            "video_id": video_id,
            "title": snippet["title"],
        }
        results[video_id] = result

        print(
            f"    {video_id}  "
            f"position={result['position']:>5}  "
            f"title={result['title']!r}"
        )

    print()
    print(
        f"    Found directly: "
        f"{len(results)}/{len(EXPECTED_VIDEO_IDS)}"
    )

    return results


def compare_pagination_with_direct_lookup(
    pagination_items: list[dict],
    direct_results: dict[str, dict],
) -> None:
    """Compare positions returned by pagination with direct videoId lookup."""

    pagination_by_id = {
        item["video_id"]: item
        for item in pagination_items
        if item["video_id"] in EXPECTED_VIDEO_IDS
    }

    print()
    print("=" * 70)
    print("PAGINATION POSITIONS VS DIRECT VIDEO-ID POSITIONS")
    print("=" * 70)

    for video_id in sorted(EXPECTED_VIDEO_IDS):
        direct = direct_results.get(video_id)
        paginated = pagination_by_id.get(video_id)

        if direct is None:
            print(f"    {video_id}: direct lookup NOT FOUND")
            continue

        if paginated is None:
            print(
                f"    {video_id}: "
                f"direct={direct['position']} "
                f"pagination=NOT FOUND"
            )
            continue

        if paginated["position"] == direct["position"]:
            print(
                f"    {video_id}: "
                f"direct={direct['position']} "
                f"pagination={paginated['position']}  ✓"
            )
        else:
            print(
                f"    {video_id}: "
                f"direct={direct['position']} "
                f"pagination={paginated['position']}  ⚠"
            )


def retrieve_playlist(
    service,
    playlist_id: str,
    max_results: int,
    max_pages: int,
) -> list[dict]:
    """Retrieve bounded pages, stopping as soon as all expected videos are found."""
    items: list[dict] = []
    page_token = None
    seen_page_tokens: set[str] = set()
    found_expected: set[str] = set()

    for page_number in range(1, max_pages + 1):
        request_kwargs = {
            "part": "snippet,contentDetails,status",
            "playlistId": playlist_id,
            "maxResults": max_results,
        }
        if page_token is not None:
            if page_token in seen_page_tokens:
                raise RuntimeError(f"Repeated page token detected: {page_token!r}")
            seen_page_tokens.add(page_token)
            request_kwargs["pageToken"] = page_token

        response = service.playlistItems().list(**request_kwargs).execute()
        page_items = response.get("items", [])
        page_info = response.get("pageInfo", {})
        next_page_token = response.get("nextPageToken")

        for item in page_items:
            snippet = item["snippet"]
            video_id = snippet["resourceId"]["videoId"]
            item_data = {
                "position": snippet["position"],
                "video_id": video_id,
                "title": snippet["title"],
            }
            items.append(item_data)
            if video_id in EXPECTED_VIDEO_IDS:
                found_expected.add(video_id)

        print(
            f"    page={page_number:02d} "
            f"items={len(page_items):02d} "
            f"total={page_info.get('totalResults')} "
            f"per_page={page_info.get('resultsPerPage')} "
            f"expected_found={len(found_expected)}/{len(EXPECTED_VIDEO_IDS)}"
        )

        if found_expected == EXPECTED_VIDEO_IDS:
            print("    ✓ All expected videos found; pagination stopped.")
            break
        if next_page_token is None:
            print("    Reached end of playlist.")
            break
        page_token = next_page_token
    else:
        print(f"    Reached MAX_PAGES={max_pages}; pagination intentionally stopped.")

    return items


def analyze_result(items: list[dict]) -> None:
    returned_ids = {item["video_id"] for item in items}
    found_expected = EXPECTED_VIDEO_IDS & returned_ids
    missing_ids = EXPECTED_VIDEO_IDS - returned_ids

    print(f"    Expected videos found: {len(found_expected)}/{len(EXPECTED_VIDEO_IDS)}")
    if missing_ids:
        print("    Missing expected IDs:")
        for video_id in sorted(missing_ids):
            print(f"      - {video_id}")




def calculate_max_results_strategy(
    initial_max_results: int,
    passes: int,
) -> tuple[int, ...]:
    """Build the maxResults strategy using the two-thirds rule."""
    values = [initial_max_results]

    for _ in range(passes - 1):
        next_value = ceil(values[-1] * 2 / 3)
        if next_value >= values[-1]:
            raise RuntimeError("maxResults strategy did not decrease.")
        values.append(next_value)

    return tuple(values)


def main() -> None:
    client = YouTubeClient(
        client_secrets_path=CLIENT_SECRETS_PATH,
        token_path=TOKEN_PATH,
    )
    service = client.service
    uploads_playlist_id = get_uploads_playlist_id(service)

    print(f"Uploads playlist: {uploads_playlist_id}")
    print(f"Expected videos: {len(EXPECTED_VIDEO_IDS)}")

    direct_results = lookup_expected_videos(
        service=service,
        playlist_id=uploads_playlist_id,
    )

    if not direct_results:
        raise RuntimeError("No expected videos were found by direct videoId lookup.")

    max_results_values = calculate_max_results_strategy(
        initial_max_results=INITIAL_MAX_RESULTS,
        passes=PAGINATION_PASSES,
    )

    print()
    print("=" * 70)
    print("MAX RESULTS STRATEGY")
    print("=" * 70)
    print(
        "    "
        + " -> ".join(str(value) for value in max_results_values)
        + "  (two-thirds rule)"
    )
    found_video_ids: set[str] = set()

    for pass_number, max_results in enumerate(max_results_values, start=1):
        required_pages = ceil(len(EXPECTED_VIDEO_IDS) / max_results)
        max_pages = min(required_pages, MAX_PAGES)

        print()
        print("=" * 70)
        print(
            f"PASS {pass_number}/{len(max_results_values)} "
            f"| MAX RESULTS = {max_results} "
            f"| MAX PAGES = {max_pages}"
        )
        print("=" * 70)

        items = retrieve_playlist(
            service=service,
            playlist_id=uploads_playlist_id,
            max_results=max_results,
            max_pages=max_pages,
        )

        retrieved_ids = {
            item["video_id"]
            for item in items
            if item["video_id"] in EXPECTED_VIDEO_IDS
        }

        new_video_ids = retrieved_ids - found_video_ids
        found_video_ids.update(retrieved_ids)

        print(f"    New videos found: {len(new_video_ids)}")
        print(
            f"    Cumulative found: "
            f"{len(found_video_ids)}/{len(EXPECTED_VIDEO_IDS)}"
        )

        if new_video_ids:
            print("    Newly recovered IDs:")
            for video_id in sorted(new_video_ids):
                print(f"      - {video_id}")

        compare_pagination_with_direct_lookup(
            pagination_items=items,
            direct_results=direct_results,
        )

        if found_video_ids == EXPECTED_VIDEO_IDS:
            print("    ✓ All expected videos recovered.")
            break
    else:
        missing_ids = EXPECTED_VIDEO_IDS - found_video_ids

        print()
        print("=" * 70)
        print("DISCOVERY FAILED")
        print("=" * 70)
        print(
            f"    Found:   {len(found_video_ids)}/{len(EXPECTED_VIDEO_IDS)}"
        )
        print(f"    Missing: {len(missing_ids)}")

        for video_id in sorted(missing_ids):
            print(f"      - {video_id}")


if __name__ == "__main__":
    main()
