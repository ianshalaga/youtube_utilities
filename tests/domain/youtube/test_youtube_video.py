import pytest

from domain.youtube.youtube_video import PrivacyStatus, YouTubeVideo


def test_youtube_video_creates_expected_values():
    video = YouTubeVideo(
        video_id="abc123",
        title="01 Opening Theme",
        description="Opening theme description.",
        privacy_status=PrivacyStatus.PRIVATE,
    )

    assert video.video_id == "abc123"
    assert video.title == "01 Opening Theme"
    assert video.description == "Opening theme description."
    assert video.privacy_status is PrivacyStatus.PRIVATE


def test_youtube_video_allows_null_description():
    video = YouTubeVideo(
        video_id="abc123",
        title="01 Opening Theme",
        description=None,
        privacy_status=PrivacyStatus.PRIVATE,
    )

    assert video.description is None


def test_privacy_status_has_expected_values():
    assert PrivacyStatus.PRIVATE.value == "private"
    assert PrivacyStatus.PUBLIC.value == "public"
    assert PrivacyStatus.UNLISTED.value == "unlisted"


@pytest.mark.parametrize("video_id", [None, "", "   "])
def test_youtube_video_rejects_invalid_video_id(video_id):
    with pytest.raises(ValueError, match="video_id must be a non-empty string"):
        YouTubeVideo(
            video_id=video_id,
            title="01 Opening Theme",
            description=None,
            privacy_status=PrivacyStatus.PRIVATE,
        )


@pytest.mark.parametrize("title", [None, "", "   "])
def test_youtube_video_rejects_invalid_title(title):
    with pytest.raises(ValueError, match="title must be a non-empty string"):
        YouTubeVideo(
            video_id="abc123",
            title=title,
            description=None,
            privacy_status=PrivacyStatus.PRIVATE,
        )


def test_youtube_video_is_immutable():
    video = YouTubeVideo(
        video_id="abc123",
        title="01 Opening Theme",
        description=None,
        privacy_status=PrivacyStatus.PRIVATE,
    )

    with pytest.raises(AttributeError):
        video.title = "Changed"