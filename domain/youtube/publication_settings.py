from __future__ import annotations

from datetime import datetime


class PublicationSettings:
    def __init__(
        self,
        first_publish_at: datetime,
        interval_days: int,
    ) -> None:
        if not isinstance(first_publish_at, datetime):
            raise TypeError("first_publish_at must be a datetime.")

        if isinstance(interval_days, bool) or not isinstance(interval_days, int):
            raise TypeError("interval_days must be an integer.")

        if interval_days <= 0:
            raise ValueError("interval_days must be greater than zero.")

        self._first_publish_at = first_publish_at
        self._interval_days = interval_days

    @property
    def first_publish_at(self) -> datetime:
        return self._first_publish_at

    @property
    def interval_days(self) -> int:
        return self._interval_days

    def __repr__(self) -> str:
        return (
            "PublicationSettings("
            f"first_publish_at={self._first_publish_at!r}, "
            f"interval_days={self._interval_days!r}"
            ")"
        )