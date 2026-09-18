from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from domain.youtube.publication_settings import PublicationSettings


def test_creates_settings_with_valid_values() -> None:
    settings = PublicationSettings(
        first_publish_at=datetime(2026, 11, 3, 9, 0),
        timezone="Europe/Paris",
        interval_days=1,
    )

    assert settings.first_publish_at == datetime(
        2026, 11, 3, 9, 0, tzinfo=ZoneInfo("Europe/Paris")
    )
    assert settings.timezone == ZoneInfo("Europe/Paris")
    assert settings.interval_days == 1


def test_rejects_non_datetime_first_publish_at() -> None:
    with pytest.raises(TypeError, match="first_publish_at must be a datetime"):
        PublicationSettings(
            first_publish_at="2026-11-03T09:00:00",  # type: ignore[arg-type]
            timezone="Europe/Paris",
            interval_days=1,
        )


def test_rejects_timezone_aware_first_publish_at() -> None:
    with pytest.raises(
        ValueError,
        match="first_publish_at must be a naive datetime",
    ):
        PublicationSettings(
            first_publish_at=datetime(
                2026, 11, 3, 9, 0, tzinfo=ZoneInfo("Europe/Paris")
            ),
            timezone="Europe/Paris",
            interval_days=1,
        )


def test_rejects_non_string_timezone() -> None:
    with pytest.raises(TypeError, match="timezone must be a string"):
        PublicationSettings(
            first_publish_at=datetime(2026, 11, 3, 9, 0),
            timezone=123,  # type: ignore[arg-type]
            interval_days=1,
        )


def test_rejects_invalid_timezone() -> None:
    with pytest.raises(ValueError, match="Invalid timezone"):
        PublicationSettings(
            first_publish_at=datetime(2026, 11, 3, 9, 0),
            timezone="Invalid/Timezone",
            interval_days=1,
        )


def test_rejects_non_integer_interval_days() -> None:
    with pytest.raises(TypeError, match="interval_days must be an integer"):
        PublicationSettings(
            first_publish_at=datetime(2026, 11, 3, 9, 0),
            timezone="Europe/Paris",
            interval_days=1.5,  # type: ignore[arg-type]
        )


def test_rejects_boolean_interval_days() -> None:
    with pytest.raises(TypeError, match="interval_days must be an integer"):
        PublicationSettings(
            first_publish_at=datetime(2026, 11, 3, 9, 0),
            timezone="Europe/Paris",
            interval_days=True,  # type: ignore[arg-type]
        )


def test_rejects_non_positive_interval_days() -> None:
    with pytest.raises(
        ValueError,
        match="interval_days must be greater than zero",
    ):
        PublicationSettings(
            first_publish_at=datetime(2026, 11, 3, 9, 0),
            timezone="Europe/Paris",
            interval_days=0,
        )


def test_repr_includes_configuration() -> None:
    settings = PublicationSettings(
        first_publish_at=datetime(2026, 11, 3, 9, 0),
        timezone="Europe/Paris",
        interval_days=1,
    )

    assert repr(settings) == (
        "PublicationSettings("
        "first_publish_at=datetime.datetime(2026, 11, 3, 9, 0, "
        "tzinfo=zoneinfo.ZoneInfo(key='Europe/Paris')), "
        "timezone='Europe/Paris', "
        "interval_days=1)"
    )
