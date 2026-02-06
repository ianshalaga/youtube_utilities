from dataclasses import dataclass


@dataclass(frozen=True)
class BaseRankingStats:
    """
    Stats base compartidas por toda entidad competitiva.
    """

    events_played: int
    wins: int
    losses: int
    draws: int

    win_rate: float
    raw_score: float
    score: float
    rating: float
