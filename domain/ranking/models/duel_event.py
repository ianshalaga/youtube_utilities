from dataclasses import dataclass
from typing import Iterable

from domain.ranking.entities.ranking_entity import RankingEntity
from domain.ranking.models.battle_event import BattleEvent


@dataclass(frozen=True)
class DuelEvent:
    """
    Evento competitivo a nivel DUEL.

    - Tiene un ganador y uno o más perdedores
    - Los battles son input para score, no para wins/losses
    """
    duel_id: int
    competitive_level: RankingEntity
    participant_ids: tuple[int, ...]
    winner_id: int
    loser_ids: tuple[int, ...]
    battles: tuple[BattleEvent, ...]

    def __post_init__(self):
        if self.winner_id not in self.participant_ids:
            raise ValueError("winner_id no pertenece a participant_ids")

        for lid in self.loser_ids:
            if lid not in self.participant_ids:
                raise ValueError("loser_id no pertenece a participant_ids")

        if self.winner_id in self.loser_ids:
            raise ValueError("winner_id no puede estar en loser_ids")

        if len(self.participant_ids) < 2:
            raise ValueError("Un duelo debe tener al menos 2 participantes")

        if not self.battles:
            raise ValueError("Un duelo debe contener al menos una battle")

    @property
    def all_participants(self) -> Iterable[int]:
        return self.participant_ids
