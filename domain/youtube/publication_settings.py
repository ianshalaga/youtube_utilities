from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class PublicationSettings:
    def __init__(
        self,
        first_publish_at: datetime,
        timezone: str,
        interval_days: int,
    ) -> None:
        if not isinstance(first_publish_at, datetime):
            raise TypeError("first_publish_at must be a datetime.")

        if first_publish_at.tzinfo is not None:
            raise ValueError("first_publish_at must be a naive datetime.")

        if not isinstance(timezone, str):
            raise TypeError("timezone must be a string.")

        try:
            timezone_info = ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"Invalid timezone: {timezone!r}.") from exc

        if isinstance(interval_days, bool) or not isinstance(interval_days, int):
            raise TypeError("interval_days must be an integer.")

        if interval_days <= 0:
            raise ValueError("interval_days must be greater than zero.")

        self._first_publish_at = first_publish_at.replace(tzinfo=timezone_info)
        self._timezone = timezone_info
        self._interval_days = interval_days

    @property
    def first_publish_at(self) -> datetime:
        return self._first_publish_at

    @property
    def timezone(self) -> ZoneInfo:
        return self._timezone

    @property
    def interval_days(self) -> int:
        return self._interval_days

    def __repr__(self) -> str:
        return (
            "PublicationSettings("
            f"first_publish_at={self._first_publish_at!r}, "
            f"timezone={self._timezone.key!r}, "
            f"interval_days={self._interval_days!r}"
            ")"
        )
