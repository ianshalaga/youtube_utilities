"""
Resultado final del ranking para una entidad.
"""

from dataclasses import dataclass
from domain.ranking.entities.rating import Rating
from domain.ranking.entities.score import Score


@dataclass(frozen=True)
class RankingResult:
    entity_id: str
    score: Score
    rating: Rating
