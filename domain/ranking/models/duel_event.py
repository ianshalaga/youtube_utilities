"""
Un duelo agrupa múltiples battles.
"""

from dataclasses import dataclass
from typing import List

from domain.ranking.models.battle_event import BattleEvent


@dataclass(frozen=True)
class DuelEvent:
    player_a: str
    player_b: str
    battles: List[BattleEvent]
