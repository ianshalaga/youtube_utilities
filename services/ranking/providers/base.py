from abc import ABC, abstractmethod
from typing import Iterable

from services.ranking.filters import RankingQuery


class DataProvider(ABC):
    """
    Contrato de acceso a datos competitivos.
    """

    @abstractmethod
    def iter_duels(self, query: RankingQuery) -> Iterable:
        """
        Devuelve duelos competitivos (para Player y Team ranking).
        """
        raise NotImplementedError

    @abstractmethod
    def iter_battles(self, query: RankingQuery) -> Iterable:
        """
        Devuelve battles competitivas (para Character y Player+Character ranking).
        """
        raise NotImplementedError
