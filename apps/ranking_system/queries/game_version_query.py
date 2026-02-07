# game_version_query.py

from services.ranking.filters import (
    RankingQuery,
    RankingScopeFilter,
)
from .base import RankingQueryPreset


class GameVersionRankingQuery(RankingQueryPreset):
    def __init__(self, *, game_id: int, game_version: str):
        self._game_id = game_id
        self._game_version = game_version

    def build(self) -> RankingQuery:
        return RankingQuery(
            scope=RankingScopeFilter(
                game_id=self._game_id,
                game_version=self._game_version,
            )
        )
