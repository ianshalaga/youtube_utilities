"""
Orquestador principal del ranking.
"""

from domain.ranking.engine.ranking_engine import RankingEngine
from domain.ranking.entities.score import Score


class RankingProcessor:
    def __init__(self, data_provider, engine: RankingEngine):
        self._provider = data_provider
        self._engine = engine

    def process(self):
        """
        Ejemplo mínimo: acumula score bruto.
        """
        score = 0.0

        for duel in self._provider.iter_duels():
            score += 1  # placeholder

        final_score = Score(score)
        return self._engine.score_to_rating(
            final_score,
            consistency_factor=1.0
        )
