# global_query.py

from services.ranking.filters import RankingQuery, RankingScopeFilter
from .base import RankingQueryPreset


class GlobalRankingQuery(RankingQueryPreset):
    def build(self) -> RankingQuery:
        return RankingQuery(
            scope=RankingScopeFilter()
        )
