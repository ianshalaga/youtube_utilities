"""
Base de queries de ranking.
"""

from abc import ABC, abstractmethod


class RankingQuery(ABC):

    @abstractmethod
    def execute(self):
        pass
