# event_type_query.py

from services.ranking.filters import (
    RankingQuery,
    RankingScopeFilter,
)
from .base import RankingQueryPreset


class EventTypeRankingQuery(RankingQueryPreset):
    def __init__(self, *, event_type_id: int):
        self._event_type_id = event_type_id

    def build(self) -> RankingQuery:
        return RankingQuery(
            scope=RankingScopeFilter(event_type_id=self._event_type_id)
        )
