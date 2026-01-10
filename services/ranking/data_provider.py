"""
Contrato para proveedores de datos de ranking.
"""

from abc import ABC, abstractmethod
from typing import Iterable

from domain.ranking.models.duel_event import DuelEvent


class RankingDataProvider(ABC):

    @abstractmethod
    def iter_duels(self) -> Iterable[DuelEvent]:
        pass
