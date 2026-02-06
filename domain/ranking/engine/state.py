from dataclasses import dataclass


@dataclass
class CompetitiveState:
    events_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0

    raw_score: float = 0.0
    rating: float = 1500.0
