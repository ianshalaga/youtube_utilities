# event_query.py

from services.ranking.filters import (
    RankingQuery,
    RankingScopeFilter,
)
from .base import RankingQueryPreset


class EventRankingQuery(RankingQueryPreset):
    def __init__(self, *, event_id: int):
        self._event_id = event_id

    def build(self) -> RankingQuery:
        return RankingQuery(
            scope=RankingScopeFilter(event_id=self._event_id)
        )
