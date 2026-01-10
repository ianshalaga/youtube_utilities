"""
Evento atómico de battle.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BattleEvent:
    winner_id: str
    loser_id: str
    winner_raw_points: float
    loser_raw_points: float
