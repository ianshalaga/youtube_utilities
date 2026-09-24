from pathlib import Path
import sys

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


def main() -> None:
    client = YouTubeClient(
        client_secrets_path=CLIENT_SECRETS_PATH,
        token_path=TOKEN_PATH,
    )

    service = client.service

    uploads_playlist_id = get_uploads_playlist_id(service)

    print(f"Uploads playlist: {uploads_playlist_id}")

    page_token = None

    for page_number in range(10):
        print()
        print(f"===== PAGE {page_number + 1} =====")
        print(f"page_token = {page_token!r}")

        request_kwargs = {
            "part": "snippet,contentDetails,status",
            "playlistId": uploads_playlist_id,
            "maxResults": 1,
        }

        if page_token is not None:
            request_kwargs["pageToken"] = page_token

        request = service.playlistItems().list(**request_kwargs)

        response = request.execute()

        items = response.get("items", [])

        print(f"items = {len(items)}")
        print(f"next_page_token = {response.get('nextPageToken')!r}")

        for item in items:
            snippet = item["snippet"]
            resource_id = snippet["resourceId"]

            print(f"position = {snippet['position']}")
            print(f"video_id = {resource_id['videoId']}")
            print(f"title = {snippet['title']}")

        page_token = response.get("nextPageToken")

        if page_token is None:
            print("No more pages.")
            break


if __name__ == "__main__":
    main()