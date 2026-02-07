# season_platform_query.py

from services.ranking.filters import (
    RankingQuery,
    RankingScopeFilter,
)
from .base import RankingQueryPreset


class SeasonPlatformRankingQuery(RankingQueryPreset):
    def __init__(self, *, season_id: int, platform_id: int):
        self._season_id = season_id
        self._platform_id = platform_id

    def build(self) -> RankingQuery:
        return RankingQuery(
            scope=RankingScopeFilter(
                season_id=self._season_id,
                platform_id=self._platform_id,
            )
        )
