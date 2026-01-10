"""
Motor central de ranking.
"""

from domain.ranking.entities.score import Score
from domain.ranking.entities.rating import Rating


class RankingEngine:
    """
    Convierte score acumulado en rating comparable.
    """

    def __init__(
        self,
        *,
        base_rating: float = 1500.0,
        k_rating: float = 0.02
    ):
        self._base_rating = base_rating
        self._k_rating = k_rating

    def score_to_rating(
        self,
        score: Score,
        consistency_factor: float
    ) -> Rating:
        """
        Rating = base_rating + score * consistency_factor * k_rating
        """
        rating_value = (
            self._base_rating +
            score.value * consistency_factor * self._k_rating
        )

        return Rating(rating_value)
