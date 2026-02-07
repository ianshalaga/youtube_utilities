# apps/ranking_system/queries/base.py

from abc import ABC, abstractmethod
from services.ranking.filters import RankingQuery


class RankingQueryPreset(ABC):
    """
    Preset de aplicación para construir RankingQuery.
    """

    @abstractmethod
    def build(self) -> RankingQuery:
        """
        Construye y devuelve un RankingQuery.
        """
        raise NotImplementedError
